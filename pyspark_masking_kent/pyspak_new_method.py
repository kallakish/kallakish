from pyspark.sql import SparkSession
import os
import re
import fnmatch

# -----------------------------
# Config
# -----------------------------
INPUT_DIR = "/lakehouse/default/Files/exports"
OUTPUT_DIR = "/lakehouse/default/Files/processed"
FILE_PATTERN = "*.csv"
OVERWRITE = True

print(f"[INFO] Starting script")
print(f"[INFO] INPUT_DIR = {INPUT_DIR}")
print(f"[INFO] OUTPUT_DIR = {OUTPUT_DIR}")
print(f"[INFO] FILE_PATTERN = {FILE_PATTERN}")
print(f"[INFO] OVERWRITE = {OVERWRITE}")

# -----------------------------
# Helper: Detect delimiter
# -----------------------------
def detect_delimiter(file_path, spark):
    print(f"[DEBUG] Detecting delimiter for: {file_path}")
    delimiters = [",", ";", "\t", "|", "^"]
    for delim in delimiters:
        try:
            df_test = spark.read.option("header", True) \
                                .option("sep", delim) \
                                .option("mode", "DROPMALFORMED") \
                                .csv(file_path)
            if df_test.columns and len(df_test.columns) > 1:
                print(f"[DEBUG] Detected delimiter '{delim}' for {file_path}")
                return delim
        except Exception as e:
            print(f"[WARN] Delimiter '{delim}' failed for {file_path} -> {e}")
    print(f"[WARN] Could not detect delimiter, defaulting to comma")
    return ","

# -----------------------------
# Helper: Strip timestamp
# -----------------------------
def strip_timestamp(filename):
    cleaned = re.sub(r"(_\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})\.csv$", ".csv", filename)
    print(f"[DEBUG] Filename cleaned: {filename} -> {cleaned}")
    return cleaned

# -----------------------------
# Main
# -----------------------------
def process_csv_files():
    spark = SparkSession.builder.getOrCreate()

    print(f"[INFO] Listing CSV files in {INPUT_DIR} using binaryFile")
    files_df = spark.read.format("binaryFile").load(INPUT_DIR + "/*.csv").select("path").collect()
    all_files = [row.path for row in files_df]

    if FILE_PATTERN != "*.csv":
        all_files = [f for f in all_files if fnmatch.fnmatch(os.path.basename(f), FILE_PATTERN)]

    if not all_files:
        print(f"[ERROR] No matching CSV files found in {INPUT_DIR}")
        return

    print(f"[INFO] Found {len(all_files)} CSV file(s) to process")
    for f in all_files:
        print(f"[INFO] Processing file: {f}")

        try:
            delim = detect_delimiter(f, spark)

            print(f"[INFO] Reading CSV with delimiter '{delim}'")
            df = spark.read.option("header", True) \
                           .option("sep", delim) \
                           .option("mode", "DROPMALFORMED") \
                           .option("encoding", "UTF-8") \
                           .csv(f)

            columns = df.columns
            print(f"[DEBUG] Columns detected: {columns}")

            first_row = df.limit(1).collect()
            print(f"[DEBUG] First row: {first_row}")

            if first_row:
                row_data = first_row[0]
                sample_values = ["" if row_data[c] is None else str(row_data[c]) for c in columns]
            else:
                sample_values = ["" for _ in columns]

            print(f"[DEBUG] Sample values: {sample_values}")

            out_df = spark.createDataFrame(
                [(col, sample, None) for col, sample in zip(columns, sample_values)],
                ["TABLE_COLUMN_NAME", "SAMPLE_DATA", "IS_MASKED"]
            )

            original_name = os.path.basename(f)
            cleaned_name = strip_timestamp(original_name)
            output_path = os.path.join(OUTPUT_DIR, cleaned_name)

            print(f"[INFO] Writing output to: {output_path}")
            mode = "overwrite" if OVERWRITE else "error"
            out_df.coalesce(1).write.option("header", True).mode(mode).csv(output_path)

            print(f"[SUCCESS] Wrote: {output_path}")

        except Exception as e:
            print(f"[ERROR] Failed processing {f} -> {e}")

# -----------------------------
# Run
# -----------------------------
process_csv_files()
print(f"[INFO] Script finished")
