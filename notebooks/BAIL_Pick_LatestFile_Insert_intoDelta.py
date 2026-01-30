# ==============================
# PIPELINE DATE PARAMETERS
# ==============================
p_year = 2026
p_month = 1
p_day = 20

# ==============================
# SOURCE CONFIG (Workspace B)
# ==============================
SOURCE_WORKSPACE = "ws-b"
SOURCE_LAKEHOUSE = "lh-bronze"
SOURCE_BASE_PATH = "bronze/source1"

# ==============================
# TARGET CONFIG (Workspace C)
# ==============================
TARGET_WORKSPACE = "ws-c"
TARGET_LAKEHOUSE = "lh-curated"
TARGET_SCHEMA = "curated"

WRITE_MODE = "overwrite"

# ==============================
# ALLOWED FILE PREFIXES
# ==============================
ALLOWED_FILE_PREFIXES = [
    "filex",
    "filey",
    "filez",
    "filea",
    "fileb"
]

# ==============================
# WRITE RULES
# prefix → target table(s)
# ==============================
WRITE_RULES = {
    "filex": ["table_x"],
    "filey": ["table_y"],
    "filez": ["common_table"],
    "filea": ["common_table"],
    "fileb": ["table_b"]
}







from mssparkutils import fs
from pyspark.sql.functions import current_timestamp, lit
from collections import defaultdict

# ------------------------------
# Resolve date folders
# ------------------------------
year_folder = f"Year_{p_year}"
month_folder = f"Month_{str(p_month).zfill(2)}"
day_folder = f"Day_{str(p_day).zfill(2)}"

# ------------------------------
# Build source folder path
# ------------------------------
source_folder_path = (
    f"abfss://{SOURCE_WORKSPACE}@onelake.dfs.fabric.microsoft.com/"
    f"{SOURCE_LAKEHOUSE}/Files/{SOURCE_BASE_PATH}/"
    f"{year_folder}/{month_folder}/{day_folder}"
)

# ------------------------------
# List parquet files
# ------------------------------
files = fs.ls(source_folder_path)
parquet_files = [f for f in files if f.name.lower().endswith(".parquet")]

if not parquet_files:
    raise Exception("No parquet files found in source folder")

# ------------------------------
# Pick latest file per prefix
# ------------------------------
latest_files = {}

for prefix in ALLOWED_FILE_PREFIXES:
    matched = [
        f for f in parquet_files
        if f.name.lower().startswith(prefix.lower())
    ]

    if not matched:
        continue

    latest = sorted(
        matched,
        key=lambda f: f.modificationTime,
        reverse=True
    )[0]

    latest_files[prefix] = latest

if not latest_files:
    raise Exception("No files matched allowed prefixes")

# ------------------------------
# Read files & buffer by target table
# ------------------------------
table_buffers = defaultdict(list)

for prefix, file_obj in latest_files.items():

    df = spark.read.parquet(file_obj.path)

    if df.count() == 0:
        raise Exception(f"Empty file detected: {file_obj.name}")

    df = (
        df
        .withColumn("ingestion_ts", current_timestamp())
        .withColumn("source_file", lit(file_obj.name))
        .withColumn("source_prefix", lit(prefix))
        .withColumn("year", lit(p_year))
        .withColumn("month", lit(p_month))
        .withColumn("day", lit(p_day))
    )

    for target_table in WRITE_RULES.get(prefix, []):
        table_buffers[target_table].append(df)

# ------------------------------
# Write Delta tables (1 or many)
# ------------------------------
for target_table, dfs in table_buffers.items():

    final_df = dfs[0]
    for extra_df in dfs[1:]:
        final_df = final_df.unionByName(extra_df)

    target_path = (
        f"abfss://{TARGET_WORKSPACE}@onelake.dfs.fabric.microsoft.com/"
        f"{TARGET_LAKEHOUSE}/Tables/{TARGET_SCHEMA}/{target_table}"
    )

    (
        final_df.write
        .format("delta")
        .mode(WRITE_MODE)
        .option("overwriteSchema", "true")
        .save(target_path)
    )

    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {TARGET_SCHEMA}.{target_table}
        USING DELTA
        LOCATION '{target_path}'
    """)

# ------------------------------
# Exit for pipeline
# ------------------------------
mssparkutils.notebook.exit("SUCCESS")
