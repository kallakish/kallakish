from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Initialize Spark Session
spark = SparkSession.builder.appName("BronzeToSilverETL").getOrCreate()

# Parameters (to be provided by the user)
storage_account = "<STORAGE_ACCOUNT_NAME>"
lakehouse_path = "<LAKEHOUSE_PATH>"
bronze_path = "<BRONZE_LAYER_PATH>"
silver_path = "<SILVER_LAYER_PATH>"
query_file_path = "<QUERY_FILE_PATH>"
source_tables = ["table1", "table2"]  # List of source table names
target_table = "<TARGET_TABLE_NAME>"  # Target table name parameter

# Function to get the latest file from a directory
def get_latest_file(path):
    files = dbutils.fs.ls(path)
    latest_file = max(files, key=lambda x: x.modificationTime).path
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
    dataframes[table] = df

# Read the transformation queries from a .txt or .sql file
with open(query_file_path, "r") as f:
    sql_queries = f.read().strip().split(";")  # Split queries by semicolon

# Create target table (if not exists)
spark.sql(f"CREATE TABLE IF NOT EXISTS {target_table} USING DELTA LOCATION '{silver_path}/{target_table}'")

# Process each transformation query
for sql_query in sql_queries:
    if sql_query.strip():  # Ensure it's not an empty query
        print(f"Executing query: {sql_query}")
        
        # Execute transformation query using the temp views
        silver_df = spark.sql(sql_query)
        
        # Write transformed data to Silver layer
        silver_df.write.format("delta").mode("overwrite").save(f"{silver_path}/{target_table}")
        print(f"Table {target_table} processed and saved to Silver layer")

print("Bronze to Silver transformation completed!")
