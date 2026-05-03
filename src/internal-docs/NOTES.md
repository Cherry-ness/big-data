# Project Notes & Initial Ideas

## Dataset Candidates

### Option A — Human Genome (GRCh38 / hg38)
- Reference size: ~3.1 Gb
- Well-characterized, massive public variant databases: gnomAD, dbSNP, ClinVar
- GTEx v10 TPM matrix (`GTEx_Analysis_v10_RNASeQCv2.4.2_gene_tpm_non_lcm.gct`) — gene expression across 54 human tissues, ~2.1 GB compressed
- GTEx v10 is the most complete analyzed Adult GTEx release
- Available via [GTEx Portal](https://gtexportal.org/home/downloads/adult-gtex/bulk_tissue_expression) and [NCBI](https://www.ncbi.nlm.nih.gov/)

### Option B — Axolotl (*Ambystoma mexicanum*, AmexG.v6)
- Reference size: ~32 Gb — roughly **10× the human genome**
- One of the largest vertebrate genomes sequenced to date, due to massive repetitive content
- Sparse annotation compared to human — harder and more interesting from a computational standpoint
- Makes an even stronger argument for distributed computing (single-node tools simply won't cut it)
- Available via [Ensembl](https://www.ensembl.org/) and NCBI
- Key paper: Nowoshilow et al., *Nature* 2018 — first assembly of the axolotl genome

## Why Distributed Computing?

Whole-genome sequencing (WGS) datasets are among the largest routinely produced in biology:
- A single human WGS sample: 100–200 GB of raw reads
- Population-scale cohorts (e.g., UK Biobank, gnomAD): petabyte range
- The axolotl reference alone is 32 Gb — before any read data

Classical single-node bioinformatics tools (samtools, GATK on a laptop) hit memory and I/O walls fast. Apache Spark distributes the data across nodes (or cores locally) and processes it in parallel — the natural fit for this scale.

## Analysis Ideas

- Cross-tissue gene expression clustering (GTEx TPM matrix → PySpark + k-means or hierarchical)
- Differential expression between tissue types at scale
- Identify highly variable genes across tissues
- Correlate expression profiles with metadata (age, sex, tissue type)
- If axolotl: comparative analysis of conserved vs. diverged expression patterns vs. human orthologs

## GTEx Preliminary Analysis — Ideas Moved from Notebook

### Expression Thresholding
- `mean TPM > 1.0` splits the bimodal distribution cleanly: ~40% of genes are expressed above threshold, ~60% are low/zero
- This threshold is standard in the GTEx pipeline docs — worth citing when we actually apply it in a later stage
- Before any downstream analysis (clustering, differential expression), filter to expressed genes only — otherwise the noise genes swamp the signal

### Top Expressed Genes Interpretation
- Top 20 genes are heavily weighted toward structural/metabolic proteins: hemoglobin (HBB, HBA1) from blood, albumin (ALB) from liver, actin from muscle
- This is expected and validates data quality — these are known high-expression genes in their respective tissues
- The skew is extreme: ALB TPM in liver samples is orders of magnitude above the mean, which is why log1p transform is necessary before visualization and clustering

### Space Medicine Angle (future work — need citations before using)
- Hypothesis: GTEx normal tissue expression = Earth baseline → deviations in astronaut samples indicate spaceflight effect
- Relevant papers to dig into:
  - Beheshti, A. et al. (2024). Aging and putative frailty biomarkers are altered by spaceflight. *Nature Scientific Reports*. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11166946/
  - Ruiz-Fernández de Córdoba, B. et al. (2025). Microgravity impact on gene expression and drug repurposing. *PubMed Central*. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11818396/
- Do NOT include this framing in the notebook until we can actually argue it from the data and have read these papers

### Preprocessing Pending (#3–#6)
- **Outlier TPM**: Need tissue labels first (from `GTEx_v10_sample_attributes.txt`) to do per-tissue IQR analysis — global IQR is meaningless when tissues are mixed
- **Sample imbalance**: Some tissues have 5 donors, some have 200+ — matters a lot for any comparative analysis
- **Structural zeros**: ~40-50% zeros per sample column. Genes with >90% zeros across all tissues are likely not expressed anywhere — safe to filter. But a gene with 0 in blood and high TPM in liver is informative, not missing
- **Sample IDs**: Need to download `GTEx_v10_sample_attributes.txt` from the portal to map sample IDs to tissue types

## References

- GATK Best Practices — <https://gatk.broadinstitute.org/hc/en-us/sections/360007226651>
- Hail: Scalable genomic data analysis on Spark — <https://hail.is/>
- SparkBWA: Speeding Up the Alignment of High-Throughput DNA Sequencing Data
- Nowoshilow et al. (2018), "The axolotl genome and the evolution of key tissue formation regulators", *Nature* 554, 50–55
- GTEx Consortium (2023), GTEx Analysis V10
