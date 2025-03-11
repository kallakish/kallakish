from pyspark.sql import SparkSession
import re
from notebookutils import mssparkutils  # Fabric's alternative to dbutils
from datetime import datetime  # To get current date

# Initialize Spark Session
spark = SparkSession.builder.appName("BronzeToSilverETL").getOrCreate()
print("Spark session initialized.")

# Sample Parameters
storage_account = "my_storage_account"
lakehouse_path = "abfss://lakehouse@my_storage_account.dfs.core.windows.net"
bronze_path_base = "Files/bronze/Metadata_Framework"
silver_path = "Files/silver"
query_file_path = "Files/queries/transformation.sql"
source_tables = ["xxxxx"]  # List of source table names, for example, "xxxxx"
target_table = "final_silver_table"  # Target table name

# Get the current date in dd-mm-yyyy format
current_date = datetime.now().strftime("%d-%m-%Y")
print(f"Current date: {current_date}")

# Concatenate the bronze path with the current date
bronze_path = f"{bronze_path_base}/{current_date}"
print(f"Constructed Bronze Path: {bronze_path}")

def get_latest_file(path, table_name):
    """Gets the latest file based on the timestamp in the filename."""
    print(f"Fetching latest file from path: {path}")
    
    files = mssparkutils.fs.ls(path)  # Use Fabric's mssparkutils instead of dbutils
    print(f"Found {len(files)} files in the path {path}")
    
    if not files:
        raise FileNotFoundError(f"No files found in {path}")
    
    # Regex to match filenames like 'xxxxx_11-03-2025:15:19:SS.parquet'
    # where `xxxxx` is the dynamic table name and the date follows this pattern
    pattern = re.compile(rf"{table_name}_(\d{{2}}-\d{{2}}-\d{{4}}:\d{{2}}:\d{{2}}:\d{{2}}:\d{{2}}).parquet")
    
    valid_files = []
    
    for file in files:
        match = pattern.search(file.name)
        if match:
            valid_files.append((file.path, match.group(1)))
    
    print(f"Found {len(valid_files)} valid files matching the pattern.")
    
    if not valid_files:
        raise FileNotFoundError(f"No matching files found in {path} with expected format.")
    
    # Sort files by extracted timestamp (convert to comparable format)
    latest_file = max(valid_files, key=lambda x: x[1])[0]
    
    print(f"Latest file found: {latest_file}")
    return latest_file

# Load latest files for each source table
for table in source_tables:
    print(f"Processing table: {table}")
    latest_file = get_latest_file(bronze_path, table)  # Pass the constructed bronze path with current date and table name
    print(f"Using latest file for {table}: {latest_file}")
    
    # Load data into SQL temp table using Spark SQL
    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW {table} AS 
        SELECT * FROM delta.`{latest_file}`
    """)
    print(f"Temporary SQL view created for {table}")

# Read the transformation queries from a .txt or .sql file
print(f"Reading transformation queries from: {query_file_path}")
with open(query_file_path, "r") as f:
    sql_queries = f.read().strip().split(";")  # Split queries by semicolon
print(f"Total {len(sql_queries)} transformation queries found.")

# Create target table (if not exists)
spark.sql(f"CREATE TABLE IF NOT EXISTS {target_table} USING DELTA LOCATION '{silver_path}/{target_table}'")
print(f"Ensured target table {target_table} exists at {silver_path}/{target_table}")

# Process each transformation query
for sql_query in sql_queries:
    if sql_query.strip():  # Ensure it's not an empty query
        print(f"Executing query: {sql_query}")
        
        # Execute transformation query using Spark SQL
        transformed_table = f"{target_table}_temp"
        spark.sql(f"""
            CREATE OR REPLACE TEMP VIEW {transformed_table} AS 
            {sql_query}
        """)
        print(f"Temporary view created for transformed data: {transformed_table}")
        
        # Debug: Show schema and sample rows
        print(f"Describing schema for {transformed_table}:")
        spark.sql(f"DESCRIBE {transformed_table}").show()
        
        print(f"Showing sample data (first 5 rows) for {transformed_table}:")
        spark.sql(f"SELECT * FROM {transformed_table} LIMIT 5").show()
        
        # Write transformed data to Silver layer
        spark.sql(f"""
            CREATE OR REPLACE TABLE {target_table} 
            USING DELTA 
            AS SELECT * FROM {transformed_table}
        """)
        print(f"Table {target_table} processed and saved to Silver layer at {silver_path}/{target_table}")

print("Bronze to Silver transformation completed!")
