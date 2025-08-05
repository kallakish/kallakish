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
