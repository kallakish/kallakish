# pyspark_mask_simple.py
# Minimal deterministic masking with PySpark (CSV/Parquet only)

import os
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import StructType, StructField, StringType

# ========== EDIT THESE PATHS ==========
DATASET_PATH    = "/Users/ashish/9. Sales-Data-Analysis.csv"  # or .csv
ATTRIBUTES_PATH = "/Users/ashish/sales-Data-Analysis.csv"               # CSV with TABLE_COLUMN_NAME, IS_Masked
OUTPUT_DIR      = "/Users/ashish/masking_report"
# ======================================

spark = SparkSession.builder.getOrCreate()

def ext(path): return os.path.splitext(path)[1].lower()

# Load dataset
if ext(DATASET_PATH) == ".csv":
    df = spark.read.option("header", True).option("inferSchema", True).csv(DATASET_PATH)
elif ext(DATASET_PATH) == ".parquet":
    df = spark.read.parquet(DATASET_PATH)
else:
    raise ValueError("Dataset must be .csv or .parquet for this simple script.")

# Define schema for attributes file
attributes_schema = StructType([
    StructField("TABLE_COLUMN_NAME", StringType(), True),
    StructField("IS_Masked", StringType(), True)
])

# Load attributes (CSV or Parquet)
if ext(ATTRIBUTES_PATH) == ".csv":
    attr = spark.read.option("header", True).schema(attributes_schema).csv(ATTRIBUTES_PATH)
elif ext(ATTRIBUTES_PATH) == ".parquet":
    attr = spark.read.parquet(ATTRIBUTES_PATH)
else:
    raise ValueError("Attributes must be .csv or .parquet for this simple script.")

# Normalize attributes
attr_norm = (attr
    .withColumn("TABLE_COLUMN_NAME", F.trim(F.col("TABLE_COLUMN_NAME")).cast("string"))
    .withColumn("IS_Masked", F.upper(F.trim(F.col("IS_Masked"))).cast("string"))
    .filter(F.col("TABLE_COLUMN_NAME").isNotNull())
)

mask_truthy = ["YES", "Y", "TRUE", "1"]
to_mask = (
    attr_norm.filter(F.col("IS_Masked").isin(mask_truthy))
             .select("TABLE_COLUMN_NAME").distinct()
             .rdd.flatMap(lambda r: r).collect()
)
to_mask = [c for c in to_mask if c in df.columns]  # only columns present

# --- Masking helpers (deterministic) ---

def mask_string_col(df, col):
    """
    Map any string value to a deterministic pseudonym.
    Returns something like str_<10-char-hex>.
    Same input → same output within this column.
    """
    h = F.sha2(F.concat_ws("||", F.lit(col), F.coalesce(F.col(col).cast("string"), F.lit(""))), 256)
    alias = F.concat(F.lit("str_"), h.substr(1, 10))
    return df.withColumn(col, F.when(F.col(col).isNull(), F.lit(None)).otherwise(alias))

def mask_numeric_col(df, col):
    """
    Multiply by a deterministic factor in [0.9, 1.1].
    """
    h = F.sha2(F.concat_ws("||", F.lit(col), F.coalesce(F.col(col).cast("string"), F.lit(""))), 256)
    # take a slice of hash → bigint-ish → [0,1) → scale to [0.9, 1.1]
    rnd01 = (F.conv(h.substr(1, 16), 16, 10).cast("double") % 10000) / F.lit(10000.0)
    factor = F.lit(0.9) + rnd01 * F.lit(0.2)
    return df.withColumn(col, (F.col(col).cast("double") * factor).cast(df.schema[col].dataType))

def mask_date_col(df, col):
    """
    Shift date by a deterministic number of days in [-365, +365].
    """
    h = F.sha2(F.concat_ws("||", F.lit(col), F.coalesce(F.col(col).cast("string"), F.lit(""))), 256)
    delta = (F.conv(h.substr(1, 16), 16, 10).cast("bigint") % F.lit(731)) - F.lit(365)
    return df.withColumn(col, F.to_date(F.date_add(F.to_date(F.col(col)), delta)))

# Decide which strategy to use by Spark dtype (simple rules)
def apply_mask(df, col):
    dtype = dict(df.dtypes)[col].lower()
    if any(t in dtype for t in ["int", "double", "float", "decimal", "long", "short"]):
        return mask_numeric_col(df, col)
    if "date" in dtype or "timestamp" in dtype:
        return mask_date_col(df, col)
    # everything else → string masking
    return mask_string_col(df, col)

# Apply masks
df_out = df
for c in to_mask:
    df_out = apply_mask(df_out, c)

# Save outputs
os.makedirs(OUTPUT_DIR, exist_ok=True)
if ext(DATASET_PATH) == ".csv":
    out_path = os.path.join(OUTPUT_DIR, "dataset_masked_csv")
    (df_out.coalesce(1)
          .write.mode("overwrite")
          .option("header", True)
          .csv(out_path))
else:
    out_path = os.path.join(OUTPUT_DIR, "dataset_masked.parquet")
    df_out.write.mode("overwrite").parquet(out_path)

# Small report
if to_mask:  # Check if to_mask is not empty
    report = spark.createDataFrame([(c, dict(df_out.dtypes)[c]) for c in to_mask], ["column", "dtype"])
    (report.coalesce(1)
           .write.mode("overwrite")
           .option("header", True)
           .csv(os.path.join(OUTPUT_DIR, "_masking_report")))
    print("✅ Done. Output at:", out_path)
else:
    print("No columns to mask. Output at:", out_path)
