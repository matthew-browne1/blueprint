import subprocess
import urllib
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

def generate_requirements_file(output_file='requirements.txt'):
    # Run 'pip freeze' to get a list of installed packages and their versions
    result = subprocess.run(['pip', 'freeze'], capture_output=True, text=True)
    
    # Check if the command was successful
    if result.returncode == 0:
        # Write the output to the specified file
        with open(output_file, 'w') as file:
            file.write(result.stdout)
        print(f"Requirements file '{output_file}' generated successfully.")
    else:
        print("Failed to generate the requirements file.")

generate_requirements_file()

# keyvault_url = "https://acblueprint-vault.vault.azure.net/"

# # Initialize Azure credentials
# credential = DefaultAzureCredential()

# # Initialize SecretClient
# secret_client = SecretClient(vault_url=keyvault_url, credential=credential)

# # Retrieve secrets from Key Vault
# db_username_secret = secret_client.get_secret("db-username").value
# db_password_secret = secret_client.get_secret("db-password").value

# # Host and database details
# host = "acblueprint-server.postgres.database.azure.com"
# database_name = "acblueprint-db"

# # Construct connection string
# connection_string = f"postgresql://{db_username_secret}:{db_password_secret}@{host}/{database_name}"
# engine = create_engine(connection_string)
# def get_tables():
#     ra_server_uri = 'postgresql://postgres:' + urllib.parse.quote_plus("Gde3400@@") + '@192.168.1.2:5432/CPW Blueprint'

#     # Create the new PostgreSQL URI for Azure


#     tables_to_download = ['All_Channel_Inputs', 'All_Laydown', 'All_Index']  # Replace 'table1', 'table2' with the names of your tables

# # Create a SQLAlchemy engine
#     engine = create_engine(ra_server_uri)

#     # Download tables as CSV files
#     for table_name in tables_to_download:
#         # Read the table directly into a pandas DataFrame
#         df = pd.read_sql_table(table_name, engine)

#         # Write the DataFrame to a CSV file
#         csv_filename = f"{table_name}.csv"
#         df.to_csv(csv_filename, index=False)

#         print(f"Table '{table_name}' downloaded and saved as '{csv_filename}'")

#     # Dispose the SQLAlchemy engine
#     engine.dispose()

# get_tables()

# csv_files = ['All_Channel_Inputs.csv','All_Index.csv','All_Laydown.csv']

# for csv_file in csv_files:
#     # Read CSV file into a pandas DataFrame
#     df = pd.read_csv(csv_file)

#     # Remove the file extension to get the table name
#     table_name = csv_file.split('.')[0]

#     # Write DataFrame to database as a table
#     df.to_sql(name=table_name, con=engine, index=False, if_exists='replace')