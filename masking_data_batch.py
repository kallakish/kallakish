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






import os
import pandas as pd
import hashlib
from pyspark.sql.functions import input_file_name

# --- Config ---
input_dir = "/lakehouse/default/Files/input_csvs"
output_dir = os.path.join(input_dir, "masked")
salt = "FABRIC_MASKING_SALT"

# Create output directory if it doesn't exist (Fabric handles this under the hood)
os.makedirs(output_dir, exist_ok=True)

# Helper: Check if column is an ID
def is_id_column(column_name):
    return column_name.lower().endswith("id")

# Helper: Consistent masking using SHA256
def mask_value(val, salt):
    if pd.isnull(val):
        return val
    return hashlib.sha256((salt + str(val)).encode()).hexdigest()

# Main masking function
def mask_csv_file(file_path, file_name):
    print(f"🔄 Processing: {file_name}")
    try:
        df = pd.read_csv(file_path, on_bad_lines='warn', engine='python')
    except Exception as e:
        print(f"❌ Error reading {file_name}: {e}")
        return

    # Apply masking
    for col in df.columns:
        if not is_id_column(col) and df[col].dtype == object:
            df[col] = df[col].apply(lambda x: mask_value(x, salt))

    # Write to output
    output_path = os.path.join(output_dir, file_name)
    try:
        df.to_csv(output_path, index=False)
        print(f"✅ Masked and saved to: {output_path}")
    except Exception as e:
        print(f"❌ Failed to save masked file: {file_name}. Error: {e}")

# List files using Spark (works with Lakehouse)
try:
    df_sample = spark.read.option("header", True).csv(f"{input_dir}/*.csv")
    files_df = df_sample.withColumn("file_name", input_file_name()).select("file_name").distinct()
    file_names = [os.path.basename(row.file_name) for row in files_df.collect()]
except Exception as e:
    print(f"❌ Failed to list CSVs in {input_dir}: {e}")
    file_names = []

# Process each file
for file_name in file_names:
    full_path = os.path.join(input_dir, file_name)
    mask_csv_file(full_path, file_name)

print("🎉 Masking complete.")



try:
    all_files = os.listdir(input_dir)
    csv_files = [f for f in all_files if f.lower().endswith(".csv")]
    print(f"📁 Found {len(csv_files)} CSV files.")
except Exception as e:
    print(f"❌ Could not list files in {input_dir}: {e}")
    csv_files = []

# Process each file
for file_name in csv_files:
    full_path = os.path.join(input_dir, file_name)
    mask_csv_file(full_path, file_name)

print("🎉 Data masking completed.")







import os
import pandas as pd
import hashlib

# === PARAMETERS ===
input_dir = "/lakehouse/default/Files/bronze/Temp/DataMasking"
output_dir = os.path.join(input_dir, "masked")
salt = "FABRIC_MASKING_SALT"

# Fetch file name from Fabric pipeline parameters
input_file_name = notebook_params.get("input_file_name", None)

if not input_file_name:
    raise ValueError("❌ Missing required parameter: 'input_file_name'.")

input_file_path = os.path.join(input_dir, input_file_name)
output_file_path = os.path.join(output_dir, input_file_name)

# === MASKING HELPERS ===

def is_id_column(column_name):
    return column_name.lower().endswith("id")

def mask_value(val, salt):
    if pd.isnull(val):
        return val
    return hashlib.sha256((salt + str(val)).encode()).hexdigest()

def mask_large_csv(input_path, output_path, chunk_size=100000):
    print(f"🔄 Masking: {os.path.basename(input_path)}")
    try:
        chunk_iter = pd.read_csv(input_path, chunksize=chunk_size, on_bad_lines='warn', engine='python')
    except Exception as e:
        print(f"❌ Failed to read CSV: {e}")
        return False

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    first_chunk = True
    chunk_num = 0

    for chunk in chunk_iter:
        chunk_num += 1
        print(f"   📦 Processing chunk {chunk_num}")

        for col in chunk.columns:
            if not is_id_column(col) and chunk[col].dtype == object:
                chunk[col] = chunk[col].apply(lambda x: mask_value(x, salt))

        try:
            chunk.to_csv(output_path, mode='w' if first_chunk else 'a', index=False, header=first_chunk)
            first_chunk = False
        except Exception as e:
            print(f"❌ Failed to write chunk {chunk_num}: {e}")
            return False

    print(f"✅ Masked file saved to: {output_path}")
    return True

# === RUN MASKING ===

success = mask_large_csv(input_file_path, output_file_path)

if not success:
    raise RuntimeError(f"❌ Masking failed for file: {input_file_name}")
else:
    print("🎉 File processed successfully.")

