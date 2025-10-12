# GenomeLoader - Genomic Models and Datasets Loader

A unified Python loader for GPN (Genomic Pre-trained Network) models and genomic datasets.

---

## 1. Features

### Model Loading
- **GPN-Brassicales**: Plant genome model trained on Brassicales species
- **GPN-MSA-Sapiens**: Multi-species alignment model (human + 89 vertebrates)
- Automatic caching and memory management

### Dataset Loading
- **Brassicales Dataset**: ~4M plant genome sequences (train/validation/test splits)
- **MSA-Sapiens Dataset**: ~4.5M multi-species alignment samples
- **Multiz100way Dataset**: 100-species vertebrate alignment (streaming or local)
- **Dark Matter Dataset**: Local human genome annotation files (GTF/FASTA)

### Key Capabilities
- Automatic cache management for models and datasets
- Support for both streaming and local dataset access
- Configurable cache directories
- Unified interface for all genomic data sources

---

## 2. Quick Start

### Basic Usage

```python
from data.loader import GenomeLoader

# Initialize loader
loader = GenomeLoader()

# Load models
gpn_model = loader.load_gpn_brassicales_model()
msa_model = loader.load_gpn_msa_sapiens_model()

# Load datasets
brassicales_data = loader.load_brassicales_dataset()
msa_data = loader.load_msa_sapiens_dataset()
multiz_data = loader.load_multiz100way_dataset()

# Load local Dark Matter data
dark_matter = loader.load_dark_matter_data()
```

### Running on Katana HPC

#### Method 1: Using PBS Job System (Recommended)

```bash
cd ~/capstone-project-25t3-9900-f09c-donut

# Create configuration
mkdir -p configs logs/training_logs
echo "data/loader.py" > configs/container_run_loader.txt

# Submit job
qsub -N loader-test -o logs/training_logs/ -v RUNCONF="configs/container_run_loader.txt" run.pbs

# Check status
qstat -u $USER

# View results (after completion)
cat logs/training_logs/<JOB_ID>.kman.restech.unsw.edu.au.OU
```

#### Method 2: Interactive Session

```bash
# Request interactive compute node
qsub -I -l select=1:ncpus=4:mem=32gb,walltime=1:00:00

# Navigate to project
cd ~/capstone-project-25t3-9900-f09c-donut

# Run in container
apptainer run /srv/scratch/$USER/images/p3.sif python3 data/loader.py
```

#### Method 3: Direct Python Import

```python
# In your own script
from data.loader import GenomeLoader, load_all_models_and_datasets

# Option 1: Step by step
loader = GenomeLoader()
model = loader.load_gpn_brassicales_model()
dataset = loader.load_brassicales_dataset()

# Option 2: Load everything at once
loader, gpn, msa, dark_matter, brassicales = load_all_models_and_datasets()
```

---

## 3. API Reference

### Class: `GenomeLoader`

#### Initialization
```python
loader = GenomeLoader(cache_dir="cache", data_dir="data")
```
- `cache_dir`: Directory for caching models and datasets (default: `"cache"`)
- `data_dir`: Directory for local data files (default: `"data"`)

#### Model Loading Methods

##### `load_model(model_name)`
Load a GPN model from Hugging Face.
```python
model = loader.load_model("gpn-brassicales")
```

##### `load_gpn_brassicales_model()`
Load GPN-Brassicales model (plant genomes).
```python
model = loader.load_gpn_brassicales_model()
```

##### `load_gpn_msa_sapiens_model()`
Load GPN-MSA-Sapiens model (human + 89 vertebrates).
```python
model = loader.load_gpn_msa_sapiens_model()
```

#### Dataset Loading Methods

##### `load_hf_dataset(dataset_name)`
Load any Hugging Face dataset.
```python
dataset = loader.load_hf_dataset("songlab/genomes-brassicales-balanced-v1")
```

##### `load_brassicales_dataset()`
Load Brassicales plant genomes dataset.
```python
dataset = loader.load_brassicales_dataset()
# Returns: DatasetDict with train/validation/test splits
# - train: 4,066,336 samples
# - validation: 127,748 samples
# - test: 186,636 samples
```

##### `load_msa_sapiens_dataset()`
Load MSA-Sapiens dataset (multi-species alignment).
```python
dataset = loader.load_msa_sapiens_dataset()
# Returns: DatasetDict with train/validation/test splits
# - train: 4,415,694 samples
# - validation: 41,586 samples
# - test: 55,004 samples
```

##### `load_multiz100way_dataset(msa_version="89", streaming=True)`
Load Multiz100way vertebrate alignment dataset.
```python
# Streaming mode (no download, ~10GB memory)
genome_msa = loader.load_multiz100way_dataset(msa_version="89", streaming=True)

# Local mode (requires download, faster queries)
genome_msa = loader.load_multiz100way_dataset(msa_version="89", streaming=False)

# Query multi-species alignment
X = genome_msa.get_msa(chrom="1", start=1000, end=2000, strand="+")
```

**Parameters:**
- `msa_version`: `"89"` (human + 89 vertebrates) or `"99"` (human + 99 vertebrates)
- `streaming`: `True` for streaming access, `False` for local file

**Returns:** `GenomeMSA` object for querying alignments

##### `load_dark_matter_data()`
Load local Dark Matter of the Genome dataset.
```python
files = loader.load_dark_matter_data()
# Returns: Dictionary with paths to:
# - 'annotation': gencode.v38.basic.annotation.gtf
# - 'chromosome_1': Homo_sapiens.GRCh38.dna.chromosome.1.fa
# - 'lncrna': gencode.v38.long_noncoding_RNAs.gtf
```

**Expected directory structure:**
```
data/Dark Matter of the Genome data/
©À©¤©¤ gencode.v38.basic.annotation.gtf
©À©¤©¤ Homo_sapiens.GRCh38.dna.chromosome.1.fa
©¸©¤©¤ gencode.v38.long_noncoding_RNAs.gtf
```

#### Information Methods

##### `get_info()`
Get information about loaded models and cached datasets.
```python
info = loader.get_info()
# Returns: Dictionary with keys:
# - loaded_models: List of currently loaded models
# - dark_matter_available: Boolean
# - dark_matter_files: List of available Dark Matter files
# - cache_directory: Path to cache directory
# - datasets_cache_directory: Path to datasets cache
# - cached_datasets: List of cached datasets
```


## 4. Data Storage

### Cache Structure
```
capstone-project-25t3-9900-f09c-donut/
©À©¤©¤ cache/
©¦   ©À©¤©¤ models--songlab--gpn-brassicales/    (252MB)
©¦   ©À©¤©¤ models--songlab--gpn-msa-sapiens/    (328MB)
©¦   ©¸©¤©¤ datasets/
©¦       ©À©¤©¤ songlab___genomes-brassicales-balanced-v1/    (1.6GB)
©¦       ©¸©¤©¤ songlab___gpn-msa-sapiens-dataset/            (varies)
©¸©¤©¤ data/
    ©¸©¤©¤ Dark Matter of the Genome data/
        ©À©¤©¤ gencode.v38.basic.annotation.gtf         (857MB)
        ©À©¤©¤ Homo_sapiens.GRCh38.dna.chromosome.1.fa  (241MB)
        ©¸©¤©¤ gencode.v38.long_noncoding_RNAs.gtf      (86MB)
```

### Katana HPC Storage
- **Models & Datasets**: Cached in `/srv/scratch/$USER/hf_cache/`
- **Container**: `/srv/scratch/$USER/images/p3.sif`
- **Multiz100way**: Streamed from Hugging Face (not stored locally by default)

### Constants
```python
# Dataset names
DATASET_BRASSICALES = "songlab/genomes-brassicales-balanced-v1"
DATASET_MSA_SAPIENS = "songlab/gpn-msa-sapiens-dataset"
DATASET_MULTIZ100WAY = "songlab/multiz100way"

# Model names
MODEL_GPN_BRASSICALES = "gpn-brassicales"
MODEL_GPN_MSA_SAPIENS = "gpn-msa-sapiens"
```

---

## Authors

9900-F09C-DONUT Team  
UNSW Capstone Project 2025
