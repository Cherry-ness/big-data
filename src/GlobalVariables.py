import os

# always resolves relative to src/ no matter where the notebook is run from
SRC_DIR = os.path.dirname(os.path.abspath(__file__))

# paths
FILE_PATH          = os.path.join(SRC_DIR, "data", "GTEx_Analysis_2022-06-06_v10_RNASeQCv2.4.2_gene_tpm_non_lcm.gct")
SAMPLE_ATTRS_PATH  = os.path.join(SRC_DIR, "data", "GTEx_Analysis_v10_Annotations_SampleAttributesDS.txt")
SUBJECT_PHENO_PATH = os.path.join(SRC_DIR, "data", "GTEx_Analysis_v10_Annotations_SubjectPhenotypesDS.txt")
OUTPUT_DIR         = os.path.join(SRC_DIR, "preliminary-analysis")

# dataset constants
N_GENES   = 59033
N_SAMPLES = 19614

# analysis parameters
RANDOM_SEED = 42    # seed for anything random — keeps results comparable across runs
SAMPLE_STEP = 100   # take every Nth sample column to keep the dataframe manageable
THRESHOLD   = 1.0   # minimum mean TPM to consider a gene expressed

# spark config
SPARK_MEMORY = "8g"
APP_NAME     = "GTEx_TC5057"