# Environment setup

```bash
# 1. create the environment from the yml file (only needed once)
conda env create -f environment.yml

# 2. activate it
conda activate big-data

# 3. register it as a jupyter kernel (only needed once)
python -m ipykernel install --user --name big-data --display-name "Python (big-data)"

# 4. launch jupyter and select the "Python (big-data)" kernel in the notebook
jupyter lab
```

> If you already have the environment and just want to update it after a change to `environment.yml`:
> ```bash
> conda env update -f environment.yml --prune
> ```

---

# Getting the data

The GTEx dataset is not tracked in git (too large). Download it first and place it inside `src/data/`:

1. Go to the [GTEx Portal downloads page](https://gtexportal.org/home/downloads/adult-gtex/bulk_tissue_expression)
2. Under **GTEx Analysis V10 → RNA-Seq**, download:  
   `GTEx_Analysis_2022-06-06_v10_RNASeQCv2.4.2_gene_tpm_non_lcm.gct` (~6.8 GB uncompressed)
3. Move the file to `src/data/` — the path in `GlobalVariables.py` already points there

# Spark memory

The driver memory is set to `8g` in [`src/GlobalVariables.py`](src/GlobalVariables.py):

```python
SPARK_MEMORY = "8g"
```

If your machine has less than ~16 GB of RAM, lower this before running the notebook:

| Total RAM | Recommended `SPARK_MEMORY` |
|-----------|---------------------------|
| 32 GB+    | `"8g"` (default)          |
| 16 GB     | `"6g"`                    |
| 8 GB      | `"4g"`                    |

Spark needs the driver memory plus room for the OS and JVM overhead, so a rough rule is to set it to no more than half your total RAM.
