#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Genome Data Loader for GPN Models
# Purpose: Unified loader for GPN models and genomic datasets from Hugging Face
# Features: Model loading (gpn-brassicales, gpn-msa-sapiens), Dataset loading (Brassicales, MSA-Sapiens, Multiz100way)
# Usage: loader = GenomeLoader(); model = loader.load_gpn_brassicales_model(); dataset = loader.load_brassicales_dataset()

from pathlib import Path
from transformers import AutoModelForMaskedLM, AutoModel
import gpn.model  # Register custom models
import os
from datasets import load_dataset


# Dataset and model name constants
# These constants define the Hugging Face model and dataset identifiers
DATASET_BRASSICALES = "songlab/genomes-brassicales-balanced-v1"  # Plant genome sequences
DATASET_MSA_SAPIENS = "songlab/gpn-msa-sapiens-dataset"         # Human + 89 vertebrate alignment
DATASET_MULTIZ100WAY = "songlab/multiz100way"                   # 100-species vertebrate alignment

MODEL_GPN_BRASSICALES = "gpn-brassicales"  # Plant genome pre-trained model
MODEL_GPN_MSA_SAPIENS = "gpn-msa-sapiens"  # Human genome pre-trained model


class GenomeLoader:
    # Unified loader for genomic models and datasets with automatic caching
    
    def __init__(self, cache_dir="cache", data_dir="data"):
        # Initialize loader with cache directories
        # Args: cache_dir (models/datasets cache), data_dir (local data files)
        self.cache_dir = Path(cache_dir)
        self.data_dir = Path(data_dir)
        self.datasets_cache_dir = self.cache_dir / "datasets"
        self.models = {}  # Cache for unmasked models
        self.masked_models = {}  # Cache for masked models
        
        # Create directories if they don't exist
        self.cache_dir.mkdir(exist_ok=True)
        self.datasets_cache_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        
        # Set Hugging Face cache directories for automatic caching
        os.environ['HF_DATASETS_CACHE'] = str(self.datasets_cache_dir)
        os.environ['HF_HOME'] = str(self.cache_dir)
    
    # Model loading methods
    
    def load_model(self, model_name, masked=True):
        # Load GPN model from Hugging Face with caching
        # Args: model_name (gpn-brassicales or gpn-msa-sapiens), masked (True for masked LM, False for base model)
        # Returns: Loaded transformers model
        model_list = self.models if not masked else self.masked_models
        
        # Check if model is already cached in memory
        if model_name in model_list:
            print(f"Using cached {model_name} model")
            return model_list[model_name]
        
        print(f"Loading {model_name} model...")
        try:
            # Select model class based on masked parameter
            preTrainAutoModel = AutoModelForMaskedLM if masked else AutoModel
            # Load from Hugging Face Hub with local caching
            model = preTrainAutoModel.from_pretrained(
                f"songlab/{model_name}",
                cache_dir=str(self.cache_dir),
                trust_remote_code=True  # Required for custom GPN architectures
            )
            model_list[model_name] = model  # Cache in memory
            print(f"{model_name} model loaded successfully!")
            return model
        except Exception as e:
            print(f"Failed to load {model_name} model: {e}")
            raise
    
    def load_gpn_brassicales_model(self, masked=True):
        # Load GPN-Brassicales plant genome model
        # Args: masked (True for masked LM variant)
        return self.load_model(MODEL_GPN_BRASSICALES, masked)
    
    def load_gpn_msa_sapiens_model(self, masked=True):
        # Load GPN-MSA-Sapiens human genome model
        # Args: masked (True for masked LM variant)
        return self.load_model(MODEL_GPN_MSA_SAPIENS, masked)
    
    # Dataset loading methods
    
    def load_hf_dataset(self, dataset_name):
        # Load Hugging Face dataset
        print(f"Loading Hugging Face dataset: {dataset_name}")
        try:
            dataset = load_dataset(dataset_name, cache_dir=str(self.datasets_cache_dir))
            print(f"Dataset loaded successfully! Keys: {list(dataset.keys())}")
            if 'train' in dataset:
                print(f"Train samples: {len(dataset['train'])}")
            return dataset
        except Exception as e:
            print(f"Failed to load dataset {dataset_name}: {e}")
            return None
    
    def load_brassicales_dataset(self):
        # Load Brassicales plant genomes dataset (for gpn-brassicales)
        return self.load_hf_dataset(DATASET_BRASSICALES)
    
    def load_msa_sapiens_dataset(self):
        # Load MSA-Sapiens dataset (human + 89 vertebrates, for gpn-msa-sapiens)
        return self.load_hf_dataset(DATASET_MSA_SAPIENS)
    
    def load_multiz100way_dataset(self, msa_version="89", streaming=True):
        # Load Multiz100way dataset (100-species vertebrate alignment)
        # This dataset uses Zarr format and requires gpn.data.GenomeMSA
        # msa_version: "89" (human + 89 vertebrates) or "99" (human + 99 vertebrates)
        # streaming: True for streaming (no download), False for local path
        
        print(f"Loading Multiz100way dataset (version: {msa_version}, streaming: {streaming})")
        
        try:
            from gpn.data import GenomeMSA
            
            if streaming:
                # Streaming mode: direct access from HuggingFace
                msa_path = f"zip:///::https://huggingface.co/datasets/songlab/multiz100way/resolve/main/{msa_version}.zarr.zip"
                print(f"Using streaming mode: {msa_path}")
                print("Note: Streaming is slower but requires no download")
            else:
                # Local mode: assumes data is downloaded and extracted
                msa_path = self.data_dir / f"{msa_version}.zarr"
                if not msa_path.exists():
                    print(f"Local dataset not found: {msa_path}")
                    print(f"Download with: wget https://huggingface.co/datasets/songlab/multiz100way/resolve/main/{msa_version}.zarr.zip")
                    return None
            
            genome_msa = GenomeMSA(str(msa_path))
            print(f"Multiz100way dataset loaded successfully!")
            return genome_msa
            
        except ImportError:
            print("Error: gpn.data.GenomeMSA not available")
            print("This dataset requires the gpn package")
            return None
        except Exception as e:
            print(f"Failed to load Multiz100way dataset: {e}")
            return None
    
    # Local data loading methods
    
    def load_dark_matter_data(self):
        # Load local Dark Matter of the Genome dataset
        dark_matter_dir = Path("dataset")
        
        if not dark_matter_dir.exists():
            print("Dataset folder not found")
            return None
        
        files = {
            'annotation': dark_matter_dir / "gencode.v38.basic.annotation.gtf",
            'chromosome_1': dark_matter_dir / "Homo_sapiens.GRCh38.dna.chromosome.1.fa",
            'lncrna': dark_matter_dir / "gencode.v38.long_noncoding_RNAs.gtf"
        }
        
        # Check if all required files exist
        missing = [name for name, path in files.items() if not path.exists()]
        if missing:
            print(f"Missing files: {missing}")
            return None
        
        print("Dark Matter dataset loaded successfully!")
        return files
    
    # Information methods
    
    def get_info(self):
        # Get information about loaded models and cached datasets
        dark_matter_dir = Path("dataset")
        
        datasets_available = self.datasets_cache_dir.exists() and any(self.datasets_cache_dir.iterdir())
        cached_datasets = []
        if datasets_available:
            for item in self.datasets_cache_dir.iterdir():
                if item.is_dir():
                    cached_datasets.append(item.name)
        
        return {
            'loaded_models': list(self.models.keys()),
            'dark_matter_available': dark_matter_dir.exists(),
            'dark_matter_files': [f.name for f in dark_matter_dir.iterdir()] if dark_matter_dir.exists() else [],
            'cache_directory': str(self.cache_dir),
            'datasets_cache_directory': str(self.datasets_cache_dir),
            'cached_datasets': cached_datasets
        }


# Convenience function
def load_all_models_and_datasets():
    # Load all models and primary datasets
    loader = GenomeLoader()
    gpn_model = loader.load_gpn_brassicales_model()
    gpn_msa_model = loader.load_gpn_msa_sapiens_model()
    dark_matter_data = loader.load_dark_matter_data()
    brassicales_dataset = loader.load_brassicales_dataset()
    
    return loader, gpn_model, gpn_msa_model, dark_matter_data, brassicales_dataset


# Test code
if __name__ == "__main__":
    print("Testing Genome Data Loader")
    print("=" * 40)
    
    loader = GenomeLoader()
    
    # Test model loading
    print("\n[1] Testing model loading...")
    try:
        gpn_model = loader.load_gpn_brassicales_model()
        gpn_msa_model = loader.load_gpn_msa_sapiens_model()
    except Exception as e:
        print(f"Model loading error: {e}")
    
    # Test local data loading
    print("\n[2] Testing Dark Matter data loading...")
    dark_matter_data = loader.load_dark_matter_data()
    if dark_matter_data:
        print("Available files:")
        for name, path in dark_matter_data.items():
            print(f"  {name}: {path.name}")
    
    # Test HF datasets loading
    print("\n[3] Testing Hugging Face datasets loading...")
    
    print("\n[3.1] Brassicales dataset...")
    brassicales_dataset = loader.load_brassicales_dataset()
    if brassicales_dataset:
        for split_name, split_data in brassicales_dataset.items():
            print(f"  {split_name}: {len(split_data)} samples")
    
    print("\n[3.2] MSA-Sapiens dataset...")
    msa_dataset = loader.load_msa_sapiens_dataset()
    if msa_dataset:
        for split_name, split_data in msa_dataset.items():
            print(f"  {split_name}: {len(split_data)} samples")
    
    print("\n[3.3] Multiz100way dataset...")
    multiz_dataset = loader.load_multiz100way_dataset()
    if multiz_dataset:
        print("  Dataset loaded successfully!")
        print("  Note: This is a GenomeMSA object, use .get_msa(chrom, start, end) to query")
    
    # Show summary
    print("\n[4] Data information:")
    info = loader.get_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    print("\nTest completed!")
