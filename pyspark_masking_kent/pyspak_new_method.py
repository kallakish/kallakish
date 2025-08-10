# PySpark (Fabric Notebook-ready)

import re
from uuid import uuid4

from pyspark.sql import Row
from pyspark.sql import functions as F
from pyspark.sql import types as T

# ----------------------
# CONFIGURE THESE PATHS
# ----------------------
INPUT_DIR  = "/lakehouse/default/Files/exports"         # folder with original CSV extracts
OUTPUT_DIR = "/lakehouse/default/Files/exports/output"  # folder to write result CSVs
GLOB       = "*.csv"                                    # optional: keep as *.csv

# ----------------------
# Helpers: environment
# ----------------------
def has_mssparkutils():
    try:
        import mssparkutils  # noqa: F401
        return True
    except Exception:
        return False

def has_dbutils():
    try:
        dbutils  # noqa: F821  # provided by some Spark envs (e.g., Databricks)
        return True
    except Exception:
        return False

MSUTILS = None
if has_mssparkutils():
    import mssparkutils
    MSUTILS = mssparkutils

# ----------------------
# List CSV files
# ----------------------
def list_csv_files(input_dir: str, pattern: str = "*.csv"):
    """List CSV files under input_dir. Fabric: use mssparkutils; else fallback via Spark Hadoop API."""
    files = []
    if MSUTILS:
        for f in MSUTILS.fs.ls(input_dir):
            if not f.isDir and f.name.lower().endswith(".csv"):
                files.append(f.path)
        return files

    # Fallback using Spark Hadoop FS
    jsc = spark._jsc
    sc_conf = jsc.hadoopConfiguration()
    Path = spark._jvm.org.apache.hadoop.fs.Path
    FileSystem = spark._jvm.org.apache.hadoop.fs.FileSystem
    fs = FileSystem.get(sc_conf)
    status = fs.listStatus(Path(input_dir))
    for st in status:
        if st.isFile():
            name = st.getPath().getName()
            if name.lower().endswith(".csv"):
                files.append(st.getPath().toString())
    return files

# ----------------------
# Detect delimiter quickly
# ----------------------
CANDIDATE_DELIMS = [",", ";", "\t", "|", "^"]

def detect_delimiter(file_path: str) -> str:
    """
    Get the first non-empty line using RDD, then pick the delimiter that
    yields the most fields. Defaults to comma.
    """
    try:
        first_line = (
            spark.sparkContext.textFile(file_path, minPartitions=1)
            .filter(lambda x: x is not None and x.strip() != "")
            .first()
        )
        counts = {d: first_line.count(d) for d in CANDIDATE_DELIMS}
        best = max(counts, key=counts.get)
        return best if counts[best] > 0 else ","
    except Exception:
        return ","

# ----------------------
# Strip timestamp from filename
#   in:  xxxx_xxx_cccc_2025_07_03_12_46_38.csv
#   out: xxxx_xxx_cccc.csv
# ----------------------
TIMESTAMP_RE = re.compile(r"^(.*?)(?:_\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})\.csv$", re.IGNORECASE)

def cleaned_basename(csv_name: str) -> str:
    m = TIMESTAMP_RE.match(csv_name)
    if m:
        return f"{m.group(1)}.csv"
    # if no timestamp pattern, return original
    return csv_name

# ----------------------
# Write single CSV file & rename to desired name
# ----------------------
def write_single_csv(df, final_path_csv: str):
    """
    Writes df as a single CSV with header to a temp folder, then moves the single part file
    to final_path_csv (and removes temp folder). Uses mssparkutils if available.
    """
    final_dir, final_name = final_path_csv.rsplit("/", 1)
    tmp_dir = f"{final_dir}/.__tmp_{uuid4().hex}"

    # write as single part
    df.coalesce(1).write.mode("overwrite").option("header", True).csv(tmp_dir)

    if MSUTILS:
        # find the single part CSV in tmp_dir
        part_csv = None
        for f in MSUTILS.fs.ls(tmp_dir):
            if f.name.endswith(".csv"):
                part_csv = f.path
                break
        if part_csv is None:
            raise RuntimeError(f"No CSV part file found in temp dir: {tmp_dir}")

        # ensure output dir exists
        try:
            MSUTILS.fs.mkdirs(final_dir)
        except Exception:
            pass

        # move/rename the part file to final single CSV
        final_full = f"{final_dir}/{final_name}"
        # If target exists, remove it first
        try:
            MSUTILS.fs.rm(final_full, recurse=False)
        except Exception:
            pass

        MSUTILS.fs.mv(part_csv, final_full, True)
        # cleanup temp
        MSUTILS.fs.rm(tmp_dir, recurse=True)
        print(f"Wrote: {final_full}")
        return final_full

    # Fallback: leave temp folder path (if not using Fabric). User can manually collect the part file.
    print(f"[Fallback] Wrote temp folder: {tmp_dir} (please rename the single part file to {final_path_csv})")
    return tmp_dir

# ----------------------
# Core processing for one file
# ----------------------
def process_one(file_path: str):
    # derive clean output file name
    base_name = file_path.split("/")[-1]
    final_name = cleaned_basename(base_name)  # xxxx_xxx_cccc.csv
    final_out_path = f"{OUTPUT_DIR}/{final_name}"

    # detect delimiter
    sep = detect_delimiter(file_path)

    # read just header + first row
    df = (
        spark.read
        .option("header", True)
        .option("inferSchema", False)
        .option("sep", sep)
        .csv(file_path)
    )

    columns = df.columns
    # take first row (if any)
    first_row = df.limit(1).collect()
    sample = first_row[0].asDict(recursive=True) if first_row else {}

    # build output rows: TABLE_COLUMN_NAME, SAMPLE_DATA, IS_MASKED (NULL)
    rows = [(col, (sample.get(col, None)), None) for col in columns]

    schema = T.StructType([
        T.StructField("TABLE_COLUMN_NAME", T.StringType(), True),
        T.StructField("SAMPLE_DATA", T.StringType(), True),
        T.StructField("IS_MASKED", T.StringType(), True),
    ])
    out_df = spark.createDataFrame(rows, schema=schema)

    # write single CSV named exactly xxxx_xxx_cccc.csv
    write_single_csv(out_df, final_out_path)

# ----------------------
# Run
# ----------------------
files = list_csv_files(INPUT_DIR, GLOB)
if not files:
    print(f"No CSV files found in: {INPUT_DIR}")
else:
    print(f"Found {len(files)} file(s). Processing...")
    for p in files:
        try:
            process_one(p)
        except Exception as e:
            print(f"ERROR processing {p}: {e}")



from pyspark.sql import SparkSession
import os
import re
import fnmatch

# -----------------------------
# Configuration (edit these paths)
# -----------------------------
INPUT_DIR = "/lakehouse/default/Files/exports"
OUTPUT_DIR = "/lakehouse/default/Files/processed"
FILE_PATTERN = "*.csv"
OVERWRITE = True  # Set to False if you don't want to overwrite

# -----------------------------
# Helper: Detect delimiter
# -----------------------------
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
    return ","  # default fallback

# -----------------------------
# Helper: Strip timestamp suffix
# -----------------------------
def strip_timestamp(filename):
    return re.sub(r"(_\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})\.csv$", ".csv", filename)

# -----------------------------
# Main processing
# -----------------------------
def process_csv_files():
    spark = SparkSession.builder.getOrCreate()

    # List all CSV files in the input folder
    all_files = [f.path for f in dbutils.fs.ls(INPUT_DIR) if f.name.endswith(".csv")]
    all_files = [f for f in all_files if fnmatch.fnmatch(os.path.basename(f), FILE_PATTERN)]

    if not all_files:
        print(f"No matching CSV files found in {INPUT_DIR}")
        return

    # Create output folder if not exists
    dbutils.fs.mkdirs(OUTPUT_DIR)

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

            # Create output DataFrame
            out_df = spark.createDataFrame(
                [(col, sample, None) for col, sample in zip(columns, sample_values)],
                ["TABLE_COLUMN_NAME", "SAMPLE_DATA", "IS_MASKED"]
            )

            # Build output file path
            original_name = os.path.basename(file_path)
            cleaned_name = strip_timestamp(original_name)
            output_path = os.path.join(OUTPUT_DIR, cleaned_name)

            # Write to CSV
            mode = "overwrite" if OVERWRITE else "error"
            out_df.coalesce(1).write.option("header", True).mode(mode).csv(output_path)

            print(f"Wrote: {output_path}")

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

# -----------------------------
# Run
# -----------------------------
process_csv_files()

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



def list_csv_files(input_dir):
    if MSUTILS:  # Microsoft Fabric/Synapse
        return [f.path for f in MSUTILS.fs.ls(input_dir) if f.name.endswith(".csv")]
    elif DBUTILS:  # Databricks
        return [f.path for f in DBUTILS.fs.ls(input_dir) if f.name.endswith(".csv")]
    else:  # Pure Spark (local or generic)
        spark = SparkSession.builder.getOrCreate()
        files_df = spark.read.format("binaryFile").load(input_dir + "/*.csv").select("path").collect()
        return [row.path for row in files_df]
