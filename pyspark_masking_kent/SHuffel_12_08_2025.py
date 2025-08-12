from pyspark.sql import SparkSession, functions as F
from notebookutils import mssparkutils
import re

# ---------------- CONFIG ----------------
input_folder  = "lakehouse:/Files/my_input_folder"
schema_folder = "lakehouse:/Files/my_schema_folder"
output_folder = "lakehouse:/Files/my_output_folder"
# -----------------------------------------

spark = SparkSession.builder.getOrCreate()

def strip_timestamp(filename):
    """Remove _YYYY_MM_DD_hh_mm_ss from filename and extension."""
    base = re.sub(r'\.parquet$', '', filename, flags=re.IGNORECASE)
    return re.sub(r'_\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}$', '', base)

def find_schema_csv(table_name):
    """Find schema CSV matching table_name.csv (case-insensitive)."""
    for f in mssparkutils.fs.ls(schema_folder):
        if f['isFile'] and f['name'].lower() == f"{table_name.lower()}.csv":
            return f['path']
    return None

def is_integer_str_column(df, col):
    """Check if column (even if string type) contains only integers."""
    sample = df.select(col).na.drop().limit(1000).toPandas()[col].astype(str)
    return sample.str.match(r"^-?\d+$").all()

def mask_by_shuffle(df, col):
    """Mask column by shuffling its values."""
    # Collect distinct values
    values = df.select(col).distinct().rdd.flatMap(lambda x: x).collect()
    shuffled = values[:]
    import random
    random.shuffle(shuffled)
    mapping_df = spark.createDataFrame(zip(values, shuffled), [col, f"{col}_shuf"])
    return df.join(mapping_df, on=col, how="left").drop(col).withColumnRenamed(f"{col}_shuf", col)

# Process each parquet file
for file in mssparkutils.fs.ls(input_folder):
    if not file['isFile'] or not file['name'].lower().endswith(".parquet"):
        continue

    print(f"[INFO] Processing {file['name']}")
    base_table = strip_timestamp(file['name'])
    schema_path = find_schema_csv(base_table)

    if not schema_path:
        print(f"[WARN] No schema for {base_table}, skipping.")
        continue

    schema_df = spark.read.option("header", True).csv(schema_path)
    mask_cols = [r["TABLE_COLUMN_NAME"] for r in schema_df.filter(F.upper(F.col("IS_MASKED")) == "YES").collect()]

    df = spark.read.parquet(file['path'])
    mask_cols = [c for c in mask_cols if c in df.columns]

    for col in mask_cols:
        if is_integer_str_column(df, col):
            df = df.withColumn(col, F.col(col).cast("int"))
        df = mask_by_shuffle(df, col)

    # Write single parquet file
    tmp_dir = output_folder.rstrip("/") + f"/tmp_{file['name']}"
    final_file = output_folder.rstrip("/") + f"/{file['name']}"

    df.coalesce(1).write.mode("overwrite").parquet(tmp_dir)
    part_file = [f for f in mssparkutils.fs.ls(tmp_dir) if f['name'].startswith("part-")][0]
    mssparkutils.fs.mv(part_file['path'], final_file)
    mssparkutils.fs.rm(tmp_dir, True)

    print(f"[SUCCESS] Wrote masked file: {final_file}")
