import subprocess
import urllib
from sqlalchemy import create_engine
import pandas as pd
# from azure.identity import DefaultAzureCredential
# from azure.keyvault.secrets import SecretClient

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

ra_server_uri = 'postgresql://postgres:' + urllib.parse.quote_plus("Gde3400@@") + '@192.168.1.2:5432/CPW Blueprint'

engine = create_engine(ra_server_uri)

# laydown_ct = pd.read_sql_table('All_Laydown', engine)
# index = pd.read_sql_table('All_Index', engine)
# incr_rev_st_ct = pd.read_sql_table('All_Incremental_Revenue_ST', engine)
# incr_rev_lt_ct = pd.read_sql_table('All_Incremental_Revenue_LT', engine)
# channel_inputs = pd.read_sql_table('All_Channel_Inputs', engine)

# laydown_ct.to_csv("laydown_ct.csv")
# index.to_csv("index.csv")
# incr_rev_st_ct.to_csv("incr_rev_st_ct.csv")
# incr_rev_lt_ct.to_csv("incr_rev_lt_ct.csv")
# channel_inputs.to_csv("channel_inputs.csv")

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

# laydown = pd.read_csv("laydown_ct.csv")
# index = pd.read_csv("index.csv")
# incr_rev_st_ct = pd.read_csv("incr_rev_st_ct.csv")
# incr_rev_lt_ct = pd.read_csv("incr_rev_lt_ct.csv")
# channel_inputs = pd.read_csv("channel_inputs.csv")

# channel_inputs.drop(columns=['level_0'], inplace=True)

# laydown.to_sql('All_Laydown', engine, if_exists='replace')
# index.to_sql('All_Index', engine, if_exists='replace')
# incr_rev_st_ct.to_sql('All_Incremental_Revenue_ST', engine, if_exists='replace')
# incr_rev_lt_ct.to_sql('All_Incremental_Revenue_LT', engine, if_exists='replace')
# channel_inputs.to_sql('All_Channel_Inputs', engine, if_exists='replace')

results = pd.read_sql_table('Optimised CSV', engine)
results.to_csv(r"C:\Users\matthew.browne\Documents\Blueprint Documentation\Results.csv")