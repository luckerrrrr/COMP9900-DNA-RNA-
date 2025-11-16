# gpn_classifier.py
import torch
import torch.nn as nn

class GPNClassifier(nn.Module):
    """
    GPN-MSA classifier:
        backbone(input_ids, aux_features)  → last_hidden_state
        → mean pooling → MLP → logits
    """

    def __init__(self, backbone, dropout=0.1, head_hidden_ratio=0.5):
        super().__init__()
        self.backbone = backbone
        H = backbone.hidden_size   # hidden=768

        head_hidden = max(32, int(H * head_hidden_ratio))

        self.classifier = nn.Sequential(
            nn.Linear(H, head_hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(head_hidden, 1),
        )

    def forward(self, input_ids, aux_features=None):
        """
        input_ids: (B, L)
        aux_features: (B, L, F)
        NOT providing attention_mask because:
            GPN-MSA backbone auto-generates padding mask internally.
        """

        # ---- 1. backbone forward ----
        out = self.backbone(
            input_ids=input_ids,
            aux_features=aux_features
        )

        # out.last_hidden_state: (B, L', H)
        # L' ≠ L；GPN-MSA downsample windows internally (e.g., 512→128)

        hidden = out.last_hidden_state               # (B, L', H)

        # ---- 2. mean pooling ----
        pooled = hidden.mean(dim=1)                  # (B, H)

        # ---- 3. MLP classifier ----
        logits = self.classifier(pooled).squeeze(-1) # (B,)

        return logits

    # ==================== FREEZE / UNFREEZE ====================
    def freeze_backbone(self):
        self.backbone.freeze()

    def unfreeze_backbone(self):
        self.backbone.unfreeze()
