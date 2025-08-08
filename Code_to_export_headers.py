from pyspark.sql import SparkSession
import os
import pandas as pd

# 1. Define lakehouse path (update this to your real path)
lakehouse_parquet_path = "Files/my-data/parquet/"  # source folder with .parquet files
output_excel_path = "Files/my-data/output_excel/"  # target folder

# 2. List all parquet files
dbutils.fs.ls(lakehouse_parquet_path)  # This helps you explore; not needed in final script

parquet_files = [f.path for f in dbutils.fs.ls(lakehouse_parquet_path) if f.name.endswith(".parquet")]

# 3. Ensure output folder exists
dbutils.fs.mkdirs(output_excel_path)

# 4. Loop through files
for file_path in parquet_files:
    # Extract parquet file name and base name
    file_name = os.path.basename(file_path)
    base_name = "_".join(file_name.split("_")[:3])  # get "xxxx_xxx_cccc"
    
    # Read parquet file
    df = spark.read.parquet(file_path)
    
    # Get column names
    column_names = df.columns
    
    # Create pandas DataFrame with header "column_name"
    column_df = pd.DataFrame({"column_name": column_names})
    
    # Set Excel file name
    excel_file_name = f"{base_name}.xlsx"
    excel_full_path = f"/lakehouse/default/{output_excel_path}{excel_file_name}"

    # Save Excel file (requires openpyxl or xlsxwriter in Fabric)
    column_df.to_excel(excel_full_path, index=False, engine="openpyxl")
    
    print(f"Wrote: {excel_file_name}")

