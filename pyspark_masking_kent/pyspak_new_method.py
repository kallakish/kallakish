from pyspark.sql import SparkSession
import re

# Adjust these paths
INPUT_DIR = "/lakehouse/default/Files/exports"
OUTPUT_DIR = "/lakehouse/default/Files/processed"
OVERWRITE = True

print(f"Input directory: {INPUT_DIR}")
print(f"Output directory: {OUTPUT_DIR}")

spark = SparkSession.builder.getOrCreate()

# Fabric utility for listing files/folders
import os
import glob

def list_parquets(path):
    # List all parquet files and folders inside path (local filesystem)
    paths = []
    # Get all .parquet files (case-insensitive)
    files = glob.glob(os.path.join(path, '*.parquet'))
    paths.extend(files)
    # Also add folders (directories) if any - you may adjust this based on your dataset
    for f in os.listdir(path):
        full = os.path.join(path, f)
        if os.path.isdir(full):
            paths.append(full)
    return paths

def safe_str(val):
    if val is None:
        return ""
    return str(val)

def list_parquets(path):
    items = mssfs.ls(path)
    paths = []
    for item in items:
        # if file ends with .parquet or folder (isFile == False)
        if (item['isFile'] and item['name'].lower().endswith('.parquet')) or (not item['isFile']):
            paths.append(item['path'])
    return paths

def process_parquet(path):
    print(f"Processing: {path}")
    try:
        df = spark.read.parquet(path)
    except Exception as e:
        print(f"Error reading parquet {path}: {e}")
        return

    cols = df.columns
    first_row = df.limit(1).collect()
    if first_row:
        first_row = first_row[0]
    else:
        first_row = None

    data = []
    for c in cols:
        sample = safe_str(first_row[c]) if first_row else ""
        data.append((c, sample, None))

    out_df = spark.createDataFrame(data, ["TABLE_COLUMN_NAME", "SAMPLE_DATA", "IS_MASKED"])

    import os
    base = os.path.basename(path.rstrip('/'))
    out_name = strip_timestamp(base)
    out_path = OUTPUT_DIR.rstrip('/') + '/' + out_name

    mode = "overwrite" if OVERWRITE else "error"
    out_df.coalesce(1).write.option("header", True).mode(mode).csv(out_path)

    print(f"Wrote CSV to: {out_path}")

parquet_datasets = list_parquets(INPUT_DIR)
if not parquet_datasets:
    print("No parquet files or folders found.")
else:
    for p in parquet_datasets:
        process_parquet(p)

print("Done.")



from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

parquet_file = "/lakehouse/default/Files/bronze/Temp/DataMasking/table_column_files/input/xxxxxx_2025_08_07_20_43_32.parquet"

try:
    df = spark.read.parquet(parquet_file)
    df.show(5)
    print("Read successful!")
except Exception as e:
    print(f"Failed reading parquet file: {e}")

