import os
import re
import glob
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import StructType, StructField, StringType

# ===== EDIT THESE PATHS =====
DATASET_PATHS   = ["/Users/ashish/data/*.csv"]  # dataset files with timestamp in name
ATTRIBUTES_DIR  = "/Users/ashish/attributes"    # attributes CSV without timestamp
OUTPUT_DIR      = "/Users/ashish/masking_report"
# ============================

spark = SparkSession.builder.getOrCreate()

def strip_timestamp(name: str):
    """
    Removes _YYYY_MM_DD_HH_MM_SS before file extension.
    Example: customers_2025_01_01_00_00_00.csv -> customers.csv
    """
    return re.sub(r'_\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}\.csv$', '.csv', name)

# --- Masking helpers ---
def mask_string_col(df, col):
    h = F.sha2(F.concat_ws("||", F.lit(col), F.coalesce(F.col(col).cast("string"), F.lit(""))), 256)
    alias = F.concat(F.lit("str_"), h.substr(1, 10))
    return df.withColumn(col, F.when(F.col(col).isNull(), F.lit(None)).otherwise(alias))

def mask_numeric_col(df, col):
    h = F.sha2(F.concat_ws("||", F.lit(col), F.coalesce(F.col(col).cast("string"), F.lit(""))), 256)
    rnd01 = (F.conv(h.substr(1, 16), 16, 10).cast("double") % 10000) / F.lit(10000.0)
    factor = F.lit(0.9) + rnd01 * F.lit(0.2)
    return df.withColumn(col, (F.col(col).cast("double") * factor).cast(df.schema[col].dataType))

def mask_date_col(df, col):
    h = F.sha2(F.concat_ws("||", F.lit(col), F.coalesce(F.col(col).cast("string"), F.lit(""))), 256)
    delta = (F.conv(h.substr(1, 16), 16, 10).cast("bigint") % F.lit(731)) - F.lit(365)
    return df.withColumn(col, F.to_date(F.date_add(F.to_date(F.col(col)), delta)))

def apply_mask(df, col):
    dtype = dict(df.dtypes)[col].lower()
    if any(t in dtype for t in ["int", "double", "float", "decimal", "long", "short"]):
        return mask_numeric_col(df, col)
    if "date" in dtype or "timestamp" in dtype:
        return mask_date_col(df, col)
    return mask_string_col(df, col)

# Expand dataset patterns
all_datasets = []
for p in DATASET_PATHS:
    all_datasets.extend(glob.glob(p))

if not all_datasets:
    raise FileNotFoundError("No dataset files found.")

mask_truthy = ["YES", "Y", "TRUE", "1"]
os.makedirs(OUTPUT_DIR, exist_ok=True)

for dataset_path in all_datasets:
    print(f"🔹 Processing {dataset_path}")

    # Find matching attributes file
    base_name = os.path.basename(dataset_path)
    attr_file_name = strip_timestamp(base_name)  # remove timestamp
    attributes_path = os.path.join(ATTRIBUTES_DIR, attr_file_name)

    if not os.path.exists(attributes_path):
        print(f"⚠ No attributes file found for {dataset_path}, skipping.")
        continue

    # Load dataset
    df = spark.read.option("header", True).option("inferSchema", True).csv(dataset_path)

    # Load attributes
    attributes_schema = StructType([
        StructField("TABLE_COLUMN_NAME", StringType(), True),
        StructField("IS_Masked", StringType(), True)
    ])
    attr = spark.read.option("header", True).schema(attributes_schema).csv(attributes_path)

    # Normalize attributes
    attr_norm = (attr
        .withColumn("TABLE_COLUMN_NAME", F.trim(F.col("TABLE_COLUMN_NAME")).cast("string"))
        .withColumn("IS_Masked", F.upper(F.trim(F.col("IS_Masked"))).cast("string"))
        .filter(F.col("TABLE_COLUMN_NAME").isNotNull())
    )

    to_mask = (
        attr_norm.filter(F.col("IS_Masked").isin(mask_truthy))
                 .select("TABLE_COLUMN_NAME").distinct()
                 .rdd.flatMap(lambda r: r).collect()
    )
    to_mask = [c for c in to_mask if c in df.columns]

    # Apply masking
    df_out = df
    for c in to_mask:
        df_out = apply_mask(df_out, c)

    # Output file
    base_noext, _ = os.path.splitext(base_name)
    out_file = os.path.join(OUTPUT_DIR, f"{base_noext}_masked.csv")
    df_out.coalesce(1).write.mode("overwrite").option("header", True).csv(out_file)

    print(f"✅ Masked file saved: {out_file}")

print("🎯 All done!")
