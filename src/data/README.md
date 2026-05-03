# Data

The raw data files are **not tracked in git** — they're too large. Download them manually and place them in this folder before running any notebooks.

## Downloading the GTEx dataset

1. Go to the [GTEx Portal downloads page](https://gtexportal.org/home/downloads/adult-gtex/bulk_tissue_expression)
2. Under **GTEx Analysis V10 → RNA-Seq**, download:

   > `GTEx_Analysis_2022-06-06_v10_RNASeQCv2.4.2_gene_tpm_non_lcm.gct`

3. Place the file directly in this folder (`src/data/`). The path is already configured in `GlobalVariables.py`.

## Dataset info — GTEx Analysis V10

| Field | Detail |
|-------|--------|
| **Full name** | Genotype-Tissue Expression (GTEx) Project, Analysis V10 |
| **File** | `GTEx_Analysis_2022-06-06_v10_RNASeQCv2.4.2_gene_tpm_non_lcm.gct` |
| **Size** | ~6.8 GB (uncompressed) |
| **Format** | GCT 1.2 — tab-separated, 2 metadata rows before the actual header |
| **Quantification tool** | RNASeQC v2.4.2 |
| **Normalization** | TPM (Transcripts Per Million) |
| **Samples** | 19,614 non-LCM bulk tissue samples |
| **Genes** | 59,033 (GENCODE v39 annotation) |
| **Tissues** | 54 tissue types from ~1,000 human donors |
| **Access** | Open — no login or IRB required |
| **Portal** | https://gtexportal.org |
| **Reference genome** | GRCh38/hg38 |

The `_non_lcm` suffix means this file excludes Laser Capture Microdissection (LCM) samples, which are kept in a separate file (`gene_tpm_lcm.gct.gz`). For bulk tissue analysis, non-LCM is the right one.

## README_GTEx.txt

The file `README_GTEx.txt` in this folder comes directly from the GTEx Portal and describes the small RNA-seq processing pipeline used in V10. It covers read filtering, UMI removal, alignment to personalized transcriptomes, and contamination correction. Keep it here as reference — do not edit it.
