from pyspark.sql import SparkSession
import os
import re
import fnmatch

# ----------------------------------
# Helpers for environment detection
# ----------------------------------
def has_dbutils():
    try:
        dbutils  # noqa: F821
        return True
    except Exception:
        return False

def has_mssparkutils():
    try:
        import mssparkutils
        return True
    except ImportError:
        return False

# Initialize utility object
MSUTILS = None
DBUTILS = None
if has_mssparkutils():
    import mssparkutils
    MSUTILS = mssparkutils
elif has_dbutils():
    DBUTILS = dbutils

# ----------------------------------
# Config
# ----------------------------------
INPUT_DIR = "/lakehouse/default/Files/exports"
OUTPUT_DIR = "/lakehouse/default/Files/processed"
FILE_PATTERN = "*.csv"
OVERWRITE = True

# ----------------------------------
# Detect delimiter
# ----------------------------------
def detect_delimiter(file_path, spark):
    delimiters = [",", ";", "\t", "|", "^"]
    for delim in delimiters:
        try:
            df_test = spark.read.option("header", True) \
                                .option("sep", delim) \
                                .option("mode", "DROPMALFORMED") \
                                .csv(file_path)
            if df_test.columns and len(df_test.columns) > 1:
                return delim
        except Exception:
            continue
    return ","

# ----------------------------------
# Strip timestamp from filename
# ----------------------------------
def strip_timestamp(filename):
    return re.sub(r"(_\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})\.csv$", ".csv", filename)

# ----------------------------------
# List files based on environment
# ----------------------------------
def list_csv_files(input_dir):
    if MSUTILS:  # Microsoft Fabric/Synapse
        return [f.path for f in MSUTILS.fs.ls(input_dir) if f.name.endswith(".csv")]
    elif DBUTILS:  # Databricks
        return [f.path for f in DBUTILS.fs.ls(input_dir) if f.name.endswith(".csv")]
    else:  # Pure Spark (local or generic)
        spark = SparkSession.builder.getOrCreate()
        files_df = spark.read.format("binaryFile").load(input_dir + "/*.csv").select("path").collect()
        return [row.path for row in files_df]

# ----------------------------------
# Main processing
# ----------------------------------
def process_csv_files():
    spark = SparkSession.builder.getOrCreate()

    all_files = list_csv_files(INPUT_DIR)
    if FILE_PATTERN != "*.csv":
        all_files = [f for f in all_files if fnmatch.fnmatch(os.path.basename(f), FILE_PATTERN)]

    if not all_files:
        print(f"No matching CSV files found in {INPUT_DIR}")
        return

    # Create output folder if possible
    if MSUTILS:
        MSUTILS.fs.mkdirs(OUTPUT_DIR)
    elif DBUTILS:
        DBUTILS.fs.mkdirs(OUTPUT_DIR)

    for file_path in all_files:
        try:
            delim = detect_delimiter(file_path, spark)

            df = spark.read.option("header", True) \
                           .option("sep", delim) \
                           .option("mode", "DROPMALFORMED") \
                           .option("encoding", "UTF-8") \
                           .csv(file_path)

            columns = df.columns
            first_row = df.limit(1).collect()

            if first_row:
                row_data = first_row[0]
                sample_values = ["" if row_data[c] is None else str(row_data[c]) for c in columns]
            else:
                sample_values = ["" for _ in columns]

            out_df = spark.createDataFrame(
                [(col, sample, None) for col, sample in zip(columns, sample_values)],
                ["TABLE_COLUMN_NAME", "SAMPLE_DATA", "IS_MASKED"]
            )

            original_name = os.path.basename(file_path)
            cleaned_name = strip_timestamp(original_name)
            output_path = os.path.join(OUTPUT_DIR, cleaned_name)

            mode = "overwrite" if OVERWRITE else "error"
            out_df.coalesce(1).write.option("header", True).mode(mode).csv(output_path)

            print(f"Wrote: {output_path}")

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

# ----------------------------------
# Run
# ----------------------------------
process_csv_files()
