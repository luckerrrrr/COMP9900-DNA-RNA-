# config.py
import os
from pathlib import Path
import datetime

# Generate timestamp string formatted as "HH-MM-SS"
timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

# Project and environment configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
USER = os.environ.get('USER', 'unknown')
MIDDLE_RESULT_DIR = Path(f"/srv/scratch/{USER}/middle_results")
MIDDLE_RESULT_DIR_OUT = Path(f"/srv/scratch/{USER}/middle_results/{timestamp}")

CHROM = "ALL"
# GTF_GENCODE = "dataset/gencode.v38.basic.annotation.gtf"
# GTF_FINE_TUNE_SET1 = "dataset/FineTuningSet1.txt"
GTF_FINE_TUNE_SET2 = "dataset/FineTuningSet2.txt"
GTF_LNCRNA = "dataset/gencode.v38.long_noncoding_RNAs.gtf"
GTF = GTF_FINE_TUNE_SET2
# FASTA = "dataset/Homo_sapiens.GRCh38.dna.chromosome.1.fa"
FASTA = f"dataset/GRCh38.primary_assembly.genome.fa"
PHASTCONS_FILE = "dataset/chr1.phastCons100way.wigFix"

MSA_BEST_MODEL = "model_results/best_models/gpn_msa/best_{SET_NAME}.pt"

CONFIG = {
    "model": {
        "name": "songlab/gpn-msa-sapiens",
        "hidden_dropout": 0.1,
    },
    "data": {
        "window_len": 512,
        "flanking": 0,
        "step": 256,
        "stride": 64,
        "pad_token_id": 0,
    },
    "train": {
        "batch_size": 4,
        "epochs": 8,
        "lr_backbone": 2e-5,
        "lr_head": 1e-4,
        "weight_decay": 1e-6,
        "warmup_steps": 200,
    }
}
