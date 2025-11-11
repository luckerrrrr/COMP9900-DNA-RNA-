from src.gpn_msa.backbone import GPNBackbone
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

class GPNClassifier(nn.Module):
    """
    Classifier wrapper:
      - 接收 backbone（GPNBackbone 对象）
      - 做 pooling（mean pool over sequence length）
      - MLP 分类头：Linear -> ReLU -> Dropout -> Linear -> logits
    输出：
      logits: FloatTensor [B]  (未经过 sigmoid)
    """
    def __init__(self, backbone: GPNBackbone, head_hidden_ratio: float = 0.5, dropout: float = 0.1):
        """
        Args:
          backbone: GPNBackbone 实例（可以是实际 HF backbone 或 dummy）
          head_hidden_ratio: classification hidden dim = hidden_size * ratio
          dropout: dropout prob for head
        """
        super().__init__()
        self.backbone = backbone
        self.hidden_size = getattr(backbone, "hidden_size", getattr(backbone, "config", {}).get("hidden_size", 256))
        head_h = max(8, int(self.hidden_size * head_hidden_ratio))  # head hidden dim 最小 8
        # 分类头（两层 MLP）
        self.pooling = self.mean_pool  # 可替换为 cls_pool / max_pool
        self.classifier = nn.Sequential(
            nn.Linear(self.hidden_size, head_h),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(head_h, 1)  # 输出单个 logit（用于 BCEWithLogitsLoss）
        )

    @staticmethod
    def mean_pool(hidden_states: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        mean_pool: 对 sequence 长度维度做平均
        Args:
          hidden_states: [B, L, H]
          mask: Optional [B, L] where 1=keep, 0=pad (如果有 pad，需要做 masked mean)
        Returns:
          pooled: [B, H]
        """
        if mask is None:
            return hidden_states.mean(dim=1)
        else:
            # mask: 1 means valid token
            mask = mask.unsqueeze(-1).to(hidden_states.dtype)  # [B, L, 1]
            sum_h = (hidden_states * mask).sum(dim=1)  # [B, H]
            denom = mask.sum(dim=1).clamp(min=1e-6)    # [B, 1]
            return sum_h / denom

    def forward(self, input_ids: torch.LongTensor, aux_features: Optional[torch.Tensor] = None, attention_mask: Optional[torch.Tensor] = None):
        """
        Args:
          input_ids: LongTensor [B, L]
          aux_features: optional FloatTensor [B, L, F]
          attention_mask: optional LongTensor [B, L] (1 for valid, 0 for pad) - 用于 masked mean pooling
        Returns:
          logits: FloatTensor [B]
        """
        # 1) backbone forward -> get last_hidden_state [B, L, H]
        out = self.backbone(input_ids=input_ids, aux_features=aux_features)
        last_hidden = out.last_hidden_state  # [B, L, H]
        # 2) pool
        pooled = self.pooling(last_hidden, mask=attention_mask)  # [B, H]
        # 3) classifier head -> logits [B, 1] -> squeeze -> [B]
        logits = self.classifier(pooled).squeeze(-1)
        return logits

    def freeze_backbone(self):
        """冻结 backbone 参数（只训练 head）"""
        for p in self.backbone.parameters():
            p.requires_grad = False

    def unfreeze_backbone(self):
        """解冻 backbone 参数（训练整个模型）"""
        for p in self.backbone.parameters():
            p.requires_grad = True
