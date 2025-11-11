#!/usr/bin/env python3
# GPN Mouse Fine-tuning Script
# Purpose: Fine-tune human-pretrained GPN model on mouse genome data
# Usage: python mouse_train.py --human-model output/human_gpn_pretrained_real_gpn --data data/mouse_gpn_preprocessing_results.json

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

class GPNMouseTrainer:
    """GPN mouse fine-tuning pipeline (transfer learning from human model)"""
    
    def __init__(self, config: Dict):
        
        self.config = config
        self.output_dir = Path(config.get('output_dir', 'output/mouse_gpn_finetuned'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        logger.info(f"Device: {self.device}")
    
    def load_model_and_tokenizer(self):
        """Load human-pretrained GPN model and tokenizer (transfer learning)"""
        
        human_model_path = self.config.get('human_model_path', 'output/human_gpn_pretrained_real_gpn')
        cache_dir = self.config.get('cache_dir', 'cache')
        
        # Use absolute path for cache
        if not cache_dir.startswith('/'):
            cache_dir = str(Path(__file__).parent.parent / cache_dir)
        
        # Check if human model exists
        human_model_path = Path(human_model_path)
        if not human_model_path.exists():
            logger.error(f"Human model not found: {human_model_path}")
            logger.error("Please train human model first using pre_train.py")
            raise FileNotFoundError(f"Human model not found: {human_model_path}")
        
        logger.info(f"Loading human-pretrained model from: {human_model_path}")
        logger.info("This is TRANSFER LEARNING: using human model as starting point")
        
        # Load human-pretrained model
        self.model = AutoModelForMaskedLM.from_pretrained(
            str(human_model_path), 
            cache_dir=cache_dir, 
            trust_remote_code=True,
            local_files_only=True  # Force loading from local path
        ).to(self.device)
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(human_model_path), 
            cache_dir=cache_dir, 
            trust_remote_code=True,
            local_files_only=True
        )
        
        num_params = sum(p.numel() for p in self.model.parameters())
        logger.info(f"Loaded {self.model.__class__.__name__} ({num_params:,} params)")
        logger.info("? Transfer learning: Model initialized from human-pretrained weights")
        return True
    
    def load_training_data(self):
        """Load mouse training data from JSON and split into train/test (80/20)"""
        # FIXED: Split by window_id to prevent data leakage (same as human)
        data_path = Path(self.config.get('data_path', 'data/mouse_gpn_preprocessing_results.json'))
        test_size = self.config.get('test_size', 0.2)  # 80/20 split by default
        random_state = self.config.get('random_state', 42)
        
        if not data_path.exists():
            logger.error(f"Mouse data not found: {data_path}")
            logger.error("Please run mouse preprocessing first: python data/mouse_preprocess.py full 111")
            return None, None
        
        logger.info(f"Loading mouse data: {data_path}")
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
        
        logger.info(f"Loaded {len(all_data)} mouse examples")
        
        # Group sequences by window_id to prevent data leakage
        # Each window has 2 sequences: original + reverse_complement
        window_groups = {}
        for item in all_data:
            window_id = item.get('window_id', '')
            if window_id not in window_groups:
                window_groups[window_id] = []
            window_groups[window_id].append(item)
        
        logger.info(f"Found {len(window_groups)} unique mouse windows")
        
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
        
        logger.info(f"Mouse data split (80/20) by window:")
        logger.info(f"  Training windows: {len(train_window_ids)} ({len(train_window_ids)/len(window_ids)*100:.1f}%)")
        logger.info(f"  Test windows: {len(test_window_ids)} ({len(test_window_ids)/len(window_ids)*100:.1f}%)")
        logger.info(f"  Training sequences: {len(train_data)} ({len(train_data)/len(all_data)*100:.1f}%)")
        logger.info(f"  Test sequences: {len(test_data)} ({len(test_data)/len(all_data)*100:.1f}%)")
        logger.info(f"  ? No data leakage: train and test have completely different windows")
        
        # Save test set for later evaluation
        test_data_path = self.output_dir / 'test_data.json'
        with open(test_data_path, 'w') as f:
            json.dump(test_data, f, indent=2)
        logger.info(f"Mouse test set saved to: {test_data_path}")
        
        # Extract only sequences for training
        training_data = [
            {'sequence': item['sequence'], 'original': item.get('original', '')}
            for item in train_data if item.get('sequence')
        ]
        
        return training_data, test_data
 
    def create_dataset(self, training_data: List[Dict]):
        """Create PyTorch dataset with MLM masking (identical to human training)"""
  
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
        
        logger.info(f"Mouse dataset: {len(dataset)} examples, batch size: {batch_size}")
        return data_loader
    
    def setup_training(self, data_loader):
        """Setup optimizer and scheduler (identical to human training)"""
        
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
        
        logger.info("Training setup complete")
        return True
    
    def train(self):
        """Run training loop (identical to human training)"""
        self.model.train()
        start_time = time.time()
        
        num_epochs = self.config.get('num_epochs', 3)
        log_steps = self.config.get('logging_steps', 100)
        warmup_steps = self.config.get('warmup_steps', 500)
        
        total_loss, total_batches = 0, 0
        
        logger.info(f"Starting mouse fine-tuning: {num_epochs} epochs")
        logger.info("Transfer learning: Fine-tuning human model on mouse data")
        
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
        
        # Save training info
        training_info = {
            'loss': avg_loss,
            'time': train_time,
            'batches': total_batches,
            'epochs': num_epochs,
            'species': 'mouse',
            'transfer_learning': True,
            'source_model': str(self.config.get('human_model_path', '')),
            'data_path': str(self.config.get('data_path', ''))
        }
        
        with open(self.output_dir / 'metrics.json', 'w') as f:
            json.dump(training_info, f, indent=2)
        
        logger.info(f"Mouse fine-tuning done! Time: {train_time:.1f}s, Loss: {avg_loss:.4f}")
        logger.info(f"Model saved: {self.output_dir}")
        return True
    
    def run_mouse_training(self):
        """Complete mouse fine-tuning pipeline"""
        logger.info("="*60)
        logger.info("GPN MOUSE FINE-TUNING (Transfer Learning from Human)")
        logger.info("="*60)
        
        self.load_model_and_tokenizer()
        training_data, test_data = self.load_training_data()
        if training_data is None:
            return False
        
        data_loader = self.create_dataset(training_data)
        self.setup_training(data_loader)
        self.train()
        
        logger.info("="*60)
        logger.info("MOUSE FINE-TUNING COMPLETE!")
        logger.info(f"Test set saved: {self.output_dir / 'test_data.json'}")
        logger.info("="*60)
        return True


def create_config(human_model_path, data_path, output_dir, epochs, batch_size, lr):
    """Create mouse training configuration"""
    return {
        "human_model_path": human_model_path,  # Key difference: load from human model
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
    
    parser = argparse.ArgumentParser(description="GPN Mouse Fine-tuning (Transfer Learning)")
    parser.add_argument("--human-model", default="output/human_gpn_pretrained_real_gpn", 
                       help="Path to human-pretrained GPN model")
    parser.add_argument("--data", default="data/mouse_gpn_preprocessing_results.json", 
                       help="Mouse training data")
    parser.add_argument("--output", default="output/mouse_gpn_finetuned", 
                       help="Output directory")
    parser.add_argument("--epochs", type=int, default=2, help="Epochs")
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
            args.human_model, args.data, args.output,
            args.epochs, args.batch_size, args.lr
        )
    
    # Log config
    logger.info("Mouse Fine-tuning Config:")
    for k, v in config.items():
        logger.info(f"  {k}: {v}")
    
    # Train
    try:
        trainer = GPNMouseTrainer(config)
        trainer.run_mouse_training()
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

