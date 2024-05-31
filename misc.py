import subprocess
import urllib
from sqlalchemy import create_engine
import pandas as pd

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

laydown_ct = pd.read_sql_table('All_Laydown', engine)
index = pd.read_sql_table('All_Index', engine)
incr_rev_st_ct = pd.read_sql_table('All_Incremental_Revenue_ST', engine)
incr_rev_lt_ct = pd.read_sql_table('All_Incremental_Revenue_LT', engine)
channel_inputs = pd.read_sql_table('All_Channel_Inputs', engine)

laydown_ct.to_csv("laydown_ct.csv")
index.to_csv("index.csv")
incr_rev_st_ct.to_csv("incr_rev_st_ct.csv")
incr_rev_lt_ct.to_csv("incr_rev_lt_ct.csv")
channel_inputs.to_csv("channel_inputs.csv")