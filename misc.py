import subprocess
from azure.identity import DefaultAzureCredential
import urllib
from azure.keyvault.secrets import SecretClient
from sqlalchemy import create_engine

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

#generate_requirements_file()

keyvault_url = "https://acblueprint-vault.vault.azure.net/"

# Initialize Azure credentials
credential = DefaultAzureCredential()

# Initialize SecretClient
secret_client = SecretClient(vault_url=keyvault_url, credential=credential)

# Retrieve secrets from Key Vault
db_username_secret = secret_client.get_secret("db-username").value
db_password_secret = secret_client.get_secret("db-password").value

# Host and database details
host = "acblueprint-server.postgres.database.azure.com"
database_name = "acblueprint-db"

# Construct connection string
connection_string = f"postgresql://{db_username_secret}:{db_password_secret}@{host}/{database_name}"


try:
    engine = create_engine(connection_string)
    # Check if the connection was successful
    if engine.connect():
        print("Connection to the database successful!")
except Exception as e:
    print("Failed to connect to the database:", e)