[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=20545616&assignment_repo_type=AssignmentRepo)

# 🚀 Getting Started on UNSW Katana HPC

This guide explains how to:

- Log in to UNSW Katana HPC  
- Clone the project repository  
- Run the demo via command line (model import included)  
- Understand the key configuration files (PBS job script, container, dependencies)

---

## 🧭 1. SSH into Katana

To work on Katana, open your terminal or VS Code and connect via SSH:

```bash
ssh zID@katana.restech.unsw.edu.au
```

> 🔸 Replace `zID` with your UNSW student ID (e.g., `z1234567`).  
> After pressing **Enter**, input your UNSW password. You’ll then be on Katana’s login node.

---

## 📥 2. Clone the Repository on Katana

Once you’re logged into Katana, clone the project directly into your home directory:

```bash
git clone git@github.com:unsw-cse-comp99-3900/capstone-project-25t3-9900-f09c-donut.git
cd capstone-project-25t3-9900-f09c-donut
```

> 💡 Make sure your GitHub account has SSH keys configured. If not, follow [GitHub’s SSH key setup guide](https://docs.github.com/en/authentication/connecting-to-github-with-ssh).

Check the files:

```bash
ls
```

Expected structure:

```
capstone-project-25t3-9900-f09c-donut/
├── configs/
│   └── container_run.txt
├── container/
│   └── p3.def
├── data/
│   ├── loader.py
│   └── preprocess.py
├── README.md
├── requirements.txt
├── run.pbs
└── src/
    └── gpn_test.py
```

---

## 🐳 3. Run the Demo on Katana

Submit the job:

```bash
qsub run.pbs
```

Check job status:

```bash
qstat
```

When it finishes, you’ll see logs like `run.pbs.oXXXXXXX` in the same directory.

---

## ⚙️ 4. Key Configuration Files Explained

### `run.pbs` — HPC Job Script

Controls how the job runs on Katana:

```bash
#PBS -l select=1:ncpus=4:mem=32gb
#PBS -l walltime=02:00:00
#PBS -j oe
#PBS -N capstone-container-run

set -euo pipefail
cd "$PBS_O_WORKDIR"

apptainer run container/p3.sif python3 src/gpn_test.py
```

- `select=1:ncpus=4:mem=32gb` → 1 node, 4 CPUs, 32 GB RAM  
- `walltime=02:00:00` → 2 hours max run time  
- `cd "$PBS_O_WORKDIR"` → Runs from the submission folder  
- `apptainer run ...` → Executes the model inside the container

---

### `container/p3.def` — Container Definition

Defines how the container is built. It typically includes:

- Base OS or PyTorch image  
- Installation of Python libraries  
- Copying project files inside

Once built, it becomes `p3.sif`, which is executed by the PBS script.

---

### `configs/container_run.txt` — Container Runtime Settings

Optional settings for container execution, e.g.:

- Working directory inside the container  
- Data/model paths  
- Command-line flags

---

### `requirements.txt` — Python Dependencies

Specifies Python libraries installed inside the container. For example:

```
torch==2.0.1
numpy
pandas
scikit-learn
```

---

## 🧪 5. Verify Model Import

Check the log file — it should contain:

```
Loading model...
✓ Model loaded.
Model class: ConvNetForMaskedLM
```

This confirms the container and dependencies are correctly set up.

---

## ✅ Summary

- ✅ SSH into Katana → `ssh zID@katana.restech.unsw.edu.au`  
- ✅ Clone the repo → `git clone ...`  
- ✅ Navigate into project folder  
- ✅ Submit the job → `qsub run.pbs`  
- ✅ Check logs for model import success
