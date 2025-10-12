# Dataset Structure Analysis

Deep dive into genomic datasets structure, loading mechanisms, and implementation details.

---

## 📊 1. Dataset Structure Analysis

### 1.1 Brassicales Dataset

**Source:** `songlab/genomes-brassicales-balanced-v1`

#### Data Splits
```python
{
    'train': 4,066,336 samples
    'validation': 127,748 samples
    'test': 186,636 samples
}
```

#### Field Structure
Each sample contains:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `sequence` | `str` | DNA sequence (A/T/C/G) | `"ATCGATCGATCG..."` |
| `label` | `int` | Classification label | `0`, `1`, `2`, etc. |
| `species` | `str` | Plant species identifier | `"Arabidopsis_thaliana"` |
| `chromosome` | `str` (optional) | Chromosome identifier | `"chr1"`, `"chr2"` |
| `start` | `int` (optional) | Genomic start position | `1000000` |
| `end` | `int` (optional) | Genomic end position | `1001000` |

#### Sequence Characteristics
- **Length:** Fixed or variable (typically ~512-1024 bp)
- **Alphabet:** {A, C, G, T, N}
- **Format:** Raw nucleotide string
- **Species Coverage:** 10 Brassicaceae species

#### Usage Pattern
```python
dataset = loader.load_brassicales_dataset()
sample = dataset['train'][0]

# Access fields
sequence = sample['sequence']  # "ATCGATCG..."
label = sample['label']        # 1
species = sample['species']    # "Arabidopsis_thaliana"
```

---

### 1.2 MSA-Sapiens Dataset

**Source:** `songlab/gpn-msa-sapiens-dataset`

#### Data Splits
```python
{
    'train': 4,415,694 samples
    'validation': 41,586 samples
    'test': 55,004 samples
}
```

#### Field Structure
Each sample contains:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `msa` | `str` or `list` | Multi-species alignment | Aligned sequences from 90 species |
| `sequence` | `str` | Reference (human) sequence | `"ATCGATCG..."` |
| `species_mask` | `list[bool]` | Species presence indicator | `[True, True, False, ...]` |
| `conservation_score` | `float` | Conservation metric | `0.85` |
| `position` | `dict` | Genomic coordinates | `{'chr': '1', 'start': 1000, 'end': 2000}` |

#### MSA Format
- **Alignment depth:** 90 species (Human + 89 vertebrates)
- **Format:** Gap-aligned sequences (`-` for gaps)
- **Reference:** Human genome (hg38)
- **Species:** Mammals, birds, reptiles, fish

#### Usage Pattern
```python
dataset = loader.load_msa_sapiens_dataset()
sample = dataset['train'][0]

# Access MSA data
msa = sample['msa']                         # Aligned sequences
human_seq = sample['sequence']              # Reference sequence
conservation = sample['conservation_score']  # 0.85
```

---

### 1.3 Multiz100way Dataset

**Source:** `songlab/multiz100way`

#### Structure
- **Format:** Zarr (compressed columnar storage)
- **Versions:** 
  - `89.zarr`: Human + 89 vertebrates (~50GB)
  - `99.zarr`: Human + 99 vertebrates (~60GB)

#### Query-Based Access
Unlike static datasets, Multiz100way uses **query interface**:

```python
msa = multiz.get_msa(
    chrom='chr1',      # Chromosome
    start=1000000,     # Start position
    end=1001000,       # End position
    strand='+'         # Strand (optional)
)
```

#### Returns
- **Type:** NumPy array or custom MSA object
- **Shape:** `(num_species, sequence_length)`
- **Content:** Aligned nucleotides with gaps

#### Data Characteristics
| Property | Value |
|----------|-------|
| **Total alignments** | ~3 billion base pairs |
| **Coverage** | ~95-98% of human genome |
| **Species** | 90-100 vertebrates |
| **Format** | One-hot encoded or character array |

---

### 1.4 GENCODE Dataset

**Source:** Local files (Manual download required)

#### Structure
- **Format:** GTF (Gene Transfer Format) + FASTA
- **Version:** v38 (GRCh38/hg38)
- **Components:** 3 files

#### File Breakdown

| File | Format | Size | Description |
|------|--------|------|-------------|
| `gencode.v38.basic.annotation.gtf` | GTF | 857 MB | Comprehensive gene annotations |
| `Homo_sapiens.GRCh38.dna.chromosome.1.fa` | FASTA | 241 MB | Chromosome 1 DNA sequence |
| `gencode.v38.long_noncoding_RNAs.gtf` | GTF | 86 MB | lncRNA-specific annotations |

---

#### File Usage and Relationships

**Purpose and Training Stages:**

| File | Stage | Purpose | Notes |
|------|-------|---------|-------|
| `Homo_sapiens.GRCh38.dna.chromosome.1.fa` | **Testing** | Validate training pipeline | Quick test with chr1 only |
| `gencode.v38.basic.annotation.gtf` | **Retraining** | Full gene annotations for GPN retrain | Complete annotation set |
| `gencode.v38.long_noncoding_RNAs.gtf` | **Fine-tuning** | lncRNA-specific fine-tuning | Subset of basic.annotation |

**Key Relationships:**

```
gencode.v38.basic.annotation.gtf (Complete Annotations)
    ├─ Contains ALL gene types:
    │   ├─ protein_coding genes (~20,000)
    │   ├─ lncRNA genes (~20,000)      ← Extracted to separate file
    │   ├─ pseudogenes
    │   ├─ miRNA, snRNA, etc.
    │   └─ Other non-coding features
    │
    └─ Filtered Subset ↓
       gencode.v38.long_noncoding_RNAs.gtf (lncRNA Only)
           └─ Only entries where gene_type = "lncRNA"
           └─ Used for specialized model fine-tuning
```

**Workflow Diagram:**

```
Step 1: Pipeline Testing
    └─ Use: Homo_sapiens.GRCh38.dna.chromosome.1.fa
    └─ Goal: Verify training code works (fast)
    
Step 2: Full Model Retraining
    └─ Use: gencode.v38.basic.annotation.gtf
    └─ Goal: Train GPN on complete annotations
    
Step 3: lncRNA Fine-tuning
    └─ Use: gencode.v38.long_noncoding_RNAs.gtf
    └─ Goal: Specialize model for non-coding RNA prediction
```

---

#### GTF Field Structure

Each line in GTF files contains 9 tab-separated fields:

| Field | Example | Description |
|-------|---------|-------------|
| `seqname` | `chr1` | Chromosome name |
| `source` | `HAVANA` | Annotation source |
| `feature` | `gene`, `transcript`, `exon` | Feature type |
| `start` | `11869` | Start position (1-based) |
| `end` | `14409` | End position (inclusive) |
| `score` | `.` | Usually unused |
| `strand` | `+` or `-` | DNA strand |
| `frame` | `0`, `1`, `2` | Reading frame (for CDS) |
| `attributes` | `gene_id "ENSG00000..."; gene_type "lncRNA"` | Key-value pairs |

#### GTF Attributes (Key Information)

Common attributes in annotation files:

```python
gene_id "ENSG00000223972"        # Ensembl gene ID
gene_type "lncRNA"                # Gene biotype (determines if in lncRNA file)
gene_name "DDX11L1"              # Gene symbol
transcript_id "ENST00000456328"  # Transcript ID
exon_number "1"                  # Exon index
```

#### FASTA Format

Chromosome sequence file structure:

```
>1 dna:chromosome chromosome:GRCh38:1:1:248956422:1 REF
NNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN
ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
...
```

- **Header:** `>` followed by chromosome metadata
- **Sequence:** Raw DNA sequence (A, C, G, T, N)
- **Line length:** Typically 50-80 characters per line

#### Usage Pattern

```python
# Load GENCODE files
gencode = loader.load_dark_matter_data()

if gencode:
    # Access file paths
    annotation_gtf = gencode['annotation']      # For retraining
    chromosome_fa = gencode['chromosome_1']     # For testing
    lncrna_gtf = gencode['lncrna']             # For fine-tuning
    
    # Example: Parse GTF file
    import pandas as pd
    
    # Read complete annotations (for retraining)
    df_complete = pd.read_csv(
        annotation_gtf,
        sep='\t',
        comment='#',
        header=None,
        names=['seqname', 'source', 'feature', 'start', 'end', 
               'score', 'strand', 'frame', 'attributes']
    )
    
    # Read lncRNA subset (for fine-tuning)
    df_lncrna = pd.read_csv(
        lncrna_gtf,
        sep='\t',
        comment='#',
        header=None,
        names=['seqname', 'source', 'feature', 'start', 'end', 
               'score', 'strand', 'frame', 'attributes']
    )
    
    # Verify relationship: lncRNA is subset of complete
    print(f"Complete annotations: {len(df_complete)} rows")
    print(f"lncRNA annotations: {len(df_lncrna)} rows")
    print(f"lncRNA is {len(df_lncrna)/len(df_complete)*100:.1f}% of complete")
    
    # Parse FASTA file (for testing)
    from Bio import SeqIO
    
    for record in SeqIO.parse(chromosome_fa, "fasta"):
        print(f"Chromosome: {record.id}")
        print(f"Length: {len(record.seq)} bp")
        sequence = str(record.seq)
```

#### Data Characteristics

**Basic Annotations (`gencode.v38.basic.annotation.gtf`):**
- **Genes:** ~60,000 (protein-coding + non-coding)
- **Transcripts:** ~230,000
- **Exons:** ~1.4 million
- **Features:** gene, transcript, exon, CDS, UTR, start_codon, stop_codon
- **Use Case:** Complete GPN model retraining

**lncRNA Annotations (`gencode.v38.long_noncoding_RNAs.gtf`):**
- **lncRNA genes:** ~20,000
- **lncRNA transcripts:** ~50,000
- **Types:** lincRNA, antisense, processed_transcript, etc.
- **Relationship:** Strict subset of basic.annotation (filtered by gene_type)
- **Use Case:** Specialized fine-tuning for non-coding RNA prediction

**Chromosome 1 Sequence (`Homo_sapiens.GRCh38.dna.chromosome.1.fa`):**
- **Length:** 248,956,422 bp (~249 Mb)
- **Largest human chromosome**
- **~2,000 genes**
- **Use Case:** Fast pipeline testing before full training

#### Loading Status

```python
# Check if GENCODE data is available
info = loader.get_info()

if info['dark_matter_available']:
    print("GENCODE files found:")
    for file in info['dark_matter_files']:
        print(f"  - {file}")
else:
    print("GENCODE files not found. Please download manually.")
```

#### Download Instructions

**Required downloads:**

1. **Gene annotations (for retraining):**
   ```bash
   wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_38/gencode.v38.basic.annotation.gtf.gz
   gunzip gencode.v38.basic.annotation.gtf.gz
   ```

2. **Chromosome 1 sequence (for testing):**
   ```bash
   wget http://ftp.ensembl.org/pub/release-104/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.chromosome.1.fa.gz
   gunzip Homo_sapiens.GRCh38.dna.chromosome.1.fa.gz
   ```

3. **lncRNA annotations (for fine-tuning):**
   ```bash
   wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_38/gencode.v38.long_noncoding_RNAs.gtf.gz
   gunzip gencode.v38.long_noncoding_RNAs.gtf.gz
   ```

**Move to correct location:**
```bash
mkdir -p "data/GENCODE data"
mv gencode.v38.basic.annotation.gtf "data/GENCODE data/"
mv Homo_sapiens.GRCh38.dna.chromosome.1.fa "data/GENCODE data/"
mv gencode.v38.long_noncoding_RNAs.gtf "data/GENCODE data/"
```

---

## 🔄 2. Data Loading Mechanisms

### 2.1 Standard Loading (HuggingFace Datasets)

#### Implementation
```python
def load_hf_dataset(self, dataset_name):
    dataset = load_dataset(
        dataset_name, 
        cache_dir=str(self.datasets_cache_dir)
    )
    return dataset
```

#### Process Flow
```
1. Check local cache
   ├─ If exists → Load from cache (fast)
   └─ If not exists → Download from HuggingFace
2. Parse dataset format (Arrow/Parquet)
3. Create DatasetDict object
4. Cache for future use
```

#### Characteristics
- **Type:** Eager loading (full download)
- **Storage:** Arrow format (memory-mapped)
- **Access:** Random access by index
- **Speed:** Fast after initial download

---

### 2.2 Streaming Loading (Multiz100way)

#### Implementation
```python
def load_multiz100way_dataset(self, msa_version="89", streaming=True):
    if streaming:
        msa_path = f"zip:///::https://huggingface.co/datasets/songlab/multiz100way/resolve/main/{msa_version}.zarr.zip"
    else:
        msa_path = self.data_dir / f"{msa_version}.zarr"
    
    genome_msa = GenomeMSA(str(msa_path))
    return genome_msa
```

#### Streaming Mode Flow
```
1. Establish connection to remote Zarr store
2. Read metadata (chromosome info, species list)
3. Query-based access:
   ├─ User requests region (chr, start, end)
   ├─ Fetch only required chunks from remote
   ├─ Decompress and decode
   └─ Return alignment array
4. No local storage (except temp cache)
```

#### Local Mode Flow
```
1. Check if local Zarr exists
2. Load from local file system
3. Memory-map Zarr arrays
4. Fast random access to any region
```

#### Comparison

| Aspect | Streaming | Local |
|--------|-----------|-------|
| **Download size** | 0 (on-demand) | 50-60 GB |
| **Initial setup** | Instant | Hours (download) |
| **Query speed** | Slow (~1-10s) | Fast (~0.01s) |
| **Memory usage** | Low (~100MB) | Medium (~1-2GB) |
| **Use case** | Occasional queries | Frequent access |

---

### 2.3 Manual Loading (GENCODE)

#### Implementation
```python
def load_dark_matter_data(self):
    dark_matter_dir = self.data_dir / "GENCODE data"
    
    if not dark_matter_dir.exists():
        print("GENCODE data folder not found")
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
    
    return files
```

#### Process Flow
```
1. Check if GENCODE directory exists
2. Verify all 3 files are present:
   ├─ annotation (for retraining)
   ├─ chromosome_1 (for testing)
   └─ lncrna (for fine-tuning)
3. Return file paths (no parsing)
4. User reads files directly based on training stage
```

#### Characteristics
- **Type:** Direct file access (no caching layer)
- **Storage:** Standard bioinformatics formats (GTF/FASTA)
- **Access:** Sequential file reading
- **Speed:** Depends on file I/O
- **Stage-specific:** Different files for different training stages

#### Why Manual Download?

**Reasons:**
- GENCODE files are standard bioinformatics formats (not HuggingFace format)
- Users may already have these files from other projects
- Allows flexibility in version selection (v38, v39, etc.)
- No dependency on HuggingFace infrastructure
- Files are large and may not be needed by all users
- Different files serve different training stages (test/retrain/fine-tune)

---

## 💾 3. Cache Management

### 3.1 Cache Directory Structure

```
data/cache/
├── models/                                    # Model cache
│   ├── models--songlab--gpn-brassicales/
│   │   ├── snapshots/
│   │   │   └── <commit_hash>/
│   │   │       ├── config.json
│   │   │       ├── pytorch_model.bin        (252 MB)
│   │   │       └── tokenizer.json
│   │   └── refs/
│   └── models--songlab--gpn-msa-sapiens/
│       └── snapshots/
│           └── <commit_hash>/
│               └── pytorch_model.bin        (328 MB)
│
└── datasets/                                 # Dataset cache
    ├── songlab___genomes-brassicales-balanced-v1/
    │   └── default/
    │       └── 0.0.0/
    │           ├── train-00000-of-00001.arrow      (1.2 GB)
    │           ├── validation-00000-of-00001.arrow (40 MB)
    │           ├── test-00000-of-00001.arrow       (60 MB)
    │           └── dataset_info.json
    │
    └── songlab___gpn-msa-sapiens-dataset/
        └── default/
            └── 0.0.0/
                ├── train.parquet                    (1.6 GB)
                ├── validation.parquet               (50 MB)
                └── test.parquet                     (70 MB)
```

### 3.2 Cache Configuration

#### Environment Variables
```python
os.environ['HF_DATASETS_CACHE'] = str(self.datasets_cache_dir)
os.environ['HF_HOME'] = str(self.cache_dir)
```

#### Cache Behavior
```python
class GenomeLoader:
    def __init__(self, cache_dir="cache", data_dir="data"):
        self.cache_dir = Path(cache_dir)
        self.data_dir = Path(data_dir)
        self.datasets_cache_dir = self.cache_dir / "datasets"
        self.models = {}  # In-memory model cache
        
        # Create directories
        self.cache_dir.mkdir(exist_ok=True)
        self.datasets_cache_dir.mkdir(exist_ok=True)
```

#### Multi-Level Caching
1. **Memory Cache** (Runtime)
   - Loaded models stored in `self.models` dictionary
   - Fast access for repeated use in same session
   
2. **Disk Cache** (Persistent)
   - Models: `cache/models/`
   - Datasets: `cache/datasets/`
   - Survives across sessions

3. **Model Caching Logic**
```python
def load_model(self, model_name):
    # Level 1: Check memory cache
    if model_name in self.models:
        print(f"Using cached {model_name} model")
        return self.models[model_name]
    
    # Level 2: Load from disk cache (or download)
    model = AutoModelForMaskedLM.from_pretrained(
        f"songlab/{model_name}",
        cache_dir=str(self.cache_dir),
        trust_remote_code=True
    )
    
    # Store in memory cache
    self.models[model_name] = model
    return model
```

### 3.3 Cache Size Management

| Component | Size | Location | Notes |
|-----------|------|----------|-------|
| GPN-Brassicales model | 252 MB | `cache/models/` | Auto-cached |
| GPN-MSA-Sapiens model | 328 MB | `cache/models/` | Auto-cached |
| Brassicales dataset | 1.6 GB | `cache/datasets/` | Auto-cached |
| MSA-Sapiens dataset | 1.6 GB | `cache/datasets/` | Auto-cached |
| GENCODE basic annotation | 857 MB | `data/GENCODE data/` | Manual, for retraining |
| GENCODE chromosome 1 | 241 MB | `data/GENCODE data/` | Manual, for testing |
| GENCODE lncRNAs | 86 MB | `data/GENCODE data/` | Manual, for fine-tuning |
| **Total (auto-cached)** | **~3.8 GB** | | Downloaded automatically |
| **Total (with GENCODE)** | **~5.0 GB** | | Includes manual downloads |

**Storage Planning:**
- **Minimum setup (testing only):** ~4.1 GB (auto-cached + chr1)
- **Full retraining setup:** ~4.7 GB (auto-cached + basic annotation)
- **Complete setup (all stages):** ~5.0 GB (everything)

---

### 3.4 GENCODE Data Management

Unlike HuggingFace datasets, GENCODE files are **not automatically cached**. They must be:

1. **Downloaded manually** from official sources
2. **Placed in:** `data/GENCODE data/` directory
3. **Used directly** without caching layer
4. **Selected based on training stage:**
   - Testing → `chromosome.1.fa`
   - Retraining → `basic.annotation.gtf`
   - Fine-tuning → `long_noncoding_RNAs.gtf`

#### Why Manual Download?

```python
def load_dark_matter_data(self):
    # Direct file access, no caching
    dark_matter_dir = self.data_dir / "GENCODE data"
    
    if not dark_matter_dir.exists():
        print("GENCODE data folder not found")
        return None
    
    files = {
        'annotation': dark_matter_dir / "gencode.v38.basic.annotation.gtf",
        'chromosome_1': dark_matter_dir / "Homo_sapiens.GRCh38.dna.chromosome.1.fa",
        'lncrna': dark_matter_dir / "gencode.v38.long_noncoding_RNAs.gtf"
    }
    
    # Check if all files exist
    missing = [name for name, path in files.items() if not path.exists()]
    if missing:
        print(f"Missing files: {missing}")
        return None
    
    return files
```

**Reasons:**
- GENCODE files are standard bioinformatics formats (not HuggingFace format)
- Users may already have these files
- Allows flexibility in version selection
- No dependency on HuggingFace infrastructure
- Stage-specific usage (not all files needed for all tasks)

---

## 🔧 4. Code Encapsulation Features

### 4.1 Unified Interface

All datasets accessed through single loader class:
```python
loader = GenomeLoader()

# Consistent API for all datasets
brassicales = loader.load_brassicales_dataset()
msa_sapiens = loader.load_msa_sapiens_dataset()
multiz = loader.load_multiz100way_dataset()
gencode = loader.load_dark_matter_data()
```

### 4.2 Automatic Error Handling

```python
def load_model(self, model_name):
    try:
        model = AutoModelForMaskedLM.from_pretrained(...)
        return model
    except Exception as e:
        print(f"Failed to load {model_name} model: {e}")
        raise  # Re-raise for caller to handle
```

### 4.3 Configuration Abstraction

Users don't need to know:
- HuggingFace dataset names
- Cache directory structure
- Environment variables
- Download mechanisms

They just call simple methods:
```python
dataset = loader.load_brassicales_dataset()  # Everything handled internally
```

### 4.4 Convenience Functions

#### Load Everything
```python
def load_all_models_and_datasets():
    loader = GenomeLoader()
    gpn_model = loader.load_gpn_brassicales_model()
    gpn_msa_model = loader.load_gpn_msa_sapiens_model()
    gencode_data = loader.load_dark_matter_data()
    brassicales_dataset = loader.load_brassicales_dataset()
    
    return loader, gpn_model, gpn_msa_model, gencode_data, brassicales_dataset
```

#### Information Query
```python
info = loader.get_info()
# Returns comprehensive system state:
# {
#     'loaded_models': ['gpn-brassicales', 'gpn-msa-sapiens'],
#     'dark_matter_available': True,
#     'dark_matter_files': ['gencode.v38.basic.annotation.gtf', ...],
#     'cache_directory': 'data/cache',
#     'datasets_cache_directory': 'data/cache/datasets',
#     'cached_datasets': ['songlab___genomes-brassicales-balanced-v1', ...]
# }
```

### 4.5 Flexible Configuration

```python
# Default configuration
loader = GenomeLoader()

# Custom cache location
loader = GenomeLoader(
    cache_dir="/custom/cache/path",
    data_dir="/custom/data/path"
)

# Streaming vs local for Multiz100way
multiz = loader.load_multiz100way_dataset(
    msa_version="89",
    streaming=True  # or False
)
```

---

## 📈 5. Performance Characteristics

### 5.1 Loading Times

| Operation | First Time | Cached | Notes |
|-----------|------------|--------|-------|
| Load Brassicales model | ~30s | ~5s | Network dependent |
| Load MSA-Sapiens model | ~40s | ~6s | Larger model |
| Load Brassicales dataset | ~5min | ~10s | 1.6GB download |
| Load MSA-Sapiens dataset | ~6min | ~12s | 1.6GB download |
| Query Multiz100way (stream) | ~2-10s | ~2-10s | Per query |
| Query Multiz100way (local) | N/A | ~0.01s | After download |
| Load GENCODE files | Instant | Instant | Direct file access |
| Parse GENCODE GTF (pandas) | ~10-30s | ~10-30s | File size dependent |

### 5.2 Memory Usage

| Component | Memory |
|-----------|--------|
| GPN-Brassicales model | ~500 MB |
| GPN-MSA-Sapiens model | ~650 MB |
| Dataset iterator | ~100 MB |
| Multiz100way (streaming) | ~100 MB |
| Multiz100way (local) | ~1-2 GB |
| GENCODE GTF (parsed) | ~1-3 GB |
| GENCODE FASTA (loaded) | ~250 MB |

### 5.3 Optimization Strategies

#### 1. Lazy Loading
```python
# Models only loaded when requested
loader = GenomeLoader()  # Instant
model = loader.load_model("gpn-brassicales")  # Loads now
```

#### 2. Memory Cache
```python
# Second access is instant
model1 = loader.load_gpn_brassicales_model()  # Loads from disk
model2 = loader.load_gpn_brassicales_model()  # Returns cached
```

#### 3. Streaming for Large Data
```python
# Avoid downloading 50GB
multiz = loader.load_multiz100way_dataset(streaming=True)
```

#### 4. Dataset Iteration
```python
# Efficient iteration without loading all to memory
for sample in dataset['train']:
    process(sample)  # Memory-mapped access
```

#### 5. Partial GENCODE Loading
```python
# Only parse what you need for your training stage
import pandas as pd

# Testing: Just use chromosome 1 sequence
chr1_seq = SeqIO.read(gencode['chromosome_1'], "fasta")

# Retraining: Load complete annotations
df_full = pd.read_csv(gencode['annotation'], sep='\t', comment='#')

# Fine-tuning: Only load lncRNA subset
df_lncrna = pd.read_csv(gencode['lncrna'], sep='\t', comment='#')
```

#### 6. Stage-Based Loading
```python
# Load only what you need for current stage
def load_for_stage(loader, stage):
    """Load data based on training stage"""
    if stage == "test":
        # Only need chr1 for testing
        gencode = loader.load_dark_matter_data()
        return {'chr1': gencode['chromosome_1']}
    
    elif stage == "retrain":
        # Need full annotations
        gencode = loader.load_dark_matter_data()
        return {'annotation': gencode['annotation']}
    
    elif stage == "finetune":
        # Need lncRNA subset only
        gencode = loader.load_dark_matter_data()
        return {'lncrna': gencode['lncrna']}
    
    else:
        # Load everything
        return loader.load_dark_matter_data()
```

---

## 🎯 6. Best Practices

### 6.1 For Development

```python
# Use cached data for fast iteration
loader = GenomeLoader()  # Uses default cache
dataset = loader.load_brassicales_dataset()  # From cache

# Stream large datasets
multiz = loader.load_multiz100way_dataset(streaming=True)

# Only load GENCODE if needed
if need_annotations:
    gencode = loader.load_dark_matter_data()
```

### 6.2 For Production

```python
# Pre-download for reliability
multiz = loader.load_multiz100way_dataset(streaming=False)

# Verify cache before training
info = loader.get_info()
assert 'gpn-brassicales' in info['loaded_models']

# Check GENCODE availability
if not info['dark_matter_available']:
    print("Warning: GENCODE files not found")
    print("Please download manually for retraining/fine-tuning")
```

### 6.3 For HPC (Katana)

```python
# Use scratch storage for cache
loader = GenomeLoader(
    cache_dir="/srv/scratch/$USER/cache",
    data_dir="/srv/scratch/$USER/data"
)

# Pre-load everything in job script
loader, gpn, msa, gencode, brass = load_all_models_and_datasets()
```


---

## 📝 7. Summary

### Key Takeaways

1. **Four Dataset Types:**
   - **Brassicales:** Plant genomes (auto-download)
   - **MSA-Sapiens:** Human/vertebrate MSA (auto-download)
   - **Multiz100way:** Large-scale alignment (streaming/local)
   - **GENCODE:** Human annotations (manual download, stage-specific)

2. **Three Loading Modes:**
   - **Standard:** Full download + cache (Brassicales, MSA-Sapiens)
   - **Streaming:** On-demand access (Multiz100way)
   - **Manual:** Direct file access (GENCODE)

3. **GENCODE Training Stages:**
   - **Testing:** Use `chromosome.1.fa` for pipeline validation
   - **Retraining:** Use `basic.annotation.gtf` for full GPN training
   - **Fine-tuning:** Use `long_noncoding_RNAs.gtf` for lncRNA specialization

4. **Three-Level Cache:**
   - **Memory** (runtime): In-memory model cache
   - **Disk** (persistent): HuggingFace cache
   - **Remote** (fallback): Download from source

5. **Unified Interface:**
   - Single class for all datasets
   - Consistent API
   - Automatic management
   - Stage-aware loading

6. **Flexible Configuration:**
   - Custom cache paths
   - Streaming vs local
   - Memory vs speed tradeoffs
   - Stage-specific data loading

### Usage Decision Tree

```
What type of research?
├─ Plant genomics → Brassicales
├─ Human/vertebrate genomics → MSA-Sapiens
├─ Cross-species conservation → Multiz100way
└─ Non-coding RNA / annotations → GENCODE

What training stage?
├─ Testing pipeline → GENCODE chromosome.1.fa
├─ Full retraining → GENCODE basic.annotation.gtf
└─ Fine-tuning lncRNA → GENCODE long_noncoding_RNAs.gtf

Need frequent random access?
├─ Yes → Use standard loading (Brassicales/MSA-Sapiens)
└─ No → Use streaming (Multiz100way)

Have disk space (50GB+)?
├─ Yes → Download Multiz100way locally
└─ No → Use streaming mode

Need fast iteration?
├─ Yes → Pre-load to cache
└─ No → Load on-demand

Need human genome annotations?
├─ Yes → Download GENCODE manually
│   ├─ All 3 files → Full capability
│   ├─ Chr1 + basic → Testing + retraining
│   └─ lncRNA only → Fine-tuning only
└─ No → Skip GENCODE
```

### GENCODE File Relationship Summary

```
Training Pipeline:
    │
    ├─ Stage 1: Testing (Fast validation)
    │   └─ File: Homo_sapiens.GRCh38.dna.chromosome.1.fa
    │       └─ Size: 241 MB
    │       └─ Purpose: Verify training code works
    │
    ├─ Stage 2: Retraining (Full model)
    │   └─ File: gencode.v38.basic.annotation.gtf
    │       └─ Size: 857 MB
    │       └─ Purpose: Train on all gene types
    │       └─ Contains: 60,000 genes (all types)
    │
    └─ Stage 3: Fine-tuning (Specialized)
        └─ File: gencode.v38.long_noncoding_RNAs.gtf
            └─ Size: 86 MB
            └─ Purpose: Specialize for lncRNA
            └─ Contains: 20,000 lncRNA genes
            └─ Relationship: Subset of basic.annotation
```

---

## 📚 Additional Resources

### Official Documentation
- **HuggingFace Datasets:** https://huggingface.co/docs/datasets
- **GENCODE Database:** https://www.gencodegenes.org
- **Ensembl Genome Browser:** https://www.ensembl.org
- **UCSC Genome Browser:** https://genome.ucsc.edu
- **Zarr Format:** https://zarr.readthedocs.io

### Song Lab Resources
- **GPN GitHub:** https://github.com/songlab-cal/gpn
- **GPN Models:** https://huggingface.co/songlab
- **Research Paper:** Nature Plants (2023)


