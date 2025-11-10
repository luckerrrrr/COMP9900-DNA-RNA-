# lncRNA Validation Analysis

## Purpose
Validate whether GENCODE lncRNA information appears in GPN-MSA training data using UMAP visualization.

## Usage

### Basic usage
```bash
python3 lncrna_analysis.py
```

### With custom parameters
```bash
python3 lncrna_analysis.py --gencode path/to/gencode.gtf --sample-size 20000
```

## Output
- `gpn_msa_umap.png` - UMAP dimensionality reduction plot colored by gene types

## Requirements
- umap-learn
- matplotlib
- datasets
- transformers
