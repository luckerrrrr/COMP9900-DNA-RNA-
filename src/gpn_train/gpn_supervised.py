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
    PreTrainedModel,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback
)
from transformers.modeling_outputs import SequenceClassifierOutput
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
    
    # 4. Training arguments
    print("\n" + "=" * 80)
    print("Training Setup")
    print("=" * 80 + "\n")
    
    training_args = TrainingArguments(
        # Output directory
        output_dir=args.output,
        overwrite_output_dir=True,
        
        # Training parameters
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        learning_rate=args.lr,
        weight_decay=args.weight_decay,
        warmup_ratio=args.warmup_ratio,
        
        # Evaluation and saving
        evaluation_strategy="steps",
        eval_steps=args.eval_steps,
        save_strategy="steps",
        save_steps=args.save_steps,
        save_total_limit=args.save_total_limit,
        
        # Best model
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        
        # Logging
        logging_dir=f"{args.output}/logs",
        logging_steps=50,
        report_to="tensorboard",
        
        # Advanced features
        fp16=args.fp16,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        
        # Others
        seed=args.seed,
        dataloader_num_workers=2,
        remove_unused_columns=False,
    )
    
    # 5. Create Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        callbacks=[
            EarlyStoppingCallback(early_stopping_patience=args.early_stopping_patience)
        ]
    )
    
    # 6. Start training
    print("\n" + "=" * 80)
    print("? Starting Training")
    print("=" * 80 + "\n")
    
    trainer.train()
    
    # 7. Evaluate on test set
    print("\n" + "=" * 80)
    print("? Evaluating on Test Set")
    print("=" * 80 + "\n")
    
    test_results = trainer.evaluate(test_dataset)
    
    print("\nTest Results:")
    for key, value in test_results.items():
        print(f"  {key}: {value:.4f}")
    
    # Save test results
    test_results_file = Path(args.output) / 'test_results.json'
    with open(test_results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"\nTest results saved to: {test_results_file}")
    
    # 8. Generate detailed classification report
    print("\n" + "=" * 80)
    print("? Generating Classification Report")
    print("=" * 80 + "\n")
    
    predictions_output = trainer.predict(test_dataset)
    predictions = np.argmax(predictions_output.predictions, axis=1)
    labels = predictions_output.label_ids
    
    # Classification report
    report = classification_report(
        labels,
        predictions,
        target_names=['non-conserved', 'conserved'],
        digits=4
    )
    print(report)
    
    # Confusion matrix
    cm = confusion_matrix(labels, predictions)
    print("Confusion Matrix:")
    print(cm)
    
    # Save classification report
    report_file = Path(args.output) / 'classification_report.txt'
    with open(report_file, 'w') as f:
        f.write("Classification Report\n")
        f.write("=" * 80 + "\n\n")
        f.write(report)
        f.write("\n\nConfusion Matrix:\n")
        f.write(str(cm))
    print(f"\nClassification report saved to: {report_file}")
    
    # 9. Save final model
    print("\n" + "=" * 80)
    print("? Saving Final Model")
    print("=" * 80 + "\n")
    
    final_model_path = Path(args.output) / 'final_model'
    trainer.save_model(str(final_model_path))
    print(f"Model saved to: {final_model_path}")
    
    print("\n" + "=" * 80)
    print("? Training Completed Successfully!")
    print("=" * 80 + "\n")
    
    return 0


if __name__ == '__main__':
    exit(main())

