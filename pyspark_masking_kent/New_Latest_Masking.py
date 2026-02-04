# ===============================
# Notebook Parameters
# ===============================

source_folder_path = "Files/source_data"
mapping_folder_path = "Files/mapping"
table_name = "customer_data"
masked_output_path = "Files/masked"




from pyspark.sql import functions as F
import random


def get_latest_parquet(folder_path):
    files = dbutils.fs.ls(folder_path)

    parquet_files = [f for f in files if f.name.lower().endswith(".parquet")]

    if not parquet_files:
        raise Exception(f"No parquet files found in {folder_path}")

    latest_file = max(parquet_files, key=lambda f: f.modificationTime)
    return latest_file.path



latest_file_path = get_latest_parquet(source_folder_path)
print(f"Latest source file: {latest_file_path}")

df = spark.read.parquet(latest_file_path)



mapping_path = f"{mapping_folder_path}/{table_name}_mapping.csv"

mapping_df = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv(mapping_path)
    .filter(F.lower(F.col("IS_MASKED")) == "yes")
)

mapping_df.display()





# =========================
# Masking Functions
# =========================

def mask_name():
    return F.lit(random.choice([
        "John Smith", "Jane Doe", "Alex Brown", "Chris Taylor"
    ]))

def mask_postcode(col):
    return F.concat(
        F.substring(col, 1, 2),
        F.lit(str(random.randint(10, 99))),
        F.lit(" "),
        F.lit("".join(random.sample("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 3)))
    )

def mask_email():
    prefixes = ["dev", "developer", "dataengineering", "engineer"]
    domains = ["kent.police.uk", "essex.police.uk"]
    return F.lit(f"{random.choice(prefixes)}@{random.choice(domains)}")

def mask_phone(col):
    return F.concat(
        F.substring(col, 1, 2),
        F.lit("".join(str(random.randint(0, 9)) for _ in range(9)))
    )

def mask_free_text():
    return F.lit(random.choice([
        "Redacted", "Comment", "Lorem Ipsum"
    ]))

def mask_geo(col):
    return F.concat(
        F.substring(col, 1, F.length(col) - 2),
        F.lit(str(random.randint(10, 99)))
    )

def mask_creds():
    return F.lit("xxxxxxxx")

def mask_random():
    return F.lit(None)





Apply masking :

for row in mapping_df.collect():
    col_name = row["COLUMN_NAME"]
    pii_type = row["PII_TYPE"].lower()

    if col_name not in df.columns:
        raise Exception(f"Column {col_name} not found")

    if pii_type == "name":
        df = df.withColumn(col_name, mask_name())

    elif pii_type == "postcode":
        df = df.withColumn(col_name, mask_postcode(F.col(col_name)))

    elif pii_type == "email":
        df = df.withColumn(col_name, mask_email())

    elif pii_type == "phone":
        df = df.withColumn(col_name, mask_phone(F.col(col_name)))

    elif pii_type in ["comment", "address"]:
        df = df.withColumn(col_name, mask_free_text())

    elif pii_type == "geo":
        df = df.withColumn(col_name, mask_geo(F.col(col_name)))

    elif pii_type == "creds":
        df = df.withColumn(col_name, mask_creds())

    elif pii_type in ["birthdate", "socsec"]:
        df = df.withColumn(col_name, mask_random())

    else:
        print(f"⚠️ Unknown PII type: {pii_type}")



write data output_path = f"{masked_output_path}/{table_name}"

df.write.mode("overwrite").parquet(output_path)

print(f"Masked data written to {output_path}")



