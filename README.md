[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=20545616&assignment_repo_type=AssignmentRepo)

# 🚀 Capstone Project ID 3 — Deep Mining the Genome’s Dark Matter  
### (9900-F09C-DONUT Team)

---

## 🧭 1. Integrated Training Command on Katana  
> 💡 **Recommended way to train models** — one command to pull code, configure models, and submit PBS jobs automatically.  

### ▶️ Run the Integrated Launcher

Login to Katana, go to your project directory:
```bash
ssh zID@katana.restech.unsw.edu.au
mkdir /srv/scratch/$USER/capstone-project-25t3-9900-f09c-donut
git clone git@github.com:unsw-cse-comp99-3900/capstone-project-25t3-9900-f09c-donut.git
```

Then simply run:
```bash
chmod +x ./train_launcher.sh
./train_launcher.sh --branch <branch> --model <m1> <m2> ... --data-loader
```

### Example Commands
| Command	| Description |
| ----------- | ----------- |
| `./train_launcher.sh`	| 🚀 Run all models and the data-loader module using local code (default mode). |
| `./train_launcher.sh --model gpn` |	Train only the GPN model. |
| `./train_launcher.sh --model gpn gpn-msa` | Train both GPN and GPN-MSA models explicitly. |
| `./train_launcher.sh --model` |	Shortcut: Run both models (GPN + GPN-MSA), exclude data-loader. |
|`./train_launcher.sh --data-loader`	| Run only the data-loader module. |
|`./train_launcher.sh --data-preprocess`	| Run only the data-preproccess module. |
| `./train_launcher.sh --model gpn --data-loader` |	Run GPN model and data-loader together. |
| `./train_launcher.sh --branch dev --model gpn-msa` |	Pull branch `dev` and train only GPN-MSA model. |
| `./train_launcher.sh --branch main --model both` |	Pull branch `main` and train both models (equivalent to `--model gpn gpn-msa`). |
| `./train_launcher.sh --branch local` |	Run all configs (models + data-loader) using local code, without Git pull. |

### Parameters
| Parameter	| Description | Default |
| ----------- | ----------- | ---------- |
|`--branch <branch>`|	Git branch to pull before execution. Use `local` to skip Git operations and run local code.|	`local`|
|`--model <names...>`	|One or more model names to train (`gpn`, `gpn-msa`). Use multiple values (space-separated) or `both` to include all models. If used without arguments, defaults to both models.	|`both`|
|`--data-loader`|	Include or run only the data-loader pipeline module. Can be combined with `--model`.|	`false` (auto-enabled when no args provided)|
|`--data-preprocess`|	Include or run only the data-preprocess pipeline module. Can be combined with `--model`.|	`false` (auto-enabled when no args provided)|

### What Happens Internally

1️⃣ Git Management

Pulls the specified branch from remote (`git fetch`, `git checkout`, `git pull`)

Skips pulling if you pass `local`

2️⃣ Run Target Selection

The launcher determines what to run — this can include one or more models and optional auxiliary modules
(such as the `data-loader, data-preprocess`) depending on the command-line arguments.

If no arguments are provided, all available run targets are executed by default
(including both models and the data-loader module).

If `--model` is specified, only those listed models are selected (`gpn`, `gpn-msa`, or both).

If `--data-loader` is specified, the data-loading pipeline is added to the run sequence or executed alone.

If `--data-preprocess` is specified, the data-preprocessing pipeline is added to the run sequence or executed alone.

Each selected target automatically generates its own container configuration file in the `configs/` directory:

Automatically generated configuration files:
```bash
configs/container_run_gpn.txt
configs/container_run_gpn-msa.txt
configs/container_run_data-loader.txt
configs/container_run_data-preprocess.txt
```
These configuration files act as execution manifests, defining which Python entry point the container should run.

They are not regenerated automatically — instead, the launcher dynamically detects and uses the ones already present.

3️⃣ Container Configuration

The launcher scans the `configs/` directory to collect all matching configuration files
(based on the selected run targets from Step 2).

For each detected configuration file:

The script reads its content to determine the corresponding Python entry script (e.g., inside src/).

A dedicated PBS job is created and submitted for that entry.

Example mapping between config and execution file:
```bash
src/gpn_test.py
src/gpn-msa_test.py
```
Each configuration file is passed to `Katana` as the environment variable `RUNCONF`,
ensuring the Apptainer container knows which Python script to execute.

This design allows you to easily control which jobs are launched —
simply add or remove configuration files under `configs/`, and the launcher will automatically detect them.

4️⃣ PBS Job Submission

- Each model job is submitted to Katana with a unique name:
```
train-gpn-153012
train-gpn-msa-153013
```

- The command used internally:
```
qsub -N "$JOB_NAME" -o "logs/training_logs/" -v MODEL_NAME="$M",RUNCONF="$CONFIG_FILE" "$PBS_SCRIPT"
```

### Log Review Tips
|Log Type	|Path	|Purpose|
| ----------- | ----------- | ---------- |
|Launcher Log |	```logs/launcher_logs/launcher_<timestamp>.log``` |	Tracks all submission activity|
|PBS Output Log |```logs/training_logs/train-<model>.o<JOBID>```|	Contains container stdout/stderr|
|Config File|	```configs/container_run.txt```|	Shows which Python file is executed in container|



## 🧭 2. Getting Started Directly on UNSW Katana HPC

This guide explains how to:

- Log in to UNSW Katana HPC  
- Clone the project repository  
- Run the demo via command line (model import included)  
- Understand the key configuration files (PBS job script, container, dependencies)

---

### 🧭 1. SSH into Katana

To work on Katana, open your terminal or VS Code and connect via SSH:

```bash
ssh zID@katana.restech.unsw.edu.au
```

> 🔸 Replace `zID` with your UNSW student ID (e.g., `z1234567`).  
> After pressing **Enter**, input your UNSW password. You’ll then be on Katana’s login node.

---

### 📥 2. Clone the Repository on Katana

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

### 🐳 3. Run the Demo on Katana

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

### ⚙️ 4. Key Configuration Files Explained

#### `run.pbs` — HPC Job Script

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

#### `container/p3.def` — Container Definition

Defines how the container is built. It typically includes:

- Base OS or PyTorch image  
- Installation of Python libraries  
- Copying project files inside

Once built, it becomes `p3.sif`, which is executed by the PBS script.

---

#### `configs/container_run.txt` — Container Runtime Settings

Optional settings for container execution, e.g.:

- Working directory inside the container  
- Data/model paths  
- Command-line flags

---

#### `requirements.txt` — Python Dependencies

Specifies Python libraries installed inside the container. For example:

```
torch==2.0.1
numpy
pandas
scikit-learn
```

---

### 🧪 5. Verify Model Import

Check the log file — it should contain:

```
Loading model...
✓ Model loaded.
Model class: ConvNetForMaskedLM
```

This confirms the container and dependencies are correctly set up.


## ✅ Summary

This project now supports both **manual job submission** and a **one-command automated training launcher** on UNSW Katana HPC.

- ✅ Use the integrated launcher script to automatically → `./train_launcher.sh [--branch <branch_name|local>] [--model <gpn|gpn-msa|both>]`
- ✅ SSH into Katana → `ssh zID@katana.restech.unsw.edu.au`  
- ✅ Clone the repo → `git clone ...`  
- ✅ Navigate into project folder  
- ✅ Submit the job → `qsub run.pbs`  
- ✅ Check logs for model import success
