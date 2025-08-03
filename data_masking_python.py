dbutils.widgets.text("file_name", "")  # Passed from pipeline
file_name = dbutils.widgets.get("file_name")

# --- Imports ---
import pandas as pd
import hashlib
import os

# --- Config ---
input_dir = "/lakehouse/default/Files/input_csvs"
output_dir = "/lakehouse/default/Files/masked_csvs"
salt = "FABRIC_MASKING_SALT"

def mask_value(val, salt=""):
    if pd.isna(val):
        return val
    return hashlib.sha256((salt + str(val)).encode()).hexdigest()[:10]

def is_id_column(col_name):
    return "id" in col_name.lower()

# --- Load CSV ---
input_path = os.path.join(input_dir, file_name)
output_path = os.path.join(output_dir, file_name)

print(f"🔍 Processing file: {input_path}")
df = pd.read_csv(input_path)

# --- Apply masking ---
for col in df.columns:
    if is_id_column(col):
        print(f"✅ Preserving ID column: {col}")
        continue
    elif pd.api.types.is_string_dtype(df[col]):
        print(f"🔒 Masking string column: {col}")
        df[col] = df[col].apply(lambda x: mask_value(x, salt))
    else:
        print(f"⚠️ Leaving column unchanged (type={df[col].dtype}): {col}")
        # You can nullify or mask other types if needed

# --- Save masked CSV ---
df.to_csv(output_path, index=False)
print(f"✅ Saved masked data to: {output_path}")
