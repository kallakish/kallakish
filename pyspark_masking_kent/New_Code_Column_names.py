import re
from pyspark.sql import SparkSession
from notebookutils import mssparkutils  # Fabric equivalent of dbutils

# -----------------------------
# Config - absolute paths
# -----------------------------
INPUT_DIR = "lakehouse:/Files/bronze/Temp/DataMasking/table_column_files/input"
OUTPUT_DIR = "lakehouse:/Files/bronze/Temp/DataMasking/table_column_files/output"
OVERWRITE = True

print(f"[INFO] Starting script")
print(f"[INFO] INPUT_DIR = {INPUT_DIR}")
print(f"[INFO] OUTPUT_DIR = {OUTPUT_DIR}")
print(f"[INFO] OVERWRITE = {OVERWRITE}")

# -----------------------------
# Helper: Strip timestamp from filename
# -----------------------------
def strip_timestamp(name):
    # Remove _YYYY_MM_DD_HH_mm_ss from end and change extension to .csv
    cleaned = re.sub(r'(_\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})\.parquet$', '.csv', name)
    print(f"[DEBUG] Filename cleaned: {name} -> {cleaned}")
    return cleaned

# -----------------------------
# Main processing function
# -----------------------------
def process_parquet_files():
    spark = SparkSession.builder.getOrCreate()

    print(f"[INFO] Listing Parquet files in {INPUT_DIR}")
    try:
        files_info = mssparkutils.fs.ls(INPUT_DIR)
        parquet_files = [f for f in files_info if f.name.endswith(".parquet")]
    except Exception as e:
        print(f"[ERROR] Could not list files in {INPUT_DIR}: {e}")
        return

    if not parquet_files:
        print(f"[WARN] No Parquet files found in {INPUT_DIR}")
        return

    print(f"[INFO] Found {len(parquet_files)} parquet file(s)")

    for file_info in parquet_files:
        file_path = file_info.path
        file_name = file_info.name

        print(f"[INFO] Processing file: {file_path}")

        try:
            # Read parquet file (dataset or single file)
            df = spark.read.parquet(file_path)

            columns = df.schema.names
            print(f"[DEBUG] Columns detected: {columns}")

            first_row = df.limit(1).collect()
            if first_row:
                row = first_row[0]
                sample_values = []
                for col in columns:
                    val = row[col]
                    if val is None:
                        sample_values.append("")
                    else:
                        # Convert complex types to string
                        sample_values.append(str(val))
            else:
                sample_values = [""] * len(columns)

            print(f"[DEBUG] Sample values: {sample_values}")

            # Create output DataFrame with required columns
            out_rows = [(col, sample, None) for col, sample in zip(columns, sample_values)]
            out_df = spark.createDataFrame(out_rows, ["TABLE_COLUMN_NAME", "SAMPLE_DATA", "IS_MASKED"])

            # Clean filename for output
            cleaned_name = strip_timestamp(file_name)

            output_path = f"{OUTPUT_DIR}/{cleaned_name}"

            print(f"[INFO] Writing output CSV to: {output_path}")

            mode = "overwrite" if OVERWRITE else "error"

            # Write as single CSV file with header
            out_df.coalesce(1).write.option("header", True).mode(mode).csv(output_path)

            print(f"[SUCCESS] Written output for {file_name} at {output_path}")

        except Exception as e:
            print(f"[ERROR] Failed processing {file_path}: {e}")

# -----------------------------
# Run the script
# -----------------------------
process_parquet_files()
print("[INFO] Script finished")
