# src/load_gpn_msa.py
# Purpose: Minimal script to load the GPN-MSA model and verify the environment & cache setup

import gpn.model  # Required: register the custom model
from transformers import AutoModelForMaskedLM

print("Loading model GPN-MSA...")
model = AutoModelForMaskedLM.from_pretrained(
    "songlab/gpn-msa-sapiens"  # Weights will be cached in HF_HOME (pointing to scratch)
)
print("✓ Model loaded.")
print(f"Model class: {model.__class__.__name__}")
