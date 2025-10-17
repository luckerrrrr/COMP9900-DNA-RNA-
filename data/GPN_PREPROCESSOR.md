# GPN Genome Preprocessor Documentation

## Overview

This Python script implements a genomic data preprocessing pipeline specifically designed for the GPN (Genome Pretraining Network) model published in PNAS 2023. The preprocessor extracts information from GENCODE annotation files and FASTA sequence files to generate standardized datasets for training deep learning models.

## Key Features

The preprocessor performs the following key tasks:

1. **Parses GENCODE GTF annotation files** to extract gene, transcript, and exon information
2. **Extracts specific genomic regions**:
   - Exons with flanking introns (default flanking length: 100bp)
   - Promoter regions (1000bp upstream of TSS)
   - Random genomic windows as controls
3. **Creates 512bp sliding windows** with a step size of 256bp (50% overlap)
4. **Applies data augmentation** by generating reverse complement sequences
5. **Sequence masking** by randomly masking 15% of nucleotide positions for training

## Classes and Methods

### `GENCODEPreprocessor` Class

Responsible for extracting and processing genomic regions from GENCODE files:

- **`parse_gtf()`**: Parses GTF file and extracts gene annotation information
- **`extract_exons_with_flanking()`**: Extracts exon regions with added flanking sequences
- **`extract_promoter_regions()`**: Extracts gene promoter regions (TSS upstream sequences)
- **`generate_random_genome_windows()`**: Generates random genome regions as controls
- **`create_gpn_windows()`**: Creates fixed-size sliding windows
- **`load_sequence_from_fasta()`**: Loads specific chromosome region sequences from FASTA files

### `GPNDataProcessor` Class

Processes DNA sequences for GPN model training:

- **`reverse_complement()`**: Generates reverse complement of DNA sequences
- **`tokenize_sequence()`**: Tokenizes sequences into single nucleotides (not k-mers)
- **`apply_data_augmentation()`**: Applies data augmentation (including reverse complement)
- **`mask_sequence()`**: Applies 15% masking rate for sequence masking

### `process_gpn_dataset()` Function

Main processing pipeline that executes in the following steps:

1. Initialize preprocessors
2. Parse GENCODE annotations
3. Extract three types of regions: exons, promoters, and random regions
4. Create 512bp windows
5. Process sequences: load, augment, tokenize, and mask

## Usage

The script can be run in two modes:

### Test Mode

```bash
python preprocess_gpn.py test
```

This runs a quick test with a small amount of data to verify the preprocessing pipeline is working correctly.

### Full Processing Mode

```bash
python preprocess_gpn.py full [exons_count] [promoters_count] [random_windows_count]
```

For example:
```bash
python preprocess_gpn.py full 1000 1000 1000
```

This will process 1000 exon regions, 1000 promoter regions, and 1000 random genomic windows.

## Input Files

1. **GTF File**: GENCODE genome annotation file (e.g., `gencode.v38.basic.annotation.gtf`)
2. **FASTA File**: Reference genome sequence file (e.g., `Homo_sapiens.GRCh38.dna.chromosome.1.fa`)

## Output Data

The processed data is saved in JSON format containing the following information:

- Window ID and chromosome location
- Region type (exon, promoter, or random)
- Gene ID and name (where applicable)
- Strand direction
- Original and masked sequences
- Token list
- Mask positions

## Technical Details

- **Window Size**: 512bp (GPN model requirement)
- **Step Size**: 256bp (50% overlap)
- **Flanking Regions**: 100bp around exons
- **Promoter Regions**: 1000bp upstream of TSS
- **Masking Rate**: 15%
- **Data Augmentation**: Includes original and reverse complement sequences

## Notes

1. Ensure input file paths are correct
2. Large FASTA files may require significant memory
3. The script is designed for processing human genome data (chromosome sizes are preset)
4. Default output is saved to `data/gpn_preprocessing_results.json`

## References

This preprocessing pipeline is designed based on the requirements of the GPN model published in PNAS 2023. The model is used for deep learning analysis and prediction of genomic sequences.
