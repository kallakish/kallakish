import os
import pandas as pd
import random
from collections import defaultdict

# === CONFIG ===
input_dir = "/lakehouse/default/Files/bronze/Temp/DataMasking"
output_dir = os.path.join(input_dir, "masked")
input_file_name = notebook_params.get("input_file_name", None)
salt = "FABRIC_MASKING_SALT"

if not input_file_name:
    raise ValueError("❌ Missing required parameter: 'input_file_name'.")

input_file_path = os.path.join(input_dir, input_file_name)
output_file_path = os.path.join(output_dir, input_file_name)

# === MASKING DICTIONARY ===
global_mask_cache = {}
counter = defaultdict(int)

def is_id_column(col):
    return col.lower().endswith("id")

def deterministic_mask_generic(val, col_name):
    if pd.isnull(val):
        return val

    key = f"{col_name}|{val}"
    if key in global_mask_cache:
        return global_mask_cache[key]

    # Generate new masked label
    counter[col_name] += 1
    masked_val = f"{col_name.upper()}_MASK_{counter[col_name]:03d}"
    global_mask_cache[key] = masked_val
    return masked_val

# === MASKING FUNCTION ===
def mask_csv_in_chunks(input_path, output_path, chunk_size=100_000):
    print(f"🔄 Masking: {os.path.basename(input_path)}")
    try:
        reader = pd.read_csv(input_path, chunksize=chunk_size, on_bad_lines='warn', engine='python')
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    first_chunk = True
    chunk_idx = 0

    for chunk in reader:
        chunk_idx += 1
        print(f"   📦 Chunk {chunk_idx}")

        for col in chunk.columns:
            if not is_id_column(col) and chunk[col].dtype == object:
                chunk[col] = chunk[col].apply(lambda x: deterministic_mask_generic(x, col))

        try:
            chunk.to_csv(output_path, mode='w' if first_chunk else 'a', index=False, header=first_chunk)
            first_chunk = False
        except Exception as e:
            print(f"❌ Error writing chunk {chunk_idx}: {e}")
            return False

    print(f"✅ Masked file saved: {output_path}")
    return True

# === RUN ===
success = mask_csv_in_chunks(input_file_path, output_file_path)
if not success:
    raise RuntimeError(f"❌ Failed to mask file: {input_file_name}")
else:
    print("🎉 File processed successfully.")






import os
import hashlib
import pandas as pd
from uuid import uuid4
from pathlib import Path

# Set paths
input_dir = "/lakehouse/default/Files/bronze/Temp/DataMasking"
output_dir = os.path.join(input_dir, "masked")
os.makedirs(output_dir, exist_ok=True)

# Reusable cache to ensure consistency of masked values
global_mask_cache = {}
salt = "FABRIC_MASKING_SALT"

# Helper: Identify ID columns (simple rule)
def is_id_column(col_name):
    col_name_lower = col_name.lower()
    return col_name_lower in ["id", "person_id", "user_id"] or col_name_lower.endswith("_id")

# Helper: Consistent masking with cache
def mask_value(col_name, val):
    if pd.isna(val) or val == "":
        return val
    key = f"{col_name}|{val}"
    if key in global_mask_cache:
        return global_mask_cache[key]
    else:
        # Use hash to get consistent and reversible value
        hashed = hashlib.sha256((salt + key).encode()).hexdigest()
        masked_val = f"{col_name.upper()}_MASK_{hashed[:8]}"
        global_mask_cache[key] = masked_val
        return masked_val

# Helper: Mask a single dataframe
def mask_dataframe(df):
    for col in df.columns:
        if df[col].dtype == "object" and not is_id_column(col):
            df[col] = df[col].apply(lambda val: mask_value(col, val))
    return df

# Process all CSVs
csv_files = [f for f in os.listdir(input_dir) if f.endswith(".csv")]
print(f"✅ Found {len(csv_files)} CSV files.")

error_files = []

for file in csv_files:
    input_path = os.path.join(input_dir, file)
    output_path = os.path.join(output_dir, file)

    try:
        print(f"🔄 Processing {file}...")
        df = pd.read_csv(input_path, on_bad_lines='skip')  # skip bad lines if any
        masked_df = mask_dataframe(df)
        masked_df.to_csv(output_path, index=False)
        print(f"✅ Done: {file} → {output_path}")
    except Exception as e:
        print(f"❌ Failed: {file} - {e}")
        error_files.append((file, str(e)))

# Summary
print("\n🔚 Batch processing complete.")
if error_files:
    print("⚠️ Some files failed:")
    for file, err in error_files:
        print(f"  - {file}: {err}")
else:
    print("🎉 All files processed successfully.")
