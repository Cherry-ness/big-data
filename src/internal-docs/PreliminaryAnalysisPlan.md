Architected comprehensive markdown briefing for code execution
Architected comprehensive markdown briefing for code execution
Here's the briefing file! Here's how to use it with Claude Code:

Option 1 — Paste it directly: Open Claude Code in your terminal, then just paste the entire contents of that .md file as your first message, followed by: "Please complete this assignment and produce the final PDF."

Option 2 — Reference the file: If you're in the same directory as the file, you can tell Claude Code:

read CLAUDE_CODE_BRIEF.md and then complete the assignment described in it, producing a final PDF
What's inside the brief:

All the dataset details and how to load it in PySpark
The research framing and objective (in Spanish and English)
Ready-to-run PySpark code snippets for each analysis step
The exact preprocessing issues to document (conceptual only — no fixes needed)
Cover page fields to fill in
The grading rubric so it knows what to prioritize
The AI declaration it needs to include
The one thing Claude Code can't do for you is download the actual dataset — you'll need to grab GTEx_Analysis_v10_RNASeQCv2.4.2_gene_tpm.gct.gz from gtexportal.org first, then point Claude Code at the file path. Everything else it should be able to handle end to end! 🚀




🧬 PySpark Big Data Project — Claude Code Briefing
## TC5057 · Tecnológico de Monterrey · Trimestre Abr–Jul 2026
 
---
 
## 🎯 What You Need To Produce
 
A **PDF report (max 3 pages / "cuartillas")** for a Big Data course assignment.  
The PDF must contain:
 
1. **Carátula (Cover page)**
2. **Descripción del tema de interés + Objetivo general**
3. **Selección del dataset** (name, origin, link, size in GB)
4. **Análisis del dataset** — descriptive statistics with graphs, plus preprocessing documentation
> ⚠️ The grader explicitly checks for: graphs showing descriptive stats, identification of nulls/outliers/noise, and a clear researchable objective. See grading rubric at the bottom of this file.
 
---
 
## 📦 The Dataset
 
**Name:** GTEx Analysis V10 — Gene Expression TPM  
**Origin:** NIH / Broad Institute — Genotype-Tissue Expression Project  
**Download link:** https://gtexportal.org/home/downloads/adult-gtex  
**File to download:** `GTEx_Analysis_v10_RNASeQCv2.4.2_gene_tpm.gct.gz`  
**Size:** 2.1 GB (compressed) — well above the 1 GB minimum requirement  
**Format:** GCT (tab-separated, basically a TSV with 2 metadata header rows to skip)  
**Access:** Fully open, no login or IRB required
 
### What the data contains:
- **Rows:** ~56,000 genes (ENSEMBL IDs, e.g. `ENSG00000000003.15`)
- **Columns:** ~17,000 tissue samples from ~1,000 human donors
- **Values:** TPM (Transcripts Per Million) — normalized gene expression level per sample
- **Tissues covered:** 54 tissue types including 13 brain subregions, heart, liver, muscle, blood, lung, skin, etc.
### How to load in PySpark:
```python
from pyspark.sql import SparkSession
 
spark = SparkSession.builder.appName("GTEx_Analysis").getOrCreate()
 
# GCT format has 2 metadata rows — skip them
df = spark.read \
    .option("sep", "\t") \
    .option("header", "true") \
    .option("comment", "#") \
    .csv("GTEx_Analysis_v10_RNASeQCv2.4.2_gene_tpm.gct.gz")
 
# Drop the 'Description' column (gene name, redundant for stats)
# First two columns are: 'Name' (ENSEMBL ID), 'Description' (gene name)
# All remaining columns are sample IDs with TPM values
```
 
> **Note:** If the full 2.1GB file is too slow to work with locally, you can also download individual tissue files (e.g. `gene_tpm_v11_brain_amygdala.gct.gz` at ~25 MB each) from the same page and combine several of them. This is a valid approach for the analysis.
 
---
 
## 📝 Research Framing (use this for the PDF text)
 
### Theme / Topic:
**Human Gene Expression as a Baseline for Astronaut Health Monitoring**
 
### Context paragraph (use/adapt this):
With NASA's Artemis II mission currently underway, sending humans back toward the Moon for the first time in decades, space medicine researchers are actively studying how spaceflight alters the human body at a molecular level. Microgravity, cosmic radiation, and mission stress are known to alter **gene expression** — how actively genes are "working" — even without changing the underlying DNA. To detect these deviations, scientists need a healthy Earth-based baseline. The GTEx dataset provides exactly that: a comprehensive map of normal human gene expression across 54 tissue types from nearly 1,000 donors, funded by the NIH Common Fund and maintained by the Broad Institute of MIT and Harvard.
 
### Objetivo general (use this verbatim or adapt):
> *"Analizar los patrones de expresión génica en 54 tipos de tejido humano para identificar marcadores biológicos relevantes para el monitoreo de la salud de astronautas, estableciendo una línea base genómica terrestre que la medicina espacial utiliza para detectar desviaciones causadas por el vuelo espacial."*
 
English version:
> *"Analyze tissue-wide human gene expression patterns across 54 tissue types to identify biological markers relevant to astronaut health monitoring — establishing Earth-normal genomic baselines that space medicine uses to detect deviations caused by spaceflight."*
 
---
 
## 📊 Analysis You Need to Run in PySpark
 
Run the following and generate graphs from the results. You can use `matplotlib` or `seaborn` after converting Spark DFs to pandas for plotting.
 
### 1. Basic structure stats
```python
# Number of rows and columns
print(f"Rows: {df.count()}, Columns: {len(df.columns)}")
 
# Data types
df.printSchema()
```
 
### 2. Descriptive statistics
```python
# Cast TPM columns to float first, then run describe
# Focus on a subset of columns if the full dataset is too wide
df.describe().show()
```
 
### 3. Missing values per column
```python
from pyspark.sql.functions import col, isnan, when, count
 
# Count nulls per column
df.select([
    count(when(col(c).isNull() | isnan(c), c)).alias(c)
    for c in df.columns[:20]  # sample first 20 columns
]).show()
```
 
### 4. Distribution of expression values (for PDF graph)
```python
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
 
# Pick one tissue column as example
sample_col = df.columns[2]  # first sample column
vals = df.select(sample_col).dropna().toPandas()
vals[sample_col] = pd.to_numeric(vals[sample_col], errors='coerce')
 
plt.figure(figsize=(8,4))
plt.hist(np.log1p(vals[sample_col].dropna()), bins=80, color='#e8003a', alpha=0.8)
plt.xlabel('log1p(TPM)')
plt.ylabel('Gene count')
plt.title('Distribution of Gene Expression (log-TPM)')
plt.tight_layout()
plt.savefig('expression_distribution.png', dpi=150)
```
 
### 5. Top expressed genes across all samples (for PDF graph)
```python
# Mean TPM across samples for each gene
# You'll need to melt or pivot — easier to do in pandas on a sample
```
 
### 6. Tissue-level comparison (optional but impressive)
If using per-tissue files: compare mean expression across tissues as a bar chart.
 
---
 
## ⚠️ Preprocessing Issues to Document (Conceptual Only — No Fix Required)
 
The assignment says you only need to **identify and describe** these, not fix them yet:
 
| Issue | Description | Proposed correction |
|-------|-------------|---------------------|
| **Metadata header rows** | GCT format has 2 non-data rows at the top | Skip with `option("comment","#")` or manually drop first 2 rows |
| **ENSEMBL gene IDs** | Gene names are codes like `ENSG00000000003.15`, not human-readable | Map to gene symbols using a reference table (e.g. GENCODE GTF) |
| **Extreme outlier TPM values** | Some genes have astronomically high TPM in specific tissues (e.g. albumin in liver) | Log-transform data (`log1p`) before analysis; apply IQR-based outlier detection |
| **Unbalanced tissue samples** | Not all 54 tissues have the same number of donors | Document sample counts per tissue; consider stratified sampling for comparative analyses |
| **Implicit zeros vs. true zeros** | Zero TPM may mean truly unexpressed OR below detection threshold | Flag zero-dominant genes; consider filtering genes with >90% zeros |
| **No missing values (sparse zeros)** | GTEx has almost no NULLs, but has many zeros — which behave like structural missing data for expression analysis | Distinguish true zeros from noise using expression thresholding |
 
---
 
## 📄 PDF Cover Page Info
 
| Field | Value |
|-------|-------|
| **Título** | Análisis de Expresión Génica Humana como Línea Base para el Monitoreo de Salud en Astronautas |
| **Asignatura** | TC5057 — Análisis de Grandes Volúmenes de Datos |
| **Institución** | Tecnológico de Monterrey |
| **Fecha** | Mayo 2026 |
| **Entregable** | archivos de Big Data PySpark_Equipo# |
 
> Fill in: student names, professor name, and team number.
 
---
 
## 📚 Key References (include in PDF)
 
1. GTEx Consortium. (2020). The GTEx Consortium atlas of genetic regulatory effects across human tissues. *Science*. https://doi.org/10.1126/science.aaz1776
2. Afshin Beheshti et al. (2024). Aging and putative frailty biomarkers are altered by spaceflight. *Nature Scientific Reports*. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11166946/
3. Ruiz-Fernández de Córdoba et al. (2025). Microgravity impact on gene expression and drug repurposing. *PubMed Central*. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11818396/
4. GTEx Portal. (2025). GTEx Analysis V10 Downloads. Broad Institute. https://gtexportal.org/home/downloads/adult-gtex
---
 
## 🤖 AI Declaration (Required by the assignment)
 
Include this at the end of the PDF:
 
> **Declaración de uso de IA:**  
> Anthropic. (2026). *Claude Sonnet 4.5* [Modelo de lenguaje grande], utilizado para investigación de dataset, redacción de contexto y resumen del tema de investigación. https://claude.ai  
> La responsabilidad final sobre el contenido entregado recae en los autores del equipo.
 
---
 
## 📋 Grading Rubric (10 points total)
 
| Criterio | Destacado (full points) |
|----------|------------------------|
| **Carátula** (1pt) | All elements: title, student names, subject, professor, institution, date |
| **Tema + Objetivo** (3pts) | Topic clearly described and contextualized; objective is clear, precise, measurable, coherent |
| **Selección del dataset** (3pts) | Name, origin, link, size in GB (≥1GB), justification of choice relative to topic |
| **Análisis del dataset** (3pts) | Multiple appropriate graphs, correct interpretation, clearly documented dataset problems (noise, outliers, nulls) |
 
**Max length: 3 cuartillas (pages)**
 
---
 
## 💡 Tips for Claude Code
 
- Generate the graphs with `matplotlib`, save as PNG, then embed in the PDF
- Use `reportlab` or `weasyprint` to generate the PDF programmatically, or generate an HTML and convert
- Keep the PDF to 3 pages max — be concise, let the graphs do the talking
- The analysis section is worth the most points (3pts) — prioritize good graphs over long text
- You do NOT need to actually fix the preprocessing issues, just identify and describe them clearly