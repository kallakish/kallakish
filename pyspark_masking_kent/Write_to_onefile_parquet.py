from pyspark.sql import SparkSession
from notebookutils import mssparkutils
import os
import re

spark = SparkSession.builder.getOrCreate()

INPUT_DIR = "/lakehouse/default/Files/bronze/Temp/DataMasking/table_column_files/input"
OUTPUT_DIR = "/lakehouse/default/Files/bronze/Temp/DataMasking/table_column_files/output"

def strip_timestamp(name):
    # Remove timestamp before extension
    return re.sub(r'(_\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})\.parquet$', '.parquet', name)

files = [f.path for f in mssparkutils.fs.ls(INPUT_DIR) if f.name.endswith(".parquet")]

for f in files:
    print(f"[INFO] Processing: {f}")
    df = spark.read.parquet(f)

    columns = df.columns
    first_row = df.limit(1).collect()

    sample_values = []
    if first_row:
        row_data = first_row[0]
        for c in columns:
            v = row_data[c]
            sample_values.append("" if v is None else str(v))
    else:
        sample_values = ["" for _ in columns]

    out_rows = list(zip(columns, sample_values, [None] * len(columns)))
    out_df = spark.createDataFrame(out_rows, ["TABLE_COLUMN_NAME", "SAMPLE_DATA", "IS_MASKED"])

    original_name = os.path.basename(f)
    cleaned_name = strip_timestamp(original_name)

    temp_dir = os.path.join(OUTPUT_DIR, cleaned_name + "_tmp")
    final_path = os.path.join(OUTPUT_DIR, cleaned_name)

    # Step 1: write to temp dir
    out_df.coalesce(1).write.mode("overwrite").parquet(temp_dir)

    # Step 2: find the part file
    part_file = [x.name for x in mssparkutils.fs.ls(temp_dir) if x.name.startswith("part-") and x.name.endswith(".parquet")][0]

    # Step 3: move to final path
    mssparkutils.fs.mv(os.path.join(temp_dir, part_file), final_path)

    # Step 4: delete temp dir
    mssparkutils.fs.rm(temp_dir, recurse=True)

    print(f"[SUCCESS] Written single file: {final_path}")
