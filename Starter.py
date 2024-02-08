
# %% --------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
from flask import Flask, render_template, send_file, jsonify, request, url_for, redirect, flash, session, current_app
import numpy as np
import pandas as pd
import seaborn as sns
import json
import os
import sys
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from urllib.parse import parse_qs
from pyomo_opt import Optimiser
from sqlalchemy import create_engine, text, Column, DateTime, Integer
from sqlalchemy.orm import Session, declarative_base
import datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import urllib.parse
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import secrets

app = Flask(__name__)

azure_host = "blueprintalpha.postgres.database.azure.com"
azure_user = "bptestadmin"
azure_password = "Password!"
azure_database = "postgres" 

# Create the new PostgreSQL URI for Azure
azure_db_uri = f"postgresql://{azure_user}:{urllib.parse.quote_plus(azure_password)}@{azure_host}:5432/{azure_database}"

app.config['SQLALCHEMY_DATABASE_URI'] = azure_db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secrets.token_hex()
app.config['SESSION_COOKIE_SECURE'] = True

engine = create_engine(azure_db_uri)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    user_info = db.relationship('UserInfo', backref='user', lazy=True)

class UserInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Snapshot(db.Model):
    name = db.Column(db.String, nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String, nullable=False)
    table_ids = db.Column(db.String, nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.options(joinedload(User.user_info)).get(int(user_id))

user_data = [
    {'username': 'mattbrowne1', 'password': 'password123', 'full_name': 'Matthew Browne', 'email': 'matthew.browne@retailalchemy.co.uk'},
    {'username': 'testuser', 'password': 'testpassword', 'full_name': 'John Doe', 'email': 'user2@example.com'},
]

def add_user(user_data):
    existing_user = User.query.filter_by(username=user_data['username']).first()

    if existing_user is None:
        hashed_password = bcrypt.generate_password_hash(user_data['password']).decode('utf-8')
        new_user = User(username=user_data['username'], password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        new_user_info = UserInfo(full_name=user_data['full_name'], email=user_data['email'], user=new_user)
        db.session.add(new_user_info)
        db.session.commit()

        print(f"User '{user_data['username']}' added successfully.")
    else:
        print(f"User '{user_data['username']}' already exists.")


@app.route('/get_user_id', methods = ['GET'])
def get_user_id():
    user_id = current_user.id
    return jsonify({'user_id':user_id})


@app.route('/save_snapshot', methods=['POST'])
@login_required
def save_snapshot():
    snapshot_name = request.json.get('name')
    user_id = current_user.id
    content = request.json.get('content')
    current_table_ids = list(table_data.keys())

    table_ids_str = ','.join(map(str, current_table_ids))

    # Check if a snapshot with the same name already exists for the current user
    existing_snapshot = Snapshot.query.filter_by(name=snapshot_name, user_id=user_id).first()

    if existing_snapshot:
        # Update the existing snapshot
        existing_snapshot.content = content
        existing_snapshot.table_ids = table_ids_str
    else:
        # Create a new snapshot
        new_snapshot = Snapshot(name=snapshot_name, content=content, table_ids=table_ids_str, user_id=user_id)
        db.session.add(new_snapshot)

    try:
        db.session.commit()
        return jsonify({'success': True})
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/overwrite_save', methods = ['POST'])
@login_required
def overwrite_save():
    snapshot_id = request.json.get('selectedSaveId')
    user_id = current_user.id
    content = request.json.get('content')
    current_table_ids = list(table_data.keys())

    table_ids_str = ','.join(map(str, current_table_ids))

    print(f"snapshot id = {snapshot_id}")
    print(f"user id = {user_id}")

    existing_snapshot = Snapshot.query.filter_by(id=snapshot_id, user_id=user_id).first()
    existing_snapshot.content = content
    existing_snapshot.table_ids = table_ids_str

    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/load_snapshot')
@login_required
def load_snapshot():
    user_id = current_user.id
    snapshot = Snapshot.query.filter_by(user_id=user_id).first()

    content_list = snapshot.content
    table_ids_list = snapshot.table_ids
    print(table_data.keys())    
    return jsonify({'content': content_list, 'table_ids': table_ids_list})

@app.route('/get_saves', methods = ['GET'])
@login_required
def get_saves():
    if not current_user.is_authenticated:
        return jsonify({'error': 'User not authenticated'}), 401

    user_saves = Snapshot.query.filter_by(user_id=current_user.id).all()
    saves_data = []

    for save in user_saves:
        save_info = {
            'DT_RowId': save.id,  # Unique identifier for DataTables (required)
            'name': save.name,
            'table_ids': save.table_ids
        }
        saves_data.append(save_info)

    return jsonify({'data': saves_data})

@app.route('/toggle_states', methods = ['POST'])
def toggle_states():
    try:
        data = request.json
       
        return jsonify({"message": "Toggle states saved successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/load_selected_row', methods = ['GET', 'POST'])
@login_required
def notify_selected_row():
    if request.method == 'POST':
        save_id = request.json.get('selectedSaveId')
        session['save_id'] = save_id
        return jsonify({'status': 'POST request procecssed successfully'})
    
    elif request.method == 'GET':
        save_id = session.get('save_id')
        session.pop('save_id', None)
        save = Snapshot.query.filter_by(id=save_id, user_id = current_user.id).first()
        if not save:
            return jsonify({'error':'Unathorized access'}), 403
        else:
            content_list = save.content
            table_ids_list = save.table_ids
            print(table_data.keys())    
            return jsonify({'content': content_list, 'table_ids': table_ids_list})



    
# OPTIMISER FILE PATHS - OLD VERSION

# laydown_filepath = os.path.join(input_fpath, f"Opt Inputs/Laydown_{brand}.csv")
# seas_index_fp = os.path.join(input_fpath, f"Opt Inputs/Index_{brand}.csv")

# channel_json = os.path.join(sys.path[0], "data/channel.json")
# channel_input = pd.read_csv("optimiser input data/UK_Channel_Inputs_v3.csv")
# channel_input.drop(columns='Unnamed: 0', inplace=True)

# channel_dict = {1:channel_input.to_dict("records")}
# ST_laydown = pd.read_csv(laydown_filepath)
# ST_laydown.rename(columns={'Unnamed: 0':'Time_Period'}, inplace=True)
# ST_laydown = ST_laydown.fillna(0)

# streams = []
# for var in channel_dict[1]:
#     streams.append(var['Channel'])

# ST_laydown_dates = ST_laydown['Time_Period']

# with open(channel_json, "w") as file:
#     json.dump(channel_dict, file, indent=4)

# with open(channel_json) as file:
#     ST_channel_input = json.load(file)

# opt_betas_dict = Optimiser.beta_opt(laydown=ST_laydown, channel_input=channel_dict[1])

# channel_input['Beta'] = list(opt_betas_dict.values())
# channel_dict = {"1":channel_input.to_dict("records")}

# max_budget = 0
results = {}

# seas_index = pd.read_csv(seas_index_fp)
# seas_index.rename(columns={'Unnamed: 0':'Time_Period'}, inplace=True)

######

# USING HEADER FILE FOR ST AND LT

# ST



brand = 'Gourmet'
input_fpath = "Y:/2023/Nestle Spiderweb/Deep Dive/Alphas/"

laydown_filepath = os.path.join(input_fpath, f"Opt Inputs/Laydown_{brand}.csv")
seas_index_fp = os.path.join(input_fpath, f"Opt Inputs/Index_{brand}.csv")
channel_json = os.path.join(sys.path[0], "data/channel.json")

alpha_headers_fp = os.path.join(input_fpath, "Alpha Work_v2.xlsx")
alpha_headers = pd.read_excel(alpha_headers_fp, 'Opt_Header')

ST_header = alpha_headers[alpha_headers['Range'] == brand]
ST_header = ST_header.iloc[:, :-3]

ST_header.drop(columns=['Channel'], inplace=True)
ST_header.rename(columns={'concat':'Channel', 'Adstock':'Carryover', 'Wtd ROI':'Current_ROI', 'Total Spend':"Current_Budget"}, inplace=True)
ST_header['Max_Spend_Cap'] = ST_header['Current_Budget']*1.5
ST_header['Min_Spend_Cap'] = 0
ST_header['CPU'] = 1

laydown = pd.read_csv(laydown_filepath)
laydown.rename(columns={'Unnamed: 0':'Time_Period'}, inplace=True)
laydown.fillna(0)

seas_index = pd.read_csv(seas_index_fp)
seas_index.rename(columns={'Unnamed: 0':'Time_Period'}, inplace=True)

for x in laydown.columns.tolist():
    if x not in ST_header['Channel'].tolist() and x != 'Time_Period':
        laydown.drop(columns=[x], inplace=True)

streams = []
for stream in ST_header['Channel']:
    streams.append(str(stream))

laydown_dates = laydown['Time_Period']
print(f"current (incorrect) current budget: {ST_header['Current_Budget']}")

for stream in streams:
    ST_header.loc[ST_header['Channel'] == stream, 'Current_Budget'] = sum(laydown[stream])

ST_header_dict = ST_header.to_dict("records")

ST_opt_betas_dict = Optimiser.beta_opt(laydown=laydown, channel_input=ST_header_dict)
print(ST_opt_betas_dict)

ST_header['Beta'] = list(ST_opt_betas_dict.values())

ST_header_dict = ST_header.to_dict("records")

max_spend_cap = sum(ST_header['Max_Spend_Cap'])

print(max_spend_cap)

table_df = ST_header.copy()

dataTable_cols = ['Channel', 'Carryover', 'Alpha', 'Beta', 'Current_Budget', 'Min_Spend_Cap', 'Max_Spend_Cap', 'Laydown']

for col in table_df.columns:
    if col not in dataTable_cols:
        table_df.drop(columns=col, inplace=True)

table_dict = table_df.to_dict("records")

table_data = {"1":table_dict}
for var in table_data["1"]:
    var['Laydown'] = laydown[var['Channel']].tolist()

### LT

alpha_headers = pd.read_excel(alpha_headers_fp, 'Opt_Header')

LT_header = alpha_headers[alpha_headers['Range'] == brand]
LT_header = LT_header.iloc[:, :-3]

LT_header.drop(columns=['Channel', 'Alpha'], inplace=True)
LT_header.rename(columns={'concat':'Channel', 'LT Adstock':'Carryover', 'LT ROI':'Current_ROI', 'LT Alpha':'Alpha', 'Total Spend':"Current_Budget"}, inplace=True)
LT_header['Max_Spend_Cap'] = LT_header['Current_Budget']*1.5
LT_header['Min_Spend_Cap'] = 0
LT_header['CPU'] = 1

LT_seas_index = pd.read_csv(seas_index_fp)
LT_seas_index.rename(columns={'Unnamed: 0':'Time_Period'}, inplace=True)

for x in laydown.columns.tolist():
    if x not in LT_header['Channel'].tolist() and x != 'Time_Period':
        laydown.drop(columns=[x], inplace=True)

streams = []
for stream in LT_header['Channel']:
    streams.append(str(stream))

print(f"current (incorrect) current budget: {LT_header['Current_Budget']}")

for stream in streams:
    LT_header.loc[LT_header['Channel'] == stream, 'Current_Budget'] = sum(laydown[stream])

LT_header['Current_ROI'] = LT_header['Current_ROI'].replace(0, 0.00001)

LT_header['Beta'] = list(ST_opt_betas_dict.values())

LT_header_dict = LT_header.to_dict("records")

bud = sum(ST_header['Current_Budget'].to_list())

seas_index_table_name = 'seas_index'
ST_db_table_name = 'ST_header'
LT_db_table_name = "LT_header"

seas_index.to_sql(seas_index_table_name, con=engine, index=False, if_exists='replace')
ST_header.to_sql(ST_db_table_name, con=engine, index=False, if_exists='replace')
LT_header.to_sql(LT_db_table_name, con=engine, index=False, if_exists='replace')

query = f'SELECT * FROM "ST_header"'
ST_input_fetched = pd.read_sql(query, con=engine)
query = f'SELECT * FROM "LT_header"'
ST_input_fetched = pd.read_sql(query, con=engine)
query = f'SELECT * FROM "seas_index"'
seas_index_fetched = pd.read_sql(query, con=engine)

ST_header_dict = LT_header.to_dict("records")
LT_header_dict = LT_header.to_dict("records")

# %% --------------------------------------------------------------------------
# 
# -----------------------------------------------------------------------------

@app.route('/optimise', methods = ['POST'])
def optimise():

    if request.method == "POST":
        data = request.json
    print("REACHING OPT METHOD")
    table_id = str(data['tableID'])
    obj_func = data['objectiveValue']
    exh_budget = data['exhaustValue']
    max_budget = int(data['maxValue'])
    num_weeks = 1000
    blend = data['blendValue']
    
    # if 'dates' in data:
    #     print('dates found in data')
    #     start_date = data['dates'][0]
    #     end_date = data['dates'][1]
    #     laydown = laydown[(laydown["Time-Period"] >= start_date) & (laydown["Time-Period"] <= end_date)]
    #     print(start_date)
    #     print(end_date)

    print(f"table id = {table_id}")
    
    # NEED TO ADD HANDLING SO THAT EDITS MADE TO TABLE DATA ARE ADDED TO THE ST_HEADER

    print(f"laydown = {laydown}")
    print(f"CPU = {[entry['CPU'] for entry in ST_header_dict]}")
    global results
    streams = [entry['Channel'] for entry in ST_header_dict]

    if blend.lower() == "blend":
        if obj_func.lower() == "profit":
            results[table_id] = Optimiser.blended_profit_max(ST_input = ST_header_dict, LT_input=LT_header_dict, laydown=laydown, seas_index=seas_index_fetched, exh_budget='yes', max_budget=max_budget, num_weeks=num_weeks)
        elif obj_func.lower() == 'revenue':
            ST_res = list(Optimiser.revenue_max(channel_input = ST_header_dict, laydown = laydown, exh_budget=exh_budget, max_budget=max_budget, num_weeks=num_weeks).values())
            LT_res = list(Optimiser.revenue_max(channel_input = LT_header_dict, laydown = laydown, exh_budget=exh_budget, max_budget=max_budget, num_weeks=num_weeks).values())
            blend_list = list(np.add(ST_res, LT_res))
            blend_res = dict(zip(streams, blend_list))
            results[table_id] = blend_res
        elif obj_func.lower() == 'roi':
            ST_res = list(Optimiser.roi_max(channel_input = ST_header_dict, laydown = laydown, exh_budget=exh_budget, max_budget=max_budget, num_weeks=num_weeks).values())
            LT_res = list(Optimiser.roi_max(channel_input = LT_header_dict, laydown = laydown, exh_budget=exh_budget, max_budget=max_budget, num_weeks=num_weeks).values())
            blend_list = list(np.add(ST_res, LT_res))
            blend_res = dict(zip(streams, blend_list))
            results[table_id] = blend_res
        
        return jsonify(results), 200
    elif blend.lower() == "st":
        if obj_func.lower() == "profit":
            results[table_id] = Optimiser.profit_max(channel_input = ST_header_dict, laydown = laydown, exh_budget=exh_budget, max_budget=max_budget, num_weeks=num_weeks)
        elif obj_func.lower() == 'revenue':
            results[table_id] = Optimiser.revenue_max(channel_input = ST_header_dict, laydown = laydown, exh_budget=exh_budget, max_budget=max_budget)
        elif obj_func.lower() == 'roi':
            results[table_id] = Optimiser.roi_max(channel_input = ST_header_dict, laydown = laydown, exh_budget=exh_budget, max_budget=max_budget)
        return jsonify(results), 200
    elif blend.lower() == "lt":
        if obj_func.lower() == "profit":
            results[table_id] = Optimiser.profit_max(channel_input = LT_header_dict, laydown = laydown, exh_budget=exh_budget, max_budget=max_budget, num_weeks=num_weeks)
        elif obj_func.lower() == 'revenue':
            results[table_id] = Optimiser.revenue_max(channel_input = LT_header_dict, laydown = laydown, exh_budget=exh_budget, max_budget=max_budget)
        elif obj_func.lower() == 'roi':
            results[table_id] = Optimiser.roi_max(channel_input = LT_header_dict, laydown = laydown, exh_budget=exh_budget, max_budget=max_budget)
        print(results)

        return jsonify(results), 200

@app.route('/results_output', methods = ['POST'])
def results_output():

    tab_names = dict(request.json)

    raw_input_data = ST_header.to_dict("records")
    
    current_budget_list = [entry['Current_Budget'] for entry in raw_input_data]
    current_budget_dict = dict(zip(streams, current_budget_list))

    cost_per_list = [float(entry['CPU']) for entry in raw_input_data]
    cost_per_dict = dict(zip(streams, cost_per_list))

    current_budget_laydown_dict = {'Time_Period':list(laydown_dates)}
    for stream in streams:
        current_budget_laydown_dict[stream] = [i * cost_per_dict[stream] for i in list(laydown.fillna(0)[stream])]
    laydown['Time_Period'] = laydown_dates
    laydown.set_index("Time_Period", inplace=True)

    stacked_df2 = pd.DataFrame(current_budget_laydown_dict)
    stacked_df2.set_index('Time_Period', inplace=True)
    stacked_df2 = stacked_df2.stack()
    stacked_df2 = pd.DataFrame(stacked_df2)
    stacked_df2['Scenario'] = "Current"
    stacked_df2['Budget/Revenue'] = "Budget"
    value_col = stacked_df2.pop(0)
    stacked_df2.insert(2, "Value", value_col)
    spend_cap_list = [float(entry['Max_Spend_Cap']) for entry in raw_input_data]
    spend_cap_dict = dict(zip(streams, spend_cap_list))

    carryover_list = [float(entry['Carryover']) for entry in raw_input_data]
    carryover_dict = dict(zip(streams, carryover_list))

    beta_list = [float(entry['Beta']) for entry in raw_input_data]
    beta_dict = dict(zip(streams, beta_list))

    alpha_list = [float(entry['Alpha']) for entry in raw_input_data]
    alpha_dict = dict(zip(streams, alpha_list))

    recorded_impressions = {}
    for x in laydown.columns:
        recorded_impressions[x] = laydown.fillna(0)[x].to_list()

    def rev_per_stream(stream, budget):
                
        cost_per_stream = cost_per_dict.get(stream, 1e-6)  # Set a small non-zero default cost
        allocation = budget / cost_per_stream
        pct_laydown = []
        for x in range(len(recorded_impressions[stream])):
            try:
                pct_laydown.append(recorded_impressions[stream][x]/sum(recorded_impressions[stream]))
            except:
                pct_laydown.append(0)
    
        pam = [pct_laydown[i]*allocation for i in range(len(pct_laydown))]
        carryover_list = []
        carryover_list.append(pam[0])
        for x in range(1,len(pam)):
            carryover_val = pam[x] + carryover_list[x-1]*carryover_dict[stream]
            carryover_list.append(carryover_val)
        rev_list = []
        for x in carryover_list:
            rev_val = beta_dict[stream] * ((1 - np.exp(-alpha_dict[stream]*x)))
            rev_list.append(rev_val)
        total_rev = sum(rev_list)
        infsum = 0
        for n in range(1, 1000):
            infsum += carryover_list[-1] * (1-carryover_dict[stream])**n
        total_rev = total_rev + infsum
        return rev_list

    current_rev_dict = {'Time_Period':list(laydown.index)}

    for stream in streams:
        current_rev_dict[stream] = rev_per_stream(stream, current_budget_dict[stream])

    stacked_df3 = pd.DataFrame(current_rev_dict)
    stacked_df3.set_index('Time_Period', inplace=True)
    stacked_df3 = stacked_df3.stack()
    stacked_df3 = pd.DataFrame(stacked_df3)
    stacked_df3['Scenario'] = "Current"
    stacked_df3['Budget/Revenue'] = "Revenue"
    value_col = stacked_df3.pop(0)
    stacked_df3.insert(2, "Value", value_col)

    stacked_df2.reset_index(inplace=True)
    stacked_df3.reset_index(inplace=True)

    stacked_df2.rename(columns={'level_1':'Channel'}, inplace=True)
    stacked_df3.rename(columns={'level_1':'Channel'}, inplace=True)

    concat_df = pd.concat([stacked_df2, stacked_df3])
    for key, value in results.items():

        opt_budget_dict = value
        print(f"results from optimiser:{results}")
        opt_rev_dict = {'Time_Period':list(laydown.index)}
        for stream in streams:
            opt_rev_dict[stream] = rev_per_stream(stream, current_budget_dict[stream])

        def daily_budget_from_pct_laydown(stream):
        
            pct_laydown = []
            for x in range(len(recorded_impressions[stream])):
                try:
                    pct_laydown.append(recorded_impressions[stream][x]/sum(recorded_impressions[stream]))
                except:
                    pct_laydown.append(0)
            return pct_laydown

        opt_budget_laydown_dict = {'Time_Period':list(laydown.index)}
        for stream in list(streams):
            opt_budget_laydown_dict[stream] = [i * opt_budget_dict[stream] for i in daily_budget_from_pct_laydown(stream)]

        stacked_df4 = pd.DataFrame(opt_budget_laydown_dict)
        stacked_df4.set_index('Time_Period', inplace=True)
        stacked_df4 = stacked_df4.stack()
        stacked_df4 = pd.DataFrame(stacked_df4)
        stacked_df4['Scenario'] = str(tab_names[key])
        stacked_df4['Budget/Revenue'] = "Budget"
        value_col = stacked_df4.pop(0)
        stacked_df4.insert(2, "Value", value_col)

        stacked_df4.reset_index(inplace=True)

        stacked_df4.rename(columns={'level_1':'Channel'}, inplace=True)

        concat_df = pd.concat([concat_df, stacked_df4])

        opt_rev_dict = {'Time_Period':list(laydown.index)}
        for stream in streams:
            opt_rev_dict[stream] = rev_per_stream(stream, opt_budget_dict[stream])

        stacked_df5 = pd.DataFrame(opt_rev_dict)
        stacked_df5.set_index('Time_Period', inplace=True)
        stacked_df5 = stacked_df5.stack()
        stacked_df5 = pd.DataFrame(stacked_df5)
        stacked_df5['Scenario'] = str(tab_names[key])
        stacked_df5['Budget/Revenue'] = "Revenue"
        value_col = stacked_df5.pop(0)
        stacked_df5.insert(2, "Value", value_col)

        stacked_df5.reset_index(inplace=True)

        stacked_df5.rename(columns={'level_1':'Channel'}, inplace=True)

        concat_df = pd.concat([concat_df, stacked_df5])
    
    concat_df['Time_Period'] = pd.to_datetime(concat_df['Time_Period'], format="%Y/%m/%d").dt.date

    print(concat_df.info())
    try:
        concat_df.to_sql('Optimised CSV', engine, if_exists='replace', index=False)
        print("csv uploaded to db successfully")
    except:
        print("csv db upload failed")

    return jsonify({"message":"csv exported successfully"})

@app.route('/chart_data', methods = ['GET'])
def chart_data():
    try:
        conn = engine.connect()
        query = text('SELECT * FROM "Optimised CSV";')

        db_result = conn.execute(query)
        #print(tp_result.fetchall())
        chart_data = []
        col_names = db_result.keys()
        for x in db_result.fetchall():
            a = dict(zip(col_names, x))
            chart_data.append(a)
       
        return jsonify(chart_data)
    
    except SQLAlchemyError as e:
        print('Error executing query:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500

    finally:
        if 'conn' in locals():
            conn.close()

np.random.seed(42)  


def poly_function(x,y,degree):

    x_reshaped = x.reshape(-1, 1)

    poly_features = PolynomialFeatures(degree=degree)

    x_poly = poly_features.fit_transform(x_reshaped)
    model = LinearRegression(fit_intercept=False)

    model.fit(x_poly, y)

    return model.predict(x_poly)


@app.route('/polynomial_data', methods=['GET'])
def polynomial_data():
    poly_x = np.random.uniform(0, 100, 20)
    poly_y = np.random.uniform(2, 4, 20)
    degree = 2
    lobf = poly_function(poly_x, poly_y, degree)
    print(f"lobf={lobf}")
    lobf_dict = dict(zip(poly_x, lobf))
    data = {
        "x": poly_x.tolist(),
        "y": poly_y.tolist(),
        "lobf": dict(sorted(lobf_dict.items()))
    }
    print(data)
    return jsonify(data)

@app.route('/blueprint_results')
@login_required
def blueprint_results():
    return render_template('blueprint_results.html')

@app.route('/date_range', methods = ['GET','POST'])
def date_range():
    start_date = list(laydown_dates)[1]
    print(start_date)
    end_date = list(laydown_dates)[-1]
    print(end_date)
    return jsonify({"startDate":start_date, "endDate":end_date})

@app.route('/blueprint')
@login_required
def blueprint():
    print(laydown_dates)
    return render_template('blueprint.html', current_user = current_user)

@app.route('/get_table_ids', methods = ['GET'])
def get_table_ids():
    table_ids = list(table_data.keys())
    return jsonify({"success": True, "tableIds":table_ids})

@app.route('/table_ids_sync', methods = ['POST'])
def table_ids_sync():
    
    try:
       
        received_data = request.get_json()
        received_table_ids = received_data.get('tableIDs', [])
        #parsed_data = parse_qs(received_data)
        received_table_ids = list(map(str, received_data['tableIDs']))

        print(f"received table ids: {received_table_ids}")

        for table_id in list(table_data.keys()):
            if table_id not in received_table_ids:
                
                del table_data[table_id]
                print(f"deleted tab: {table_id}")

        return jsonify({'success': True, 'message': 'Table data updated successfully'})

    except KeyError:
        print("tableIDs not found in ajax post request.")
        return jsonify({'status': 'error', 'message': 'Invalid request data'}), 400
    except Exception as e:
    
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/sync_tab_counter', methods = ['GET'])
def sync_tab_counter():
    last_number = list(table_data.keys())[-1]
    return jsonify({'lastNumber': last_number})

@app.route('/create_copy', methods = ['POST'])
def create_copy():
    global table_data

    tableID = str(request.form.get('tableID'))
    channel_dict = ST_header.to_dict("records")
    for var in channel_dict:
        var['Laydown'] = laydown[var['Channel']].tolist()
    if tableID not in table_data.keys():
        table_data[tableID] = table_dict
    print(table_data.keys())
    return jsonify({"success": True, "table_id": tableID})

@app.route('/channel', methods = ['GET', 'PUT'])
def channel():
    print("reaching /channel")
    if request.method == 'GET':
        print("getting")
        return jsonify(table_data)

@app.route('/channel_delete', methods = ['POST'])
def channel_delete():
    deleted_tab = str(request.json.get("tabID"))
    print(f"deleted tab: {deleted_tab}")
    table_data.pop(deleted_tab)
    return jsonify({"success":"tab removed succesfully"})

@app.route('/channel_main', methods = ['GET'])
def channel_main():
    print(table_data.keys())    
    return jsonify(table_data)

@app.route('/')
def welcome_page():
    print(current_user)
    return render_template('Welcome.html', current_user=current_user)

# Get request required pending login db sorted
@app.route('/home', methods=['GET', 'POST'])

def home():
    return render_template('Home.html', current_user=current_user)

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('psw')

        configurations = load_configurations()

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=True)  # Use Flask-Login's login_user
            print(f"User {username} logged in successfully.")
            print(current_user.user_info)
            return redirect(url_for('blueprint'))
        else:
            print(f"Failed login attempt for user {username}.")
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

def load_configurations():
    try:
        with open('data\config.json', 'r') as config_file:
            configurations = json.load(config_file)
    except (FileNotFoundError, json.JSONDecodeError):
        # Handle the case when the file doesn't exist or is empty
        configurations = {}
        
def save_configurations(configurations):
    with open('config.json', 'w') as config_file:
        json.dump(configurations, config_file, indent=2)

    return configurations
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('/home'))

if __name__ == '__main__':
     with app.app_context():

        db.create_all()
        for user in user_data:
            add_user(user)
        app.run(host="0.0.0.0", debug=True)