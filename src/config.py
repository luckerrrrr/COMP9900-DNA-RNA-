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

CHROM = "1"
GTF = "dataset/gencode.v38.basic.annotation.gtf"
FASTA = "dataset/Homo_sapiens.GRCh38.dna.chromosome.1.fa"
PHASTCONS_FILE = "dataset/chr1.phastCons100way.wigFix"

CONFIG = {
    "model": {
        "name": "songlab/gpn-msa-sapiens",
        "hidden_dropout": 0.1,
    },
    "data": {
        "window_len": 512,
        "flanking": 100,
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
