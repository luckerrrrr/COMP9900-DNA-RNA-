# src/load_gpn.py
# Purpose: Minimal script to load the GPN model and verify the environment & cache setup

import gpn.model  # Required: register the custom model
from transformers import AutoModelForMaskedLM

print("Loading model...")
model = AutoModelForMaskedLM.from_pretrained(
    "songlab/gpn-brassicales"  # Weights will be cached in HF_HOME (pointing to scratch)
)
print("✓ Model loaded.")
print(f"Model class: {model.__class__.__name__}")
