#!/usr/bin/env python3
# GPN Model Pre-training Script
# Usage: python pre_train.py --data data.json --output output/ --epochs 3

import torch
from torch.utils.data import Dataset, DataLoader
import gpn.model
from transformers import AutoModelForMaskedLM, AutoTokenizer
import torch.optim as optim
from torch.optim.lr_scheduler import LinearLR
from sklearn.model_selection import train_test_split
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GPNPreTrainer:
    # GPN pre-training pipeline
    
    def __init__(self, config: Dict):
        
        
        self.config = config
        self.output_dir = Path(config.get('output_dir', 'output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        logger.info(f"Device: {self.device}")
    
    def load_model_and_tokenizer(self):
        # Load GPN model and tokenizer
        
        
        model_name = self.config.get('model_name', 'songlab/gpn-brassicales')
        cache_dir = self.config.get('cache_dir', 'cache')
        
        # Use absolute path for cache
        if not cache_dir.startswith('/'):
            cache_dir = str(Path(__file__).parent.parent / cache_dir)
        
        logger.info(f"Loading model: {model_name}")
        logger.info(f"Cache directory: {cache_dir}")
        
        self.model = AutoModelForMaskedLM.from_pretrained(
            model_name, cache_dir=cache_dir, trust_remote_code=True
        ).to(self.device)
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, cache_dir=cache_dir, trust_remote_code=True
        )
        
        num_params = sum(p.numel() for p in self.model.parameters())
        logger.info(f"Loaded {self.model.__class__.__name__} ({num_params:,} params)")
        return True
    
    def load_training_data(self):
        # Load training data from JSON and split into train/test (80/20)
        # FIXED: Split by window_id to prevent data leakage
        data_path = Path(self.config.get('data_path', 'data/human_gpn_preprocessing_results.json'))
        test_size = self.config.get('test_size', 0.2)  # 80/20 split by default
        random_state = self.config.get('random_state', 42)
        
        if not data_path.exists():
            logger.error(f"Data not found: {data_path}")
            return None, None
        
        logger.info(f"Loading: {data_path}")
        with open(data_path) as f:
            data = json.load(f)
        
        # Extract sequences with full metadata
        all_data = [
            {
                'sequence': item['masked_sequence'], 
                'original': item.get('original_sequence', ''),
                **{k: v for k, v in item.items() if k not in ['masked_sequence', 'original_sequence']}
            }
            for item in data if item.get('masked_sequence')
        ]
        
        logger.info(f"Loaded {len(all_data)} examples")
        
        # Group sequences by window_id to prevent data leakage
        # Each window has 2 sequences: original + reverse_complement
        window_groups = {}
        for item in all_data:
            window_id = item.get('window_id', '')
            if window_id not in window_groups:
                window_groups[window_id] = []
            window_groups[window_id].append(item)
        
        logger.info(f"Found {len(window_groups)} unique windows")
        
        # Split windows (not sequences) into train/test
        window_ids = list(window_groups.keys())
        train_window_ids, test_window_ids = train_test_split(
            window_ids,
            test_size=test_size,
            random_state=random_state,
            shuffle=True
        )
        
        # Collect all sequences for each window split
        train_data = []
        for wid in train_window_ids:
            train_data.extend(window_groups[wid])
        
        test_data = []
        for wid in test_window_ids:
            test_data.extend(window_groups[wid])
        
        logger.info(f"Data split (80/20) by window:")
        logger.info(f"  Training windows: {len(train_window_ids)} ({len(train_window_ids)/len(window_ids)*100:.1f}%)")
        logger.info(f"  Test windows: {len(test_window_ids)} ({len(test_window_ids)/len(window_ids)*100:.1f}%)")
        logger.info(f"  Training sequences: {len(train_data)} ({len(train_data)/len(all_data)*100:.1f}%)")
        logger.info(f"  Test sequences: {len(test_data)} ({len(test_data)/len(all_data)*100:.1f}%)")
        logger.info(f"  ? No data leakage: train and test have completely different windows")
        
        # Save test set for later evaluation
        test_data_path = self.output_dir / 'test_data.json'
        with open(test_data_path, 'w') as f:
            json.dump(test_data, f, indent=2)
        logger.info(f"Test set saved to: {test_data_path}")
        
        # Extract only sequences for training
        # Note: train_data items already have 'sequence' key (from masked_sequence)
        training_data = [
            {'sequence': item['sequence'], 'original': item.get('original', '')}
            for item in train_data if item.get('sequence')
        ]
        
        return training_data, test_data
 
    def create_dataset(self, training_data: List[Dict]):
        # Create PyTorch dataset with MLM masking
  
        class GPNDataset(Dataset):
            def __init__(self, data, tokenizer, max_length, mask_prob=0.15):
                self.data = data
                self.tokenizer = tokenizer
                self.max_length = max_length
                self.mask_prob = mask_prob
                
                # Get special token IDs that should not be masked
                self.special_tokens = set()
                if hasattr(tokenizer, 'pad_token_id') and tokenizer.pad_token_id is not None:
                    self.special_tokens.add(tokenizer.pad_token_id)
                if hasattr(tokenizer, 'cls_token_id') and tokenizer.cls_token_id is not None:
                    self.special_tokens.add(tokenizer.cls_token_id)
                if hasattr(tokenizer, 'sep_token_id') and tokenizer.sep_token_id is not None:
                    self.special_tokens.add(tokenizer.sep_token_id)
                if hasattr(tokenizer, 'mask_token_id') and tokenizer.mask_token_id is not None:
                    self.mask_token_id = tokenizer.mask_token_id
                else:
                    # If no mask token, use a placeholder (shouldn't happen with MLM models)
                    self.mask_token_id = tokenizer.unk_token_id if hasattr(tokenizer, 'unk_token_id') else 0

            def __len__(self):
                return len(self.data)
            
            def __getitem__(self, idx):
                tokens = self.tokenizer(
                    self.data[idx]['sequence'],
                    max_length=self.max_length,
                    padding='max_length',
                    truncation=True,
                    return_tensors='pt'
                )
                
                input_ids = tokens['input_ids'].clone().squeeze()
                labels = input_ids.clone()
                
                # Create mask for MLM: randomly mask mask_prob% of tokens
                # Don't mask special tokens (pad, cls, sep, etc.)
                probability_matrix = torch.full(labels.shape, self.mask_prob)
                
                # Don't mask special tokens
                for special_token_id in self.special_tokens:
                    special_token_mask = (input_ids == special_token_id)
                    probability_matrix[special_token_mask] = 0.0
                
                # Create masked indices
                masked_indices = torch.bernoulli(probability_matrix).bool()
                
                # Set labels to -100 for non-masked positions (so loss ignores them)
                labels[~masked_indices] = -100
                
                # Replace masked input tokens with [MASK] token
                input_ids[masked_indices] = self.mask_token_id
                
                return {
                    'input_ids': input_ids,
                    'attention_mask': tokens['attention_mask'].squeeze(),
                    'labels': labels
                }
        
        dataset = GPNDataset(training_data, self.tokenizer, self.config.get('max_length', 512))
        batch_size = self.config.get('batch_size', 8)
        
        data_loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)
        
        logger.info(f"Dataset: {len(dataset)} examples, batch size: {batch_size}")
        return data_loader
    
    def setup_training(self, data_loader):
        # Setup optimizer and scheduler
        
        self.data_loader = data_loader
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=self.config.get('learning_rate', 5e-5),
            weight_decay=self.config.get('weight_decay', 0.01)
        )
        self.scheduler = LinearLR(
            self.optimizer,
            start_factor=0.1,
            total_iters=self.config.get('warmup_steps', 500)
        )
        
        logger.info("Setup complete")
        return True
    
    def train(self):
        # Run training loop
        self.model.train()
        start_time = time.time()
        
        num_epochs = self.config.get('num_epochs', 3)
        log_steps = self.config.get('logging_steps', 100)
        warmup_steps = self.config.get('warmup_steps', 500)
        
        total_loss, total_batches = 0, 0
        
        logger.info(f"Starting training: {num_epochs} epochs")
        
        for epoch in range(num_epochs):
            epoch_loss, epoch_batches = 0, 0
            
            for batch_idx, batch in enumerate(self.data_loader):
                # Move to device
                batch = {k: v.to(self.device) for k, v in batch.items()}
                
                # Forward + backward
                self.optimizer.zero_grad()
                outputs = self.model(**batch)
                outputs.loss.backward()
                self.optimizer.step()
                
                # Update scheduler during warmup
                if total_batches < warmup_steps:
                    self.scheduler.step()
                
                # Track loss
                loss_val = outputs.loss.item()
                total_loss += loss_val
                epoch_loss += loss_val
                total_batches += 1
                epoch_batches += 1
                
                # Log progress
                if (batch_idx + 1) % log_steps == 0:
                    logger.info(f"Epoch {epoch+1}/{num_epochs}, Batch {batch_idx+1}, Loss: {epoch_loss/epoch_batches:.4f}")
            
            logger.info(f"Epoch {epoch+1} done. Avg loss: {epoch_loss/epoch_batches:.4f}")
        
        # Save model and metrics
        train_time = time.time() - start_time
        avg_loss = total_loss / total_batches
        
        self.model.save_pretrained(self.output_dir)
        self.tokenizer.save_pretrained(self.output_dir)
        
        with open(self.output_dir / 'metrics.json', 'w') as f:
            json.dump({
                'loss': avg_loss,
                'time': train_time,
                'batches': total_batches,
                'epochs': num_epochs
            }, f, indent=2)
        
        logger.info(f"Training done! Time: {train_time:.1f}s, Loss: {avg_loss:.4f}")
        logger.info(f"Model saved: {self.output_dir}")
        return True
    
    def run_pre_training(self):
        # Complete pipeline
        logger.info("="*50)
        logger.info("GPN PRE-TRAINING")
        logger.info("="*50)
        
        self.load_model_and_tokenizer()
        training_data, test_data = self.load_training_data()
        if training_data is None:
            return False
        
        data_loader = self.create_dataset(training_data)
        self.setup_training(data_loader)
        self.train()
        
        logger.info("="*50)
        logger.info("TRAINING COMPLETE!")
        logger.info(f"Test set saved for evaluation: {self.output_dir / 'test_data.json'}")
        logger.info("="*50)
        return True


def create_config(data_path, output_dir, model_name, epochs, batch_size, lr):
    # Create training configuration
    return {
        "model_name": model_name,
        "data_path": data_path,
        "output_dir": output_dir,
        "cache_dir": "cache",
        "max_length": 512,
        "batch_size": batch_size,
        "num_epochs": epochs,
        "learning_rate": lr,
        "warmup_steps": 500,
        "weight_decay": 0.01,
        "logging_steps": 100,
        "test_size": 0.2,  # 80/20 split (train/test)
        "random_state": 42  # For reproducible split
    }


def main():
    
    parser = argparse.ArgumentParser(description="GPN Pre-training")
    parser.add_argument("--data", default="../data/gpn_preprocessing_results.json", help="Training data")
    parser.add_argument("--output", default="../output/gpn_pretrained", help="Output directory")
    parser.add_argument("--model", default="songlab/gpn-brassicales", help="Model name")
    parser.add_argument("--epochs", type=int, default=3, help="Epochs")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size")
    parser.add_argument("--lr", type=float, default=5e-5, help="Learning rate")
    parser.add_argument("--config", help="Config JSON (overrides other args)")
    
    args = parser.parse_args()
    
    # Load or create config
    if args.config and Path(args.config).exists():
        with open(args.config) as f:
            config = json.load(f)
    else:
        config = create_config(
            args.data, args.output, args.model,
            args.epochs, args.batch_size, args.lr
        )
    
    # Log config
    logger.info("Config:")
    for k, v in config.items():
        logger.info(f"  {k}: {v}")
    
    # Train
    try:
        trainer = GPNPreTrainer(config)
        trainer.run_pre_training()
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
