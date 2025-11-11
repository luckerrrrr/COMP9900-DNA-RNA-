# -*- coding: utf-8 -*-
"""
Backbone for end-to-end fine-tune pipeline.
- First tries to load the real GPN backbone using GenomeLoader (Hugging Face)
- Falls back to a small dummy Transformer backbone for offline/local debugging
"""

from typing import Optional
import torch
import torch.nn as nn

# Import unified loader
from data.loader import GenomeLoader, MODEL_GPN_MSA_SAPIENS


class BackboneLoadError(Exception):
    """Custom exception for backbone loading failures."""
    pass


class GPNBackbone(nn.Module):
    """
    Backbone wrapper:
      - If GenomeLoader (Hugging Face) model can be loaded, use it directly.
      - Otherwise, fall back to a local dummy transformer encoder.
    Interface:
      forward(input_ids, aux_features=None) -> object with attribute `last_hidden_state`
      last_hidden_state: Tensor [B, L, H]
    """
    def __init__(
        self,
        model_name: str = MODEL_GPN_MSA_SAPIENS,
        hidden_size: int = 256,
        use_dummy_if_failed: bool = True,
        cache_dir: Optional[str] = None,
    ):
        """
        Args:
            model_name: Hugging Face model name (default: gpn-msa-sapiens)
            hidden_size: dummy backbone hidden size (used if HF model fails)
            use_dummy_if_failed: fallback to dummy if load fails
            cache_dir: optional cache directory for HF models
        """
        super().__init__()
        self.model_name = model_name
        self.hidden_size = hidden_size
        self._using_dummy = False

        # Try to load using GenomeLoader first
        try:
            loader = GenomeLoader(cache_dir or "cache")
            print(f"🧬 Using GenomeLoader to load model: {model_name}")
            self._hf_model = loader.load_gpn_msa_sapiens_model(masked=False)
            self.hidden_size = getattr(self._hf_model.config, "hidden_size", hidden_size)
            self._using_dummy = False
            print(f"✅ Loaded HF model '{model_name}' with hidden size = {self.hidden_size}")
            return
        except Exception as e:
            print(f"⚠️ GenomeLoader failed to load model {model_name}: {e}")
            if not use_dummy_if_failed:
                raise BackboneLoadError(f"Failed to load model {model_name}") from e
            print("➡️ Falling back to dummy backbone for local testing")

        # Dummy backbone (Embedding + small TransformerEncoder)
        self._using_dummy = True
        vocab_size = 32
        emb_size = hidden_size
        self.token_embedding = nn.Embedding(vocab_size, emb_size, padding_idx=0)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=emb_size,
            nhead=8,
            dim_feedforward=emb_size * 4,
            activation="relu",
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=2)
        # Expose config-like object for compatibility
        self.config = type("C", (), {"hidden_size": emb_size})

    # ------------------------------------------------------------------ #
    # Forward pass
    # ------------------------------------------------------------------ #
    def forward(
        self,
        input_ids: torch.LongTensor,
        aux_features: Optional[torch.Tensor] = None,
    ):
        """
        Args:
            input_ids: LongTensor [B, L] - token IDs
            aux_features: optional FloatTensor [B, L, F]
        Returns:
            An object with attribute `last_hidden_state` (Tensor [B, L, H])
        """
        if self._using_dummy:
            # Simple embedding + transformer flow
            x = self.token_embedding(input_ids)  # [B, L, H]

            if aux_features is not None:
                # Optional projection of aux features to hidden space
                proj = getattr(self, "_aux_proj", None)
                if proj is None:
                    self._aux_proj = nn.Linear(aux_features.shape[-1], self.hidden_size).to(aux_features.device)
                    proj = self._aux_proj
                x = x + proj(aux_features)

            # Transformer encoder
            h = self.transformer(x)  # [B, L, H]
            # Return a namespace-like object to mimic HF output
            return type("O", (), {"last_hidden_state": h})

        else:
            # Hugging Face model forward pass
            try:
                out = self._hf_model(input_ids=input_ids, aux_features=aux_features, return_dict=True)
            except TypeError:
                # Some models don't support aux_features
                out = self._hf_model(input_ids=input_ids, return_dict=True)
            return out

    # ------------------------------------------------------------------ #
    # Utility
    # ------------------------------------------------------------------ #
    def using_dummy(self) -> bool:
        """Return True if dummy backbone is being used."""
        return self._using_dummy
    
    def model_instance(self):
        return self._hf_model


# ------------------------------------------------------------------ #
# Local test block
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    model = GPNBackbone()
    print(f"Model loaded: dummy={model.using_dummy()}, hidden_size={model.hidden_size}")

    # Smoke test
    x = torch.randint(0, 8, (2, 512))
    y = model(x)
    print("Output:", y.last_hidden_state.shape)
