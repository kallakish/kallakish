import os
import pandas as pd
import hashlib

# --- Config ---
input_dir = "/lakehouse/default/Files/input_csvs"
output_dir = os.path.join(input_dir, "masked")
salt = "FABRIC_MASKING_SALT"

all_files = os.listdir(input_dir)
csv_files = [f for f in all_files if f.endswith(".csv")]

print(f"📂 Files found in '{input_dir}':")
for f in csv_files:
    print(f"   - {f}")


# --- Masking Logic ---
def mask_value(val, salt=""):
    if pd.isna(val):
        return val
    return hashlib.sha256((salt + str(val)).encode()).hexdigest()[:10]

def is_id_column(col_name):
    return "id" in col_name.lower()

def mask_csv_file(file_path, file_name):
    print(f"🔄 Processing: {file_name}")
    df = pd.read_csv(file_path)

    for col in df.columns:
        if is_id_column(col):
            print(f"   ✅ Preserving ID column: {col}")
        elif pd.api.types.is_string_dtype(df[col]):
            print(f"   🔒 Masking string column: {col}")
            df[col] = df[col].apply(lambda x: mask_value(x, salt))
        else:
            print(f"   ⚠️ Leaving column unchanged (type={df[col].dtype}): {col}")
            # Optionally: df[col] = None

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, file_name)
    df.to_csv(output_path, index=False)
    print(f"✅ Saved masked file: {output_path}")

# --- Batch Process All CSV Files ---
file_list = os.listdir(input_dir)
csv_files = [f for f in file_list if f.endswith(".csv")]

print(f"📂 Found {len(csv_files)} CSV files.")
for file_name in csv_files:
    full_path = os.path.join(input_dir, file_name)
    mask_csv_file(full_path, file_name)

print("🎉 All files masked.")





from pyspark.sql.functions import input_file_name

input_dir = "/lakehouse/default/Files/input_csvs"
output_dir = input_dir + "/masked"
salt = "FABRIC_MASKING_SALT"

# List all CSV files in the input_dir
df = spark.read.format("csv").option("header", "true").load(f"{input_dir}/*.csv")
files_df = df.withColumn("file_name", input_file_name()).select("file_name").distinct()

file_names = [os.path.basename(row.file_name) for row in files_df.collect()]

print(f"📂 Found {len(file_names)} CSV files in {input_dir}:")
for f in file_names:
    print(f"   - {f}")
