# Run the compare_multiz_gencode_hpc.py on Katana

This guide explains how to run the `compare_multiz_gencode_hpc.py` on the **Katana HPC cluster** to calculate the result of the coverage using a PBS submission script.

---

## Steps to Run

### Prepare the dataset
Due to GitHub upload limitations, one of our datasets cannot be included in this repository.  
To run `compare_multiz_gencode_hpc.py` on the HPC system, you first need to download the dataset `gencode.v38.long_noncoding_RNAs.gtf` from the following link:  

[Download gencode.v38.long_noncoding_RNAs.gtf](https://unsw-my.sharepoint.com/personal/z5234380_ad_unsw_edu_au/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fz5234380%5Fad%5Funsw%5Fedu%5Fau%2FDocuments%2FDark%20Matter%20of%20the%20Genome%20data&ga=1)

Place the downloaded file in the same directory as the script.

---

### Submit the job
To start the `compare_multiz_gencode_hpc.py`, use the following command:
```bash
qsub run.pbs
```

### Check job status
To check if the task has been completed，use the following command:
```bash
qstat
```
When it finishes, you’ll see logs like run.pbs.oXXXXXXX in the same directory.

### Check results
If you want to check the results，use the following command:
```bash
cat run.pbs.oXXXXXXX
```
This log will record the final result of the coverage calculated after running `compare_multiz_gencode_hpc.py`.
