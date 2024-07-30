import subprocess
import urllib
from sqlalchemy import create_engine
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

ra_server_uri = 'postgresql://postgres:' + urllib.parse.quote_plus("Gde3400@@") + '@192.168.1.2:5432/CPW Blueprint'

# engine = create_engine(ra_server_uri)

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
engine = create_engine(connection_string)

dfs=[]
laydown = pd.read_excel("All_Laydown.xlsx", index_col="index")
dfs.append(laydown)
index = pd.read_excel("All_Index.xlsx", index_col="index")
dfs.append(index)
channel_inputs = pd.read_excel("All_Channel_Inputs.xlsx", index_col="index")
dfs.append(channel_inputs)
incr_rev_lt = pd.read_excel("All_Incremental_Revenue_LT.xlsx", index_col="index")
dfs.append(incr_rev_lt)
incr_rev_st = pd.read_excel("All_Incremental_Revenue_ST.xlsx", index_col="index")
dfs.append(incr_rev_st)
budget_response = pd.read_excel("Curves_Budget_Response.xlsx")
dfs.append(budget_response)
channel_response_blended = pd.read_excel("Curves_Channel_Response_Blended.xlsx", index_col="index")
dfs.append(channel_response_blended)
channel_response_LT = pd.read_excel("Curves_Channel_Response_LT.xlsx", index_col="index")
dfs.append(channel_response_LT)
channel_response_ST = pd.read_excel("Curves_Channel_Response_ST.xlsx", index_col="index")
dfs.append(channel_response_ST)
curves_horizon = pd.read_excel("Curves_Horizon.xlsx", index_col="index")
dfs.append(curves_horizon)
optimal_tv_laydown = pd.read_excel("Optimal_TV_Laydown.xlsx", index_col="index")
dfs.append(optimal_tv_laydown)
optimal_roi = pd.read_excel("Curves_Optimal_ROI.xlsx", index_col="index")
dfs.append(optimal_roi)
nns = pd.read_excel("ROIs and factors all regions inc. KSA.xlsx", index_col="index")

for df in dfs:
    if "Unnamed: 0" in df.columns:
        df.drop(columns=["Unnamed: 0"], inplace=True)

# laydown.drop(columns=["Unnamed: 0"], inplace=True)
# index.drop(columns=["Unnamed: 0"], inplace=True)
# channel_inputs.drop(columns=["Unnamed: 0"], inplace=True)
# incr_rev_lt.drop(columns=["Unnamed: 0"], inplace=True)
# incr_rev_st.drop(columns=["Unnamed: 0"], inplace=True)
# budget_response.drop(columns=["Unnamed: 0"], inplace=True)
# channel_response_blended.drop(columns=["Unnamed: 0"], inplace=True)
# channel_response_LT.drop(columns=["Unnamed: 0"], inplace=True)
# channel_response_ST.drop(columns=["Unnamed: 0"], inplace=True)
# optimal_roi.drop(columns=["Unnamed: 0"], inplace=True)
# curves_horizon.drop(columns=["Unnamed: 0"], inplace=True)
# optimal_tv_laydown.drop(columns=["Unnamed: 0"], inplace=True)

laydown.to_sql('All_Laydown', engine, if_exists='replace')
index.to_sql("All_Index", engine, if_exists="replace")
channel_inputs.to_sql('All_Channel_Inputs', engine, if_exists='replace')
incr_rev_lt.to_sql('All_Incremental_Revenue_ST', engine, if_exists='replace')
incr_rev_st.to_sql('All_Incremental_Revenue_LT', engine, if_exists='replace')
channel_response_blended.to_sql('Curves_Channel_Response_Blended', engine, if_exists='replace')
channel_response_LT.to_sql('Curves_Channel_Response_LT', engine, if_exists='replace')
channel_response_ST.to_sql('Curves_Channel_Response_ST', engine, if_exists='replace')
curves_horizon.to_sql('Curves_Horizon', engine, if_exists='replace')
optimal_tv_laydown.to_sql('Optimal_TV_Laydown', engine, if_exists='replace')
optimal_roi.to_sql('Curves_Optimal_ROI', engine, if_exists='replace')
budget_response.to_sql('Curves_Budget_Response', engine, if_exists='replace')