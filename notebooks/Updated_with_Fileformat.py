from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import re
from notebookutils import mssparkutils  # Fabric's alternative to dbutils

# Initialize Spark Session
spark = SparkSession.builder.appName("BronzeToSilverETL").getOrCreate()

# Sample Parameters
storage_account = "my_storage_account"
lakehouse_path = "abfss://lakehouse@my_storage_account.dfs.core.windows.net"
bronze_path = "Files/bronze/Metadata_Framework"
silver_path = "Files/silver"
query_file_path = "Files/queries/transformation.sql"
source_tables = ["tbi_Stage"]  # List of source table names
target_table = "final_silver_table"  # Target table name

def get_latest_file(path):
    """Gets the latest file based on the timestamp in the filename."""
    print(f"Fetching latest file from path: {path}")
    
    files = mssparkutils.fs.ls(path)  # Use Fabric's mssparkutils instead of dbutils
    
    if not files:
        raise FileNotFoundError(f"No files found in {path}")
    
    # Regex to match filenames with expected format and extract timestamp
    pattern = re.compile(r"tbi_Stage_(\d{2}-\d{2}-\d{4}:\d{2}:\d{2}:\d{2})\.parquet")
    
    valid_files = []
    
    for file in files:
        match = pattern.search(file.name)
        if match:
            valid_files.append((file.path, match.group(1)))
    
    if not valid_files:
        raise FileNotFoundError(f"No matching files found in {path} with expected format.")
    
    # Sort files by extracted timestamp (convert to comparable format)
    latest_file = max(valid_files, key=lambda x: x[1])[0]
    
    print(f"Latest file found: {latest_file}")
    return latest_file

# Dictionary to hold DataFrames
dataframes = {}

# Load latest files for each source table
for table in source_tables:
    latest_file = get_latest_file(f"{bronze_path}/{table}")
    print(f"Using latest file for {table}: {latest_file}")
    
    # Load data into DataFrame
    df = spark.read.format("delta").load(latest_file)
    df.createOrReplaceTempView(table)  # Creating a temp view with table name
    print(f"Temporary view created for {table}")
    dataframes[table] = df

# Read the transformation queries from a .txt or .sql file
print(f"Reading transformation queries from: {query_file_path}")
with open(query_file_path, "r") as f:
    sql_queries = f.read().strip().split(";")  # Split queries by semicolon

# Create target table (if not exists)
spark.sql(f"CREATE TABLE IF NOT EXISTS {target_table} USING DELTA LOCATION '{silver_path}/{target_table}'")
print(f"Ensured target table {target_table} exists at {silver_path}/{target_table}")

# Process each transformation query
for sql_query in sql_queries:
    if sql_query.strip():  # Ensure it's not an empty query
        print(f"Executing query: {sql_query}")
        
        # Execute transformation query using the temp views
        silver_df = spark.sql(sql_query)
        
        # Print schema and few rows for debugging
        silver_df.printSchema()
        silver_df.show(5)
        
        # Write transformed data to Silver layer
        silver_df.write.format("delta").mode("overwrite").save(f"{silver_path}/{target_table}")
        print(f"Table {target_table} processed and saved to Silver layer at {silver_path}/{target_table}")

print("Bronze to Silver transformation completed!")
