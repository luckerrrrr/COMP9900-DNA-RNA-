#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPN Supervised Fine-tuning using Hugging Face Transformers

Using AutoModelForSequenceClassification for lncRNA conservation prediction
"""

import torch
import torch.nn as nn
from torch.utils.data import Dataset
from transformers import (
    PretrainedConfig,
    PreTrainedModel
)
from transformers.modeling_outputs import SequenceClassifierOutput
import torch.optim as optim
from torch.utils.data import DataLoader
import numpy as np
import json
import argparse
from pathlib import Path
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)
import sys
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from gpn.model import ConvNetForMaskedLM
from gpn.data import Tokenizer


# ============================================================================
# 1. GPNConfig - Hugging Face compatible configuration class
# ============================================================================

class GPNConfig(PretrainedConfig):
    """
    Configuration class for GPN model
    Inherits from PretrainedConfig to make GPN compatible with HF ecosystem
    """
    model_type = "gpn"
    
    def __init__(
        self,
        pretrained_model_path=None,
        num_labels=2,
        hidden_size=768,
        classifier_dropout=0.1,
        freeze_backbone=False,
        **kwargs
    ):
        """
        Args:
            pretrained_model_path: Path to pretrained GPN model
            num_labels: Number of labels (2 for binary classification)
            hidden_size: GPN hidden size (default: 768)
            classifier_dropout: Dropout rate for classifier head
            freeze_backbone: Whether to freeze GPN backbone
        """
        super().__init__(num_labels=num_labels, **kwargs)
        self.pretrained_model_path = pretrained_model_path
        self.hidden_size = hidden_size
        self.classifier_dropout = classifier_dropout
        self.freeze_backbone = freeze_backbone


# ============================================================================
# 2. GPNForSequenceClassification - HF compatible classification model
# ============================================================================

class GPNForSequenceClassification(PreTrainedModel):
    """
    GPN sequence classification model
    Inherits from PreTrainedModel to be compatible with HF Trainer API
    """
    config_class = GPNConfig
    
    def __init__(self, config):
        super().__init__(config)
        self.num_labels = config.num_labels
        self.config = config
        
        # 1. Load pretrained GPN backbone
        print(f"Loading GPN model from: {config.pretrained_model_path}")
        self.gpn = ConvNetForMaskedLM.from_pretrained(
            config.pretrained_model_path
        )
        
        # Get hidden size
        self.hidden_size = self.gpn.model.config.hidden_size
        
        # 2. Freeze backbone if specified
        if config.freeze_backbone:
            print("Freezing GPN backbone (training classifier head only)")
            for param in self.gpn.parameters():
                param.requires_grad = False
        else:
            print("Full fine-tuning (training entire model)")
        
        # 3. Define classification head
        # Structure: hidden_size -> hidden_size//2 -> num_labels
        self.classifier = nn.Sequential(
            nn.Dropout(config.classifier_dropout),
            nn.Linear(self.hidden_size, self.hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(config.classifier_dropout),
            nn.Linear(self.hidden_size // 2, config.num_labels)
        )
        
        # 4. HF required initialization
        self.post_init()
        
        # Count parameters
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in self.parameters())
        print(f"Trainable parameters: {trainable_params:,} / {total_params:,} "
              f"({100 * trainable_params / total_params:.2f}%)")
    
    def forward(
        self,
        input_ids=None,
        attention_mask=None,
        labels=None,
        return_dict=True,
        **kwargs
    ):
        """
        Forward pass
        
        Args:
            input_ids: [batch_size, seq_length] Token IDs
            attention_mask: [batch_size, seq_length] Attention mask
            labels: [batch_size] Labels for classification
            return_dict: Whether to return SequenceClassifierOutput
        
        Returns:
            SequenceClassifierOutput with loss and logits
        """
        
        # 1. Get GPN embeddings
        outputs = self.gpn.model(
            input_ids,
            attention_mask=attention_mask
        )
        hidden_states = outputs.last_hidden_state  # [batch, seq_len, hidden_size]
        
        # 2. Mean Pooling
        # Average all token embeddings (considering attention_mask)
        mask_expanded = attention_mask.unsqueeze(-1).expand(hidden_states.size()).float()
        sum_embeddings = torch.sum(hidden_states * mask_expanded, dim=1)
        sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
        pooled_output = sum_embeddings / sum_mask  # [batch, hidden_size]
        
        # 3. Classification
        logits = self.classifier(pooled_output)  # [batch, num_labels]
        
        # 4. Calculate loss
        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(
                logits.view(-1, self.num_labels),
                labels.view(-1)
            )
        
        # 5. Return HF standard output
        if not return_dict:
            output = (logits,) + outputs[1:]
            return ((loss,) + output) if loss is not None else output
        
        return SequenceClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=None,
            attentions=None
        )


# ============================================================================
# 3. Dataset - Data loading class
# ============================================================================

class FineTuningDataset(Dataset):
    """
    Fine-tuning dataset
    Loads preprocessed data from JSON file
    """
    
    def __init__(self, data_file, tokenizer, max_length=512):
        """
        Args:
            data_file: Path to JSON data file
            tokenizer: GPN tokenizer
            max_length: Maximum sequence length
        """
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        # Load data
        print(f"Loading data from: {data_file}")
        with open(data_file, 'r') as f:
            self.data = json.load(f)
        
        print(f"Loaded {len(self.data)} samples")
        
        # Print label distribution
        self._print_label_distribution()
    
    def _print_label_distribution(self):
        """Print label distribution"""
        labels = [item['label'] for item in self.data]
        unique, counts = np.unique(labels, return_counts=True)
        
        print("Label distribution:")
        for label, count in zip(unique, counts):
            label_name = "conserved" if label == 1 else "non-conserved"
            print(f"  Label {label} ({label_name}): {count} ({100 * count / len(labels):.2f}%)")
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        """
        Get one sample
        
        Returns:
            dict with keys: input_ids, attention_mask, labels
        """
        item = self.data[idx]
        
        # Get sequence and label
        sequence = item['sequence']
        label = item['label']
        
        # Tokenize sequence
        seq_array = np.array(list(sequence))
        tokens = self.tokenizer(seq_array)
        
        if isinstance(tokens, np.ndarray):
            tokens = tokens.tolist()
        
        # Truncate or pad
        if len(tokens) > self.max_length:
            tokens = tokens[:self.max_length]
        
        # Create attention mask
        attention_mask = [1] * len(tokens)
        
        # Padding
        pad_length = self.max_length - len(tokens)
        if pad_length > 0:
            tokens = tokens + [0] * pad_length  # 0 is pad token
            attention_mask = attention_mask + [0] * pad_length
        
        return {
            'input_ids': torch.tensor(tokens, dtype=torch.long),
            'attention_mask': torch.tensor(attention_mask, dtype=torch.long),
            'labels': torch.tensor(label, dtype=torch.long)
        }


# ============================================================================
# 4. Metrics computation function
# ============================================================================

def compute_metrics(eval_pred):
    """
    Compute evaluation metrics
    Trainer will automatically call this function
    
    Args:
        eval_pred: EvalPrediction with predictions and label_ids
    
    Returns:
        dict with metrics
    """
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    
    # Calculate various metrics
    accuracy = accuracy_score(labels, predictions)
    f1 = f1_score(labels, predictions, average='weighted')
    precision = precision_score(labels, predictions, average='weighted', zero_division=0)
    recall = recall_score(labels, predictions, average='weighted', zero_division=0)
    
    # Try to calculate AUC (requires probability values)
    try:
        # Calculate AUC using predicted probabilities
        probs = np.exp(eval_pred.predictions) / np.exp(eval_pred.predictions).sum(axis=1, keepdims=True)
        auc = roc_auc_score(labels, probs[:, 1])
    except:
        auc = 0.0
    
    return {
        'accuracy': accuracy,
        'f1': f1,
        'precision': precision,
        'recall': recall,
        'auc': auc
    }


# ============================================================================
# 5. Main training function
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="GPN Supervised Fine-tuning with Hugging Face Transformers"
    )
    
    # Data parameters
    parser.add_argument('--data', required=True, help="Path to processed JSON data file")
    parser.add_argument('--pretrained-model', required=True, help="Path to pretrained GPN model")
    parser.add_argument('--output', default='output/gpn_supervised', help="Output directory")
    
    # Model parameters
    parser.add_argument('--num-labels', type=int, default=2, help="Number of classes")
    parser.add_argument('--max-length', type=int, default=512, help="Max sequence length")
    parser.add_argument('--freeze-backbone', action='store_true', help="Freeze GPN backbone")
    parser.add_argument('--classifier-dropout', type=float, default=0.1, help="Classifier dropout")
    
    # 训练参数
    parser.add_argument('--epochs', type=int, default=20, help="Number of epochs")
    parser.add_argument('--batch-size', type=int, default=16, help="Batch size")
    parser.add_argument('--eval-batch-size', type=int, default=32, help="Evaluation batch size")
    parser.add_argument('--lr', type=float, default=2e-5, help="Learning rate")
    parser.add_argument('--weight-decay', type=float, default=0.01, help="Weight decay")
    parser.add_argument('--warmup-ratio', type=float, default=0.1, help="Warmup ratio")
    
    # 评估和保存
    parser.add_argument('--eval-steps', type=int, default=100, help="Evaluation steps")
    parser.add_argument('--save-steps', type=int, default=100, help="Save checkpoint steps")
    parser.add_argument('--save-total-limit', type=int, default=3, help="Max checkpoints to keep")
    parser.add_argument('--early-stopping-patience', type=int, default=3, help="Early stopping patience")
    
    # 高级特性
    parser.add_argument('--fp16', action='store_true', help="Enable mixed precision training")
    parser.add_argument('--gradient-accumulation-steps', type=int, default=1, help="Gradient accumulation")
    
    # 其他
    parser.add_argument('--seed', type=int, default=42, help="Random seed")
    parser.add_argument('--test-size', type=float, default=0.15, help="Test set size")
    parser.add_argument('--val-size', type=float, default=0.15, help="Validation set size")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("GPN Supervised Fine-tuning with Hugging Face Transformers")
    print("=" * 80)
    print("\nConfiguration:")
    for arg, value in vars(args).items():
        print(f"  {arg}: {value}")
    print()
    
    # 1. Create model configuration
    config = GPNConfig(
        pretrained_model_path=args.pretrained_model,
        num_labels=args.num_labels,
        hidden_size=768,  # GPN default
        classifier_dropout=args.classifier_dropout,
        freeze_backbone=args.freeze_backbone
    )
    
    # 2. Create model
    print("\n" + "=" * 80)
    print("Creating Model")
    print("=" * 80 + "\n")
    model = GPNForSequenceClassification(config)
    
    # 3. Prepare data
    print("\n" + "=" * 80)
    print("Loading Data")
    print("=" * 80 + "\n")
    
    tokenizer = Tokenizer()
    
    # Load full dataset
    full_dataset = FineTuningDataset(
        data_file=args.data,
        tokenizer=tokenizer,
        max_length=args.max_length
    )
    
    # Split dataset: train/val/test
    total_size = len(full_dataset)
    test_size = int(total_size * args.test_size)
    val_size = int(total_size * args.val_size)
    train_size = total_size - test_size - val_size
    
    print(f"\nDataset split:")
    print(f"  Train: {train_size} ({100 * train_size / total_size:.1f}%)")
    print(f"  Validation: {val_size} ({100 * val_size / total_size:.1f}%)")
    print(f"  Test: {test_size} ({100 * test_size / total_size:.1f}%)")
    
    train_dataset, val_dataset, test_dataset = torch.utils.data.random_split(
        full_dataset,
        [train_size, val_size, test_size],
        generator=torch.Generator().manual_seed(args.seed)
    )
    
    # 4. Create data loaders  
    print("\n" + "=" * 80)
    print("Creating Data Loaders")
    print("=" * 80 + "\n")
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=args.eval_batch_size, shuffle=False, num_workers=2)
    test_loader = DataLoader(test_dataset, batch_size=args.eval_batch_size, shuffle=False, num_workers=2)
    
    print(f"Train batches: {len(train_loader)}")
    print(f"Val batches: {len(val_loader)}")
    print(f"Test batches: {len(test_loader)}")
    
    # 5. Setup training
    print("\n" + "=" * 80)
    print("Training Setup")
    print("=" * 80 + "\n")
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    model = model.to(device)
    
    # Optimizer
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    
    # Learning rate scheduler
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=2, verbose=True)
    
    # Output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 6. Training loop
    print("\n" + "=" * 80)
    print("Starting Training")
    print("=" * 80 + "\n")
    
    best_val_f1 = 0.0
    patience_counter = 0
    history = {'train_loss': [], 'val_loss': [], 'val_f1': [], 'val_acc': []}
    
    for epoch in range(args.epochs):
        print(f"\nEpoch {epoch + 1}/{args.epochs}")
        print("-" * 80)
        
        # Train
        model.train()
        train_loss = 0.0
        for batch_idx, batch in enumerate(train_loader):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            optimizer.zero_grad()
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            
            if (batch_idx + 1) % 50 == 0:
                print(f"  Step {batch_idx + 1}/{len(train_loader)}: loss={loss.item():.4f}")
        
        avg_train_loss = train_loss / len(train_loader)
        history['train_loss'].append(avg_train_loss)
        
        # Validate
        model.eval()
        val_loss = 0.0
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device)
                
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                val_loss += outputs.loss.item()
                preds = torch.argmax(outputs.logits, dim=1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        avg_val_loss = val_loss / len(val_loader)
        val_acc = accuracy_score(all_labels, all_preds)
        val_f1 = f1_score(all_labels, all_preds, average='weighted')
        
        history['val_loss'].append(avg_val_loss)
        history['val_f1'].append(val_f1)
        history['val_acc'].append(val_acc)
        
        print(f"\nTrain Loss: {avg_train_loss:.4f}")
        print(f"Val Loss: {avg_val_loss:.4f}, Val Acc: {val_acc:.4f}, Val F1: {val_f1:.4f}")
        
        scheduler.step(val_f1)
        
        # Save best model
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            torch.save({'model_state_dict': model.state_dict(), 'epoch': epoch, 'val_f1': val_f1}, output_dir / 'best_model.pt')
            print(f"? Best model saved (F1: {best_val_f1:.4f})")
            patience_counter = 0
        else:
            patience_counter += 1
            print(f"No improvement. Patience: {patience_counter}/{args.early_stopping_patience}")
            if patience_counter >= args.early_stopping_patience:
                print(f"\nEarly stopping at epoch {epoch + 1}")
                break
    
    # Save history
    with open(output_dir / 'training_history.json', 'w') as f:
        json.dump(history, f, indent=2)
    
    # 7. Test evaluation
    print("\n" + "=" * 80)
    print("Evaluating on Test Set")
    print("=" * 80 + "\n")
    
    # Load best model
    checkpoint = torch.load(output_dir / 'best_model.pt')
    model.load_state_dict(checkpoint['model_state_dict'])
    print(f"Loaded best model from epoch {checkpoint['epoch'] + 1}")
    
    # Evaluate
    model.eval()
    all_preds = []
    all_labels = []
    all_probs = []
    
    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=1)
            preds = torch.argmax(logits, dim=1)
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
    
    test_acc = accuracy_score(all_labels, all_preds)
    test_f1 = f1_score(all_labels, all_preds, average='weighted')
    test_precision = precision_score(all_labels, all_preds, average='weighted')
    test_recall = recall_score(all_labels, all_preds, average='weighted')
    
    try:
        all_probs = np.array(all_probs)
        test_auc = roc_auc_score(all_labels, all_probs[:, 1])
    except:
        test_auc = 0.0
    
    print("\nTest Results:")
    print(f"  Accuracy: {test_acc:.4f}")
    print(f"  F1 Score: {test_f1:.4f}")
    print(f"  Precision: {test_precision:.4f}")
    print(f"  Recall: {test_recall:.4f}")
    print(f"  AUC: {test_auc:.4f}")
    
    test_results = {'test_accuracy': float(test_acc), 'test_f1': float(test_f1), 'test_precision': float(test_precision), 'test_recall': float(test_recall), 'test_auc': float(test_auc)}
    with open(output_dir / 'test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"\nTest results saved to: {output_dir / 'test_results.json'}")
    
    # 8. Classification report
    print("\n" + "=" * 80)
    print("Generating Classification Report")
    print("=" * 80 + "\n")
    
    report = classification_report(all_labels, all_preds, target_names=['non-conserved', 'conserved'], digits=4)
    print(report)
    
    cm = confusion_matrix(all_labels, all_preds)
    print("\nConfusion Matrix:")
    print(cm)
    
    with open(output_dir / 'classification_report.txt', 'w') as f:
        f.write("Classification Report\n" + "=" * 80 + "\n\n" + report + "\n\nConfusion Matrix:\n" + str(cm))
    print(f"\nReport saved to: {output_dir / 'classification_report.txt'}")
    
    # 9. Save final model
    print("\n" + "=" * 80)
    print("Saving Final Model")
    print("=" * 80 + "\n")
    
    final_model_path = output_dir / 'final_model'
    final_model_path.mkdir(parents=True, exist_ok=True)
    torch.save({'model_state_dict': model.state_dict(), 'config': vars(args), 'test_results': test_results}, final_model_path / 'pytorch_model.bin')
    with open(final_model_path / 'config.json', 'w') as f:
        json.dump({'model_type': 'gpn', 'num_labels': args.num_labels, 'hidden_size': 768, 'classifier_dropout': args.classifier_dropout}, f, indent=2)
    print(f"Model saved to: {final_model_path}")
    
    print("\n" + "=" * 80)
    print("? Training Completed Successfully!")
    print("=" * 80 + "\n")
    
    return 0


if __name__ == '__main__':
    exit(main())

