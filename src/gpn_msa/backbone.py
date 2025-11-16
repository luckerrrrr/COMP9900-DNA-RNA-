# gpn_backbone.py
import torch
import torch.nn as nn
from typing import Optional
from data.loader import GenomeLoader
# from gpn.msa.embedding import MSAEmbedding
# from gpn.legacy import GPNRoFormerForMaskedLM

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class GPNBackbone(nn.Module):
    """
    正确的 GPN-MSA backbone 封装
    - 输入: input_ids (B, N_species, L)
    - 输出: last_hidden_state (B, L, H)
    """

    def __init__(self, model_name="songlab/gpn-msa-sapiens", cache_dir="cache"):
        super().__init__()
        print(f"🔥 Loading official GPN-MSA model: {model_name}")
        loader = GenomeLoader(cache_dir=cache_dir)
        self.model = loader.load_gpn_msa_sapiens_model(masked=False).to(DEVICE)
        self.hidden_size = self.model.config.hidden_size
        print(f"✅ GPN-MSA loaded. hidden_size = {self.hidden_size}")

    def forward(self, input_ids, aux_features):
        """
        input_ids:      (B, L)
        aux_features:   (B, L, F)
        attention_mask: (B, L)
        """
        with torch.no_grad():
            out = self.model(input_ids=input_ids, aux_features=aux_features)
            return out

    # utility
    def freeze(self):
        for p in self.parameters():
            p.requires_grad = False

    def unfreeze(self):
        for p in self.parameters():
            p.requires_grad = True
