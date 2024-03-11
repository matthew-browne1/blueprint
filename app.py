
# %% --------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
from flask import Flask, render_template, send_file, jsonify, request, url_for, redirect, flash, session, current_app
from flask_sse import sse
from flask_socketio import SocketIO, emit
import numpy as np
import pandas as pd
import seaborn as sns
import json
import os
import sys
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from urllib.parse import parse_qs
# from pyomo_opt import Optimiser
from sqlalchemy import create_engine, text, Column, DateTime, Integer, func
from sqlalchemy.orm import Session, declarative_base
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import urllib.parse
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import secrets
import logging
from logging.handlers import RotatingFileHandler
from pyomo.environ import *
from pyomo.opt import SolverFactory
import statsmodels as sm
from scipy.optimize import minimize
from optimiser import Optimise
from pyomo_opt import Optimiser
from io import BytesIO
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from multiprocessing import Manager, freeze_support

app = Flask(__name__)
socketio = SocketIO(app)

#executor = ProcessPoolExecutor()

### TODO: WRITE A CLASS WHICH FETCHES CORRECT DB DETAILS

azure_host = "blueprintalpha.postgres.database.azure.com"
azure_user = "bptestadmin"
azure_password = "Password!"
azure_database = "postgres" 

ra_server_uri = 'postgresql://postgres:'+urllib.parse.quote_plus("Gde3400@@")+'@192.168.1.2:5432/CPW Blueprint'

# Create the new PostgreSQL URI for Azure
azure_db_uri = f"postgresql://{azure_user}:{urllib.parse.quote_plus(azure_password)}@{azure_host}:5432/{azure_database}"

app.config['SQLALCHEMY_DATABASE_URI'] = ra_server_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secrets.token_hex()
app.config['SESSION_COOKIE_SECURE'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['DEBUG'] = True

engine = create_engine(ra_server_uri)

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
    table_data = db.Column(db.Text, nullable=False)

# class DatabaseHandler(logging.Handler):
#     def emit(self, record):
#         try:
#             message = self.format(record)
#             db.session.add(Log(message=message))
#             db.session.commit()
#         except Exception:
#             self.handleError(record)

# database_handler = DatabaseHandler()
# database_handler.setLevel(logging.DEBUG)
# app.logger.addHandler(database_handler)

class PyomoLogHandler(logging.Handler):
    def emit(self, record):
        log_message = self.format(record)
        db.session.add(Log(message=log_message))
        db.session.commit()

pyomo_logger = logging.getLogger('pyomo')
pyomo_logger.addHandler(PyomoLogHandler())

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    message = db.Column(db.String, nullable=False)

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

        app.logger.info(f"User '{user_data['username']}' added successfully.")
    else:
        app.logger.info(f"User '{user_data['username']}' already exists.")


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
    table_data_json = json.dumps(table_data)

    table_ids_str = ','.join(map(str, current_table_ids))

    # Check if a snapshot with the same name already exists for the current user
    existing_snapshot = Snapshot.query.filter_by(name=snapshot_name, user_id=user_id).first()

    if existing_snapshot:
        # Update the existing snapshot
        existing_snapshot.content = content
        existing_snapshot.table_ids = table_ids_str
        existing_snapshot.table_data = table_data_json
    else:
        # Create a new snapshot
        new_snapshot = Snapshot(name=snapshot_name, content=content, table_ids=table_ids_str, user_id=user_id, table_data=table_data_json)
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
    table_data_json = json.dumps(table_data)

    table_ids_str = ','.join(map(str, current_table_ids))

    app.logger.info(f"snapshot id = {snapshot_id}")
    app.logger.info(f"user id = {user_id}")

    existing_snapshot = Snapshot.query.filter_by(id=snapshot_id, user_id=user_id).first()
    existing_snapshot.content = content
    existing_snapshot.table_ids = table_ids_str
    existing_snapshot.table_data = table_data_json

    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/load_snapshot')
@login_required
def load_snapshot():
    global table_data
    user_id = current_user.id
    snapshot = Snapshot.query.filter_by(user_id=user_id).first()
    table_data = json.loads(snapshot.table_data)
    content_list = snapshot.content
    table_ids_list = snapshot.table_ids
    app.logger.info(table_data.keys())    
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
            'DT_RowId': save.id,  
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
            app.logger.info(table_data.keys())    
            return jsonify({'content': content_list, 'table_ids': table_ids_list})

results = {}

seas_index_table_name = 'seas_index'
ST_db_table_name = 'ST_header'
LT_db_table_name = "LT_header"
laydown_table_name = "laydown"

# seas_index.to_sql(seas_index_table_name, con=engine, index=False, if_exists='replace')
# ST_header.to_sql(ST_db_table_name, con=engine, index=False, if_exists='replace')
# LT_header.to_sql(LT_db_table_name, con=engine, index=False, if_exists='replace')
# laydown.to_sql(laydown_table_name, con=engine, index=False, if_exists='replace')

# laydown_query = 'select * FROM "laydown"'
# laydown_fetched = pd.read_sql(laydown_query, con=engine)
# ST_query = f'SELECT * FROM "ST_header"'
# ST_input_fetched = pd.read_sql(ST_query, con=engine)
# LT_query = f'SELECT * FROM "LT_header"'
# LT_input_fetched = pd.read_sql(LT_query, con=engine)
# si_query = f'SELECT * FROM "seas_index"'
# seas_index_fetched = pd.read_sql(si_query, con=engine)

# bud = sum(ST_input_fetched['Current_Budget'].to_list())
# streams = []
# for stream in ST_input_fetched['Channel']:
#     streams.append(str(stream))

# laydown = laydown_fetched
# ST_header_dict = ST_input_fetched.to_dict("records")
# LT_header_dict = LT_input_fetched.to_dict("records")
# seas_index = seas_index_fetched.to_dict("records")

# laydown_dates = laydown['Time_Period']

# ### TABLE DATA ###

# table_df = ST_input_fetched.copy()

# dataTable_cols = ['Channel', 'Carryover', 'Alpha', 'Beta', 'Current_Budget', 'Min_Spend_Cap', 'Max_Spend_Cap', 'Laydown']

# for col in table_df.columns:
#     if col not in dataTable_cols:
#         table_df.drop(columns=col, inplace=True)

# table_dict = table_df.to_dict("records")

# table_data = {"1":table_dict}
# for var in table_data["1"]:
#     var['Laydown'] = laydown[var['Channel']].tolist()


# seas_index = seas_index_fetched




num_weeks = 1000

def prep_rev_per_stream(stream, budget, cost_per_dict, carryover_dict, alpha_dict, beta_dict):
    cost_per_stream = cost_per_dict.get(stream, 1e-6)  # Set a small non-zero default cost
    #print("cpu:")
    #print(cost_per_stream)
    allocation = budget / cost_per_stream
    #print('allocation:')
    #print(allocation)
    pct_laydown = []
    for x in range(len(recorded_impressions[stream])):
        try:
            pct_laydown.append(recorded_impressions[stream][x] / sum(recorded_impressions[stream]))
        except:
            pct_laydown.append(0)
    #print("pct_laydown:")
    #print(pct_laydown)
    pam = [pct_laydown[i] * allocation for i in range(len(pct_laydown))]
    carryover_list = []
    carryover_list.append(pam[0])
    for x in range(1, len(pam)):
        carryover_val = pam[x] + carryover_list[x - 1] * carryover_dict[stream]
        carryover_list.append(carryover_val)
    #print("carryover list:")
    #print(carryover_list)
    rev_list = []
    for x in carryover_list:
        rev_val = beta_dict[stream] * (1 - np.exp(-alpha_dict[stream] * x))
        rev_list.append(rev_val)
    #print("rev list")
    #print(rev_list)
    indexed_vals = [a * b for a, b in zip(rev_list, seas_dict[stream])]
    total_rev = sum(indexed_vals)
    infsum = 0
    for n in range(1, num_weeks):
        infsum += carryover_list[-1] * (1 - carryover_dict[stream]) ** n
    total_rev = total_rev + infsum
    return rev_list

def prep_total_rev_per_stream(stream, budget):
    ST_rev = prep_rev_per_stream(stream, budget, ST_cost_per_dict, ST_carryover_dict, ST_alpha_dict, ST_beta_dict)
    LT_rev = prep_rev_per_stream(stream, budget, LT_cost_per_dict, LT_carryover_dict, LT_alpha_dict, LT_beta_dict)
    total_rev = ST_rev + LT_rev
    return total_rev

results = {}

ST_header = pd.read_sql_table('All_Channel_Inputs', engine)
# Show column headers without underscores!
ST_header.columns = [x.replace("_", " ") for x in ST_header.columns.tolist()]

laydown = pd.read_sql_table('All_Laydown', engine)
laydown.fillna(0)
laydown.columns
seas_index = pd.read_sql_table('All_Index', engine)

for x in laydown.columns.tolist():
    if x not in ST_header['Opt Channel'].tolist() and x != 'Date':
        #print(x)
        laydown.drop(columns=[x], inplace=True)

streams = []
for stream in ST_header['Opt Channel']:
    streams.append(str(stream))

laydown_dates = laydown['Date']


for stream in streams:
    ST_header.loc[ST_header['Opt Channel'] == stream, 'Current Budget'] = sum(laydown[stream])

ST_header['ST Revenue'] = ST_header['Current Budget'] * ST_header['ST Current ROI']

ST_header_dict = ST_header.to_dict("records")

ST_cost_per_list = [float(entry['CPU']) for entry in ST_header_dict]
ST_cost_per_dict = dict(zip(streams, ST_cost_per_list))

ST_carryover_list = [float(entry['ST Carryover']) for entry in ST_header_dict]
ST_carryover_dict = dict(zip(streams, ST_carryover_list))

ST_beta_dict = dict(zip(streams, [1] * len(streams)))

ST_alpha_list = [float(entry['ST Alpha']) for entry in ST_header_dict]
ST_alpha_dict = dict(zip(streams, ST_alpha_list))
raw_input_data = ST_header.to_dict("records")
current_budget_list = [entry['Current Budget'] for entry in raw_input_data]
current_budget_dict = dict(zip(streams, current_budget_list))

seas_dict = seas_index

recorded_impressions = {}
for x in laydown.columns:
    recorded_impressions[x] = laydown.fillna(0)[x].to_list()

beta_calc_rev_dict_ST = {'Date': list(laydown.Date)}
for stream in list(streams):
    beta_calc_rev_dict_ST[stream] = prep_rev_per_stream(stream, current_budget_dict[stream], ST_cost_per_dict,
                                                   ST_carryover_dict, ST_alpha_dict, ST_beta_dict)
    sum(beta_calc_rev_dict_ST[stream])
beta_calc_df = pd.DataFrame(beta_calc_rev_dict_ST)[list(streams)].sum().reset_index()
beta_calc_df.columns = ['Opt Channel', 'Calc_Rev']
beta_calc_df = pd.merge(beta_calc_df, ST_header[['Opt Channel', 'ST Revenue']], on='Opt Channel')
beta_calc_df['ST Beta'] = np.where(beta_calc_df['Calc_Rev'] == 0, 0,
                                   beta_calc_df['ST Revenue'] / beta_calc_df['Calc_Rev'])
ST_opt_betas_dict = dict(zip(streams, beta_calc_df['ST Beta'].tolist()))

ST_header['ST Beta'] = list(ST_opt_betas_dict.values())

ST_header_dict = ST_header.to_dict("records")

max_spend_cap = sum(ST_header['Max Spend Cap'])

print(max_spend_cap)

LT_header = pd.read_sql_table('All_Channel_Inputs', engine)
# Show column headers without underscores!
LT_header.columns = [x.replace("_", " ") for x in LT_header.columns.tolist()]

laydown = pd.read_sql_table('All_Laydown', engine)
laydown.fillna(0)
laydown.columns
seas_index = pd.read_sql_table('All_Index', engine)

for x in laydown.columns.tolist():
    if x not in LT_header['Opt Channel'].tolist() and x != 'Date':
        #print(x)
        laydown.drop(columns=[x], inplace=True)

streams = []
for stream in LT_header['Opt Channel']:
    streams.append(str(stream))

laydown_dates = laydown['Date']


for stream in streams:
    LT_header.loc[LT_header['Opt Channel'] == stream, 'Current Budget'] = sum(laydown[stream])

LT_header['LT Revenue'] = LT_header['Current Budget'] * LT_header['LT Current ROI']

LT_header_dict = LT_header.to_dict("records")

LT_cost_per_list = [float(entry['CPU']) for entry in LT_header_dict]
LT_cost_per_dict = dict(zip(streams, LT_cost_per_list))

LT_carryover_list = [float(entry['LT Carryover']) for entry in LT_header_dict]
LT_carryover_dict = dict(zip(streams, LT_carryover_list))

LT_beta_dict = dict(zip(streams, [1] * len(streams)))

LT_alpha_list = [float(entry['LT Alpha']) for entry in LT_header_dict]
LT_alpha_dict = dict(zip(streams, LT_alpha_list))
raw_input_data = LT_header.to_dict("records")
current_budget_list = [entry['Current Budget'] for entry in raw_input_data]
current_budget_dict = dict(zip(streams, current_budget_list))

seas_dict = seas_index

recorded_impressions = {}
for x in laydown.columns:
    recorded_impressions[x] = laydown.fillna(0)[x].to_list()

beta_calc_rev_dict_LT = {'Date': list(laydown.Date)}
#stream = 'ATLTVSuper FoodsBSBakersDog'
for stream in list(streams):
    beta_calc_rev_dict_ST[stream] = prep_rev_per_stream(stream, current_budget_dict[stream], LT_cost_per_dict,
                                                   LT_carryover_dict, LT_alpha_dict, LT_beta_dict)
    sum(beta_calc_rev_dict_ST[stream])
beta_calc_df = pd.DataFrame(beta_calc_rev_dict_ST)[list(streams)].sum().reset_index()
beta_calc_df.columns = ['Opt Channel', 'Calc_Rev']
beta_calc_df = pd.merge(beta_calc_df, LT_header[['Opt Channel', 'LT Revenue']], on='Opt Channel')
beta_calc_df['LT Beta'] = np.where(beta_calc_df['Calc_Rev'] == 0, 0,
                                   beta_calc_df['LT Revenue'] / beta_calc_df['Calc_Rev'])
LT_opt_betas_dict = dict(zip(streams, beta_calc_df['LT Beta'].tolist()))

LT_header['LT Beta'] = list(LT_opt_betas_dict.values())
ST_header['LT Beta'] = list(LT_opt_betas_dict.values())

LT_header_dict = LT_header.to_dict("records")

table_df = ST_header.copy()

dataTable_cols = ['Region', 'Brand', 'Channel', 'Current Budget', 'Min Spend Cap', 'Max Spend Cap',
                  #'ST Carryover', 'ST Alpha', 'ST Beta', 'LT Carryover', 'LT Alpha', 'LT Beta',
                  'Laydown']

for col in table_df.columns:
    if col not in dataTable_cols:
        table_df.drop(columns=col, inplace=True)

table_df.insert(0, 'row_id', range(1, len(table_df)+1))
table_dict = table_df.to_dict("records")
for var in table_dict:
    var['Laydown'] = laydown[var['Channel']+"_"+var['Region']+"_"+var['Brand']].tolist()

table_data = {"1": deepcopy(table_dict)}
bud = sum(ST_header['Current Budget'].to_list())

# %% --------------------------------------------------------------------------
# 
# -----------------------------------------------------------------------------

inputs_per_result = {}

def optimise(ST_input, LT_input, laydown, seas_index, blend, obj_func, max_budget, exh_budget, ftol, ssize, table_id):
    global results

    result = Optimise.blended_profit_max_scipy(ST_input=ST_input, LT_input=LT_input, laydown=laydown, seas_index=seas_index, return_type=blend, objective_type=obj_func, max_budget=max_budget, exh_budget=exh_budget, method='SLSQP', ftol=ftol, ssize=ssize)

    # result = Optimiser.profit_max(channel_input=ST_header_dict, laydown=laydown, seas_index=seas_index, max_budget=max_budget, exh_budget=exh_budget, num_weeks=1000)
    try:
        with app.app_context():
            print(f"Task completed: {result}")
            results[table_id] = result
            print(f"total results: {results}")
            socketio.emit('opt_complete', {'data':table_id})
    except Exception as e:
        with app.app_context():
            print(f"Error in task callback: {str(e)}")
            socketio.emit('opt_complete', {'data':table_id})

@socketio.on('optimise')
def run_optimise(dataDict):
    data = dict(dataDict.get('dataToSend'))
    global inputs_per_result

    ST_header_copy = deepcopy(ST_header)
    LT_header_copy = deepcopy(LT_header)
    laydown_copy = deepcopy(laydown)
    seas_index_copy = deepcopy(seas_index)

    app.logger.info("REACHING OPT METHOD")
    table_id = str(data['tableID'])
    obj_func = data['objectiveValue']
    exh_budget = data['exhaustValue']
    max_budget = int(data['maxValue'])
    ftol_input = float(data['ftolValue'])
    ssize_input = float(data['ssizeValue'])
    num_weeks = 1000
    blend = data['blendValue']
    disabled_rows = list(data['disabledRows'])
    print(f"disabled row ids: {disabled_rows}")
    
    current_table_df = pd.DataFrame.from_records(deepcopy(table_data[table_id]))
    removed_rows_df = current_table_df[current_table_df.row_id.isin(disabled_rows)].copy()
    removed_rows_df['Opt Channel'] = removed_rows_df.apply(lambda row: '_'.join([str(row['Channel']), str(row['Region']), str(row['Brand'])]), axis=1)

    disabled_opt_channels = list(removed_rows_df['Opt Channel'])

    for col in current_table_df.columns:
        ST_header_copy[col] = current_table_df[col]
        LT_header_copy[col] = current_table_df[col]

    ST_header_copy = ST_header_copy[~(ST_header_copy['Opt Channel'].isin(disabled_opt_channels))]
    LT_header_copy = LT_header_copy[~(LT_header_copy['Opt Channel'].isin(disabled_opt_channels))]

    laydown_copy = laydown_copy.drop(columns=disabled_opt_channels, errors='ignore')
    seas_index_copy = seas_index_copy.drop(columns=disabled_opt_channels, errors='ignore')

    ST_input = ST_header_copy.to_dict('records')
    LT_input = LT_header_copy.to_dict('records')

    # if 'dates' in data:
    #     app.logger.info('dates found in data')
    #     start_date = data['dates'][0]
    #     end_date = data['dates'][1]
    #     laydown = laydown[(laydown["Time-Period"] >= start_date) & (laydown["Time-Period"] <= end_date)]
    #     app.logger.info(start_date)
    #     app.logger.info(end_date)

    print(f"retrieved from the server: table id = {table_id}, objective function = {obj_func}, exhaust budget = {exh_budget}, max budget = {max_budget}, blended = {blend}")
    
    # NEED TO ADD HANDLING SO THAT EDITS MADE TO TABLE DATA ARE ADDED TO THE ST_HEADER

    print(f"laydown = {laydown_copy}")
    print(f"CPU = {[entry['CPU'] for entry in ST_input]}")

    inputs_dict = {'ST_input':ST_input,'LT_input':LT_input,'laydown':laydown_copy,'seas_index':seas_index_copy}
    
    print(f"inputs per result: {inputs_per_result}")
    inputs_per_result[table_id] = deepcopy(inputs_dict)

    min_spend_cap_list = [float(entry['Min Spend Cap']) for entry in ST_input]
    min_spend_cap_dict = dict(zip(streams, min_spend_cap_list))

    print(min_spend_cap_dict)
    socketio.start_background_task(target=optimise, ST_input=ST_input, LT_input=LT_input, laydown=laydown_copy, seas_index=seas_index_copy, blend=blend, obj_func=obj_func, max_budget=max_budget, exh_budget=exh_budget, ftol=ftol_input, ssize=ssize_input, table_id = table_id)

    return jsonify({'status': 'Task started in the background'})


@app.route('/results_output', methods = ['POST'])
def results_output():
    global inputs_per_result
    tab_names = dict(request.json)
    print(tab_names)
    #print(inputs_per_result)
    output = create_output(results_dict=results, inputs_per_result=inputs_per_result, tab_names=tab_names, include_current=True)
    output.to_csv('output.csv')

    try:
        output.to_sql('Optimised CSV', engine, if_exists='replace', index=False)
        app.logger.info("csv uploaded to db successfully")
    except:
        app.logger.info("csv db upload failed")

    return jsonify({"message":"csv exported successfully"})

def create_output(results_dict, inputs_per_result, tab_names, include_current=True):

    def output_rev_per_stream(stream, budget, cost_per_dict, carryover_dict, alpha_dict, beta_dict, recorded_impressions, seas_dict, num_weeks):
        cost_per_stream = cost_per_dict.get(stream, 1e-6)  # Set a small non-zero default cost
        allocation = budget / cost_per_stream

        pct_laydown = np.array(recorded_impressions[stream]) / sum(recorded_impressions[stream]) if sum(recorded_impressions[stream]) != 0 else 0
        # print(sum(pct_laydown))

        pam = pct_laydown * allocation
        # print(sum(pam))
        # carryover_list = np.zeros_like(pam)
        # carryover_list[0] = pam[0]
        # print(stream)
        carryover_list = Optimise.adstock(pam, carryover_dict[stream])
        # print(sum(carryover_list))
        # for i in range(1, len(pam)):
        #     carryover_val = pam[i] + carryover_list[i - 1] * carryover_dict[stream]
        #     carryover_list[i] = carryover_val
        # print(sum(carryover_list))
        # print("carryover_list:", carryover_list)

        rev_list = Optimise.dim_returns(alpha_dict[stream], beta_dict[stream], carryover_list)
        # rev_list = beta_dict[stream] * ((1 - np.exp(-alpha_dict[stream] * carryover_list)))

        # print(stream)
        # print(sum(rev_list))
        # print("beta dict:", beta_dict[stream])

        indexed_vals = rev_list * seas_dict[stream]
        # total_rev = np.sum(indexed_vals)
        # print(total_rev)

        # infsum = np.sum(carryover_list[-1] * carryover_dict[stream] ** np.arange(1, num_weeks))
        #
        # total_rev += infsum
        return indexed_vals

    global ST_header, laydown_dates, laydown, seas_index, streams, ST_header_dict, LT_header_dict
    concat_df = pd.DataFrame()
    raw_input_data = ST_header.to_dict("records")

    current_budget_list = [entry['Current Budget'] for entry in raw_input_data]
    current_budget_dict = dict(zip(streams, current_budget_list))

    cost_per_list = [float(entry['CPU']) for entry in raw_input_data]
    cost_per_dict = dict(zip(streams, cost_per_list))

    current_budget_laydown_dict = {'Date': list(laydown_dates)}
    for stream in streams:
        current_budget_laydown_dict[stream] = [i * cost_per_dict[stream] for i in list(laydown.fillna(0)[stream])]
    laydown['Date'] = laydown_dates.tolist()
    laydown.set_index("Date", inplace=True)

    stacked_df2 = pd.DataFrame(current_budget_laydown_dict)
    stacked_df2.set_index('Date', inplace=True)
    stacked_df2 = stacked_df2.stack()
    stacked_df2 = pd.DataFrame(stacked_df2)
    stacked_df2['Scenario'] = "Current"
    stacked_df2['Budget/Revenue'] = "Budget"
    value_col = stacked_df2.pop(0)
    stacked_df2.insert(2, "Value", value_col)
    spend_cap_list = [float(entry['Max Spend Cap']) for entry in raw_input_data]

    ST_cost_per_list = [float(entry['CPU']) if 'CPU' in entry else 0.0 for entry in ST_header_dict]
    ST_cost_per_dict = dict(zip(streams, ST_cost_per_list))
    LT_cost_per_list = [float(entry['CPU']) if 'CPU' in entry else 0.0 for entry in LT_header_dict]
    LT_cost_per_dict = dict(zip(streams, LT_cost_per_list))

    ST_carryover_list = [float(entry['ST Carryover']) if 'ST Carryover' in entry else 0.0 for entry in ST_header_dict]
    ST_carryover_dict = dict(zip(streams, ST_carryover_list))
    LT_carryover_list = [float(entry['LT Carryover']) if 'LT Carryover' in entry else 0.0 for entry in LT_header_dict]
    LT_carryover_dict = dict(zip(streams, LT_carryover_list))

    ST_alpha_list = [float(entry['ST Alpha']) if 'ST Alpha' in entry else 0.0 for entry in ST_header_dict]
    ST_alpha_dict = dict(zip(streams, ST_alpha_list))
    LT_alpha_list = [float(entry['LT Alpha']) if 'LT Alpha' in entry else 0.0 for entry in LT_header_dict]
    LT_alpha_dict = dict(zip(streams, LT_alpha_list))

    ST_beta_list = [float(entry['ST Beta']) if 'ST Beta' in entry and not pd.isna(entry['ST Beta']) and entry['ST Beta'] != np.inf else 0.0 for entry in ST_header_dict]
    ST_beta_dict = dict(zip(streams, ST_beta_list))
    LT_beta_list = [float(entry['LT Beta']) if 'LT Beta' in entry and not pd.isna(entry['LT Beta']) and entry['LT Beta'] != np.inf else 0.0 for entry in LT_header_dict]
    LT_beta_dict = dict(zip(streams, LT_beta_list))

    seas_dict = seas_index

    recorded_impressions = {}
    for x in laydown.columns:
        recorded_impressions[x] = laydown.fillna(0)[x].to_list()

    if include_current:
        current_rev_dict_ST = {'Date': list(laydown.index)}
        current_rev_dict_LT = {'Date': list(laydown.index)}
        
        for stream in list(streams):
            # current_rev_dict[stream] = total_rev_per_stream(stream, current_budget_dict[stream])

            current_rev_dict_ST[stream] = output_rev_per_stream(stream, current_budget_dict[stream], ST_cost_per_dict,
                                                         ST_carryover_dict, ST_alpha_dict, ST_beta_dict, recorded_impressions, seas_dict, num_weeks=1000)
            current_rev_dict_LT[stream] = output_rev_per_stream(stream, current_budget_dict[stream], LT_cost_per_dict,
                                                         LT_carryover_dict, LT_alpha_dict, LT_beta_dict, recorded_impressions, seas_dict, num_weeks=1000)

        stacked_df3 = pd.DataFrame(current_rev_dict_ST)
        stacked_df3.set_index('Date', inplace=True)
        stacked_df3 = stacked_df3.stack()
        stacked_df3 = pd.DataFrame(stacked_df3)
        stacked_df3['Scenario'] = "Current"
        stacked_df3['Budget/Revenue'] = "ST Revenue"
        value_col = stacked_df3.pop(0)
        stacked_df3.insert(2, "Value", value_col)

        stacked_df2.reset_index(inplace=True)
        stacked_df3.reset_index(inplace=True)

        stacked_df2.rename(columns={'level_1': 'Opt Channel'}, inplace=True)
        stacked_df3.rename(columns={'level_1': 'Opt Channel'}, inplace=True)

        concat_df = pd.concat([stacked_df2, stacked_df3])

        stacked_df3 = pd.DataFrame(current_rev_dict_LT)
        stacked_df3.set_index('Date', inplace=True)
        stacked_df3 = stacked_df3.stack()
        stacked_df3 = pd.DataFrame(stacked_df3)
        stacked_df3['Scenario'] = "Current"
        stacked_df3['Budget/Revenue'] = "LT Revenue"
        value_col = stacked_df3.pop(0)
        stacked_df3.insert(2, "Value", value_col)

        stacked_df2.reset_index(inplace=True)
        stacked_df3.reset_index(inplace=True)

        stacked_df2.rename(columns={'level_1': 'Opt Channel'}, inplace=True)
        stacked_df3.rename(columns={'level_1': 'Opt Channel'}, inplace=True)

        concat_df = pd.concat([concat_df, stacked_df3])
        fill_df = concat_df.copy()

    for key, value in results_dict.items():

        table_id = key
        opt_budget_dict = value
        included_streams = list(opt_budget_dict.keys())
        print(f"included streams list: {included_streams}")

        curr_ST_input = inputs_per_result[table_id]['ST_input']
        curr_LT_input = inputs_per_result[table_id]['LT_input']

        curr_ST_cost_per_list = [float(entry['CPU']) if 'CPU' in entry else 0.0 for entry in curr_ST_input]
        curr_ST_cost_per_dict = dict(zip(included_streams, curr_ST_cost_per_list))
        curr_LT_cost_per_list = [float(entry['CPU']) if 'CPU' in entry else 0.0 for entry in curr_LT_input]
        curr_LT_cost_per_dict = dict(zip(included_streams, curr_LT_cost_per_list))

        curr_ST_carryover_list = [float(entry['ST Carryover']) if 'ST Carryover' in entry else 0.0 for entry in curr_ST_input]
        curr_ST_carryover_dict = dict(zip(included_streams, curr_ST_carryover_list))
        curr_LT_carryover_list = [float(entry['LT Carryover']) if 'LT Carryover' in entry else 0.0 for entry in curr_LT_input]
        curr_LT_carryover_dict = dict(zip(included_streams, curr_LT_carryover_list))

        curr_ST_alpha_list = [float(entry['ST Alpha']) if 'ST Alpha' in entry else 0.0 for entry in curr_ST_input]
        curr_ST_alpha_dict = dict(zip(included_streams, curr_ST_alpha_list))
        curr_LT_alpha_list = [float(entry['LT Alpha']) if 'LT Alpha' in entry else 0.0 for entry in curr_LT_input]
        curr_LT_alpha_dict = dict(zip(included_streams, curr_LT_alpha_list))

        curr_ST_beta_list = [float(entry['ST Beta']) if 'ST Beta' in entry and not pd.isna(entry['ST Beta']) and entry['ST Beta'] != np.inf else 0.0 for entry in curr_ST_input]
        curr_ST_beta_dict = dict(zip(included_streams, curr_ST_beta_list))
        curr_LT_beta_list = [float(entry['LT Beta']) if 'LT Beta' in entry and not pd.isna(entry['LT Beta']) and entry['LT Beta'] != np.inf else 0.0 for entry in curr_LT_input]
        curr_LT_beta_dict = dict(zip(included_streams, curr_LT_beta_list))
        
        # print(f"results from optimiser:{results}")

        # for stream in streams:
        #     opt_rev_dict[stream] = rev_per_stream(stream, opt_budget_dict[stream])
        curr_laydown = inputs_per_result[table_id]['laydown']
        curr_seas_dict = inputs_per_result[table_id]['seas_index']

        curr_budget_laydown_dict = {'Date': list(laydown_dates)}
        for stream in included_streams:
            curr_budget_laydown_dict[stream] = [i * cost_per_dict[stream] for i in list(curr_laydown.fillna(0)[stream])]
        curr_laydown['Date'] = laydown_dates.tolist()
        curr_laydown.set_index("Date", inplace=True)

        curr_recorded_impressions = {}
        for x in curr_laydown.columns:
            curr_recorded_impressions[x] = curr_laydown.fillna(0)[x].to_list()

        def daily_budget_from_pct_laydown(stream):

            pct_laydown = []
            for x in range(len(curr_recorded_impressions[stream])):
                try:
                    pct_laydown.append(curr_recorded_impressions[stream][x] / sum(curr_recorded_impressions[stream]))
                except:
                    pct_laydown.append(0)
            return pct_laydown

        opt_budget_laydown_dict = {'Date': list(curr_laydown.index)}
        for stream in included_streams:
            opt_budget_laydown_dict[stream] = [i * opt_budget_dict[stream] for i in daily_budget_from_pct_laydown(stream)]

        stacked_df4 = pd.DataFrame(opt_budget_laydown_dict)
        stacked_df4.set_index('Date', inplace=True)
        stacked_df4 = stacked_df4.stack()
        stacked_df4 = pd.DataFrame(stacked_df4)
        stacked_df4.reset_index(inplace=True)

        stacked_df4.rename(columns={'level_1': 'Opt Channel'}, inplace=True)

        stacked_df4 = pd.merge(fill_df[["Date", "Opt Channel"]].drop_duplicates(), stacked_df4, on = ["Date", "Opt Channel"], how="left").fillna(0)
        stacked_df4['Scenario'] = tab_names[key]
        stacked_df4['Budget/Revenue'] = "Budget"
        value_col = stacked_df4.pop(0)
        stacked_df4.insert(2, "Value", value_col)
        concat_df = pd.concat([concat_df, stacked_df4])

        opt_rev_dict_ST = {'Date': list(curr_laydown.index)}
        opt_rev_dict_LT = {'Date': list(curr_laydown.index)}
        for inc_stream in included_streams:

            opt_rev_dict_ST[inc_stream] = output_rev_per_stream(inc_stream, opt_budget_dict[inc_stream], curr_ST_cost_per_dict, curr_ST_carryover_dict, curr_ST_alpha_dict, curr_ST_beta_dict, curr_recorded_impressions, curr_seas_dict, num_weeks=1000)
            opt_rev_dict_LT[inc_stream] = output_rev_per_stream(inc_stream, current_budget_dict[inc_stream], curr_LT_cost_per_dict, curr_LT_carryover_dict, curr_LT_alpha_dict, curr_LT_beta_dict, curr_recorded_impressions, curr_seas_dict, num_weeks=1000)
       
        stacked_df5 = pd.DataFrame(opt_rev_dict_ST)
        stacked_df5.set_index('Date', inplace=True)
        stacked_df5 = stacked_df5.stack()
        stacked_df5 = pd.DataFrame(stacked_df5)
        
        stacked_df5.reset_index(inplace=True)

        stacked_df5.rename(columns={'level_1': 'Opt Channel'}, inplace=True)
        stacked_df5 = pd.merge(fill_df[["Date", "Opt Channel"]].drop_duplicates(), stacked_df5, on = ["Date", "Opt Channel"], how="left").fillna(0)
        stacked_df5['Scenario'] = tab_names[key]
        stacked_df5['Budget/Revenue'] = "ST Revenue"
        value_col = stacked_df5.pop(0)
        stacked_df5.insert(2, "Value", value_col)
        concat_df = pd.concat([concat_df, stacked_df5])

        stacked_df5 = pd.DataFrame(opt_rev_dict_LT)
        stacked_df5.set_index('Date', inplace=True)
        stacked_df5 = stacked_df5.stack()
        stacked_df5 = pd.DataFrame(stacked_df5)
        stacked_df5.reset_index(inplace=True)

        stacked_df5.rename(columns={'level_1': 'Opt Channel'}, inplace=True)
        stacked_df5 = pd.merge(fill_df[["Date", "Opt Channel"]].drop_duplicates(), stacked_df5, on = ["Date", "Opt Channel"], how="left").fillna(0)
        stacked_df5['Scenario'] = tab_names[key]
        stacked_df5['Budget/Revenue'] = "LT Revenue"
        value_col = stacked_df5.pop(0)
        stacked_df5.insert(2, "Value", value_col)
        concat_df = pd.concat([concat_df, stacked_df5])

    concat_df = pd.merge(concat_df, ST_header[['Opt Channel', 'Region', 'Brand', 'Channel Group', 'Channel']].drop_duplicates(), on="Opt Channel")
    concat_df['Date'] = concat_df['Date'].astype(str)
    return concat_df

@socketio.on("collect_data")
def chart_data():

    try:
        conn = engine.connect()
        query = text('SELECT * FROM "Optimised CSV";')

        db_result = conn.execute(query)
        #app.logger.info(tp_result.fetchall())
        chart_data = []
        col_names = db_result.keys()
        print("worked")
        for x in db_result.fetchall():
            a = dict(zip(col_names, x))
            date_column = a.get("Date")
            if date_column:
                month_year = datetime.strptime(date_column, '%Y-%m-%d').strftime("%b %Y")
                a["Month_Year"] = month_year
            chart_data.append(a)
        socketio.emit('chart_data', {'chartData':chart_data})
        print("chart_data sent")
    
    except SQLAlchemyError as e:
        print('Error executing query:', str(e))
       
    finally:
        if 'conn' in locals():
            conn.close()
@app.route('/filter_chart_data', methods=['GET'])
def filter_chart_data():
    try:
        conn = engine.connect()
        query = text('SELECT * FROM "Optimised CSV";')

        db_result = conn.execute(query)

        if db_result is None:
            return jsonify({'error': 'Internal Server Error'}), 500

        col_names = db_result.keys()
        min_date = None
        max_date = None
        data = {}

        for x in db_result.fetchall():
            for col_name, value in zip(col_names, x):
                if col_name == 'Date':
                    date_value = pd.to_datetime(value)
                    if min_date is None or date_value < min_date:
                        min_date = date_value
                    if max_date is None or date_value > max_date:
                        max_date = date_value
                elif col_name in ['Channel', 'Channel Group', 'Region', 'Country', 'Brand', 'Scenario', 'Optimisation Type', 'Budget/Revenue']:
                    if col_name not in data:
                        data[col_name] = []
                    if value not in data[col_name]:
                        data[col_name].append(value)

        if not min_date or not max_date:
            return jsonify({'error': 'Internal Server Error'}), 500

        # Remove 'Budget' from revenue types
        revenue_types = [rev_type for rev_type in data['Budget/Revenue'] if rev_type != 'Budget']
        data['revenue_types'] = revenue_types

        data['min_date'] = min_date.strftime('%Y-%m-%d')
        data['max_date'] = max_date.strftime('%Y-%m-%d')

        return jsonify(data)

    except SQLAlchemyError as e:
        print('Error executing query:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500

    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/chart_response', methods = ['GET'])
def chart_response():
    try:
        fpath = 'C:/Users/matthew.browne/Documents/Blueprint/optimiser output data'
        csv_data = pd.read_csv(fpath + '/response_curve_data.csv')
        chart_response = csv_data.to_dict(orient='records')
        return jsonify(chart_response)

    except Exception as e:
        print('Error reading CSV file:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/chart_budget', methods = ['GET'])
def chart_budget():
    try:
        fpath = 'C:/Users/matthew.browne/Documents/Blueprint/optimiser output data'
        csv_data = pd.read_csv(fpath + '/budget_curve_data.csv')
        chart_budget = csv_data.to_dict(orient='records')
        return jsonify(chart_budget)

    except Exception as e:
        print('Error reading CSV file:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/blueprint_results')
@login_required
def blueprint_results():
    return render_template('blueprint_results.html')

@app.route('/date_range', methods = ['GET','POST'])
def date_range():
    start_date = list(laydown_dates)[1]
    app.logger.info(start_date)
    end_date = list(laydown_dates)[-1]
    app.logger.info(end_date)
    return jsonify({"startDate":start_date, "endDate":end_date})

@app.route('/blueprint')
@login_required
def blueprint():
    app.logger.info(laydown_dates)
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

        app.logger.info(f"received table ids: {received_table_ids}")

        for table_id in list(table_data.keys()):
            if table_id not in received_table_ids:
                
                del table_data[table_id]
                app.logger.info(f"deleted tab: {table_id}")

        return jsonify({'success': True, 'message': 'Table data updated successfully'})

    except KeyError:
        app.logger.info("tableIDs not found in ajax post request.")
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

    if tableID not in table_data.keys():
        table_data[tableID] = deepcopy(table_dict)

    app.logger.info(table_data.keys())

    return jsonify({"success": True, "table_id": tableID})

@app.route('/channel_delete', methods = ['POST'])
def channel_delete():
    deleted_tab = str(request.json.get("tabID"))
    app.logger.info(f"deleted tab: {deleted_tab}")
    table_data.pop(deleted_tab)
    return jsonify({"success":"tab removed succesfully"})

@app.route('/channel_main', methods = ['GET'])
def channel_main():
    app.logger.info(table_data.keys())    
    return jsonify(table_data)

@app.route('/table_data_editor', methods = ['POST'])
def table_data_editor():
    global table_data
    try:
        data = request.get_json()
        print(data)
        table_id = str(data['tableId'])
        print(table_id)
        target_table = table_data[table_id]
        if data['action'] == 'edit':
            for row_id, changes in data['data'].items():
                row_index = int(row_id) - 1
                for field, new_value in changes.items():
                    table_data[table_id][row_index][field] = new_value
        print(table_data["1"][row_index])
        print(table_data[table_id][row_index])
        return jsonify(data=target_table)
    except Exception as e:
        print("error processing data:", str(e))
        response = {
            'data': 'error',
            'status': 'error'
        }
    return jsonify(response)
    

@app.route('/')
def welcome_page():
    app.logger.info(current_user)
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
            app.logger.info(f"User {username} logged in successfully.")
            app.logger.info(current_user.user_info)
            return redirect(url_for('blueprint'))
        else:
            app.logger.info(f"Failed login attempt for user {username}.")
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

@app.route('/export_data')
@login_required
def export_data():
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        all_input = pd.read_sql_table('All_Channel_Inputs', engine)
        laydown= pd.read_sql_table('All_Laydown', engine)
        all_index= pd.read_sql_table('All_Index', engine)
        #ST_incr_rev= pd.read_sql_table('All_Incremental_Revenue_ST', engine)
        #LT_incr_rev = pd.read_sql_table('All_Incremental_Revenue_LT', engine)
        
        all_input.to_excel(writer, sheet_name='All Inputs', index=False)
        laydown.to_excel(writer, sheet_name='Laydown', index=False)
        all_index.to_excel(writer, sheet_name='Seasonal Index', index=False)

    excel_buffer.seek(0)

    return send_file(excel_buffer, download_name=f'{current_user.id}_Input_File.xlsx', as_attachment=True)


if __name__ == '__main__':
     with app.app_context():
        db.create_all()
        # for user in user_data:
        #     add_user(user)
        socketio.run(app=app, host='0.0.0.0', port=os.environ.get('PORT', 5000), debug=True)
