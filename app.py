# %% --------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
from flask import Flask, render_template, send_file, jsonify, request, url_for, redirect, flash, session, current_app
from flask_socketio import SocketIO, emit
import numpy as np
import pandas as pd
import json
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload, sessionmaker
from sqlalchemy import create_engine, text, Column, DateTime, Integer, func, UUID
import uuid
from datetime import datetime, date, time
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import urllib.parse
from flask_bcrypt import Bcrypt
import secrets
import logging
from optimiser import Optimise
from io import BytesIO
from copy import deepcopy
import threading
import queue
import app_config
# from identity.flask import Auth
from pathlib import Path
from flask_session import Session
import msal
from functools import wraps

#from azure import identity

app = Flask(__name__)
socketio = SocketIO(app=app, async_mode='eventlet')

task_queue = queue.Queue()

app.config.from_object(app_config)

app.config['SESSION_COOKIE_SECURE'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['DEBUG'] = True
db_username = app_config.DB_USERNAME
db_password = app_config.DB_PASSWORD

host = "acblueprint-server.postgres.database.azure.com"
database_name = "acblueprint-db"
connection_string = f"postgresql://{db_username}:{db_password}@{host}/{database_name}"  # Replace with your database connection URL

app.config['SQLALCHEMY_DATABASE_URI'] = connection_string

engine = create_engine(connection_string, pool_pre_ping=True)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# app.config["MSAL_CLIENT"] = msal.ConfidentialClientApplication(
#     client_id,
#     authority=authority,
#     client_credential=client_secret
# )

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):
            # User is not authenticated, redirect to login page
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


class Snapshot(db.Model):
    name = db.Column(db.String, nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String, nullable=False)
    table_ids = db.Column(db.String, nullable=False)
    scenario_names = db.Column(db.String, nullable=False)
    user_id = db.Column(db.UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    table_data = db.Column(db.Text, nullable=False)

active_sessions = {}

@app.route("/")
def index():
    #if not session.get("user"):
    #    return redirect(url_for("login"))

    if not session.get("user"):
        print("rendering index.html, user does not exist in session")
        
        session["flow"] = _build_auth_code_flow(scopes=app_config.SCOPE)
        return render_template('index.html', auth_url=session["flow"]["auth_uri"], version=msal.__version__)
    else:
        print("rendering index.html, user exists in session")
        print(session["user"]['oid'])
        return render_template('index.html', user=session["user"], version=msal.__version__)
    
@app.route("/login")
def login():
    # Technically we could use empty list [] as scopes to do just sign in,
    # here we choose to also collect end user consent upfront
    session["flow"] = _build_auth_code_flow(scopes=app_config.SCOPE)
    auth_url=session["flow"]["auth_uri"]
    version=msal.__version__
    return redirect(auth_url)

@app.route(app_config.REDIRECT_PATH)  # Its absolute URL must match your app's redirect_uri set in AAD
def authorized():
    try:
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_auth_code_flow(
            session.get("flow", {}), request.args)
        if "error" in result:
            return render_template("auth_error.html", result=result)
        session["user"] = result.get("id_token_claims")
        _save_cache(cache)
    except ValueError:  # Usually caused by CSRFF
        pass  # Simply ignore them
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()  # Wipe out user and its token cache from session
    return redirect(  # Also logout from your tenant's web session
        app_config.AUTHORITY + "/oauth2/v2.0/logout" +
        "?post_logout_redirect_uri=" + url_for("index", _external=True))

# MSAL METHODS

def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        client_id=app_config.CLIENT_ID, authority=app_config.AUTHORITY,
        client_credential=app_config.CLIENT_SECRET, token_cache=cache)

def _build_auth_code_flow(authority=None, scopes=None):
    return _build_msal_app(authority=app_config.AUTHORITY).initiate_auth_code_flow(
        scopes or [],
        redirect_uri=url_for("authorized", _external=True))

def _get_token_from_cache(scope=None):
    cache = _load_cache()  # This web app maintains one cache per session
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    if accounts:  # So all account(s) belong to the current signed-in user
        result = cca.acquire_token_silent(scope, account=accounts[0])
        _save_cache(cache)
        return result

app.jinja_env.globals.update(_build_auth_code_flow=_build_auth_code_flow)  # Used in template




class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    message = db.Column(db.String, nullable=False)


@app.route('/get_user_id', methods=['GET'])
def get_user_id():
    user_id = session['user']['oid']
    return jsonify({'user_id': user_id})


@app.route('/save_snapshot', methods=['POST'])

def save_snapshot():
    snapshot_name = request.json.get('name')
    user_id = session['user']['oid']
    content = request.json.get('content')
    scenario_names = request.json.get('scenarioNames')
    current_table_ids = list(table_data.keys())
    table_data_json = json.dumps(table_data)

    table_ids_str = ','.join(map(str, current_table_ids))

    # Check if a snapshot with the same name already exists for the current user
    existing_snapshot = Snapshot.query.filter_by(name=snapshot_name, user_id=user_id).first()

    if existing_snapshot:
        # Update the existing snapshot
        existing_snapshot.content = content
        existing_snapshot.table_ids = table_ids_str
        existing_snapshot.scenario_names = scenario_names
        existing_snapshot.table_data = table_data_json
    else:
        # Create a new snapshot
        new_snapshot = Snapshot(name=snapshot_name, content=content, table_ids=table_ids_str, scenario_names=scenario_names, user_id=user_id,
                                table_data=table_data_json)
        db.session.add(new_snapshot)

    try:
        db.session.commit()
        return jsonify({'success': True})
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/overwrite_save', methods=['POST'])
def overwrite_save():
    snapshot_id = request.json.get('selectedSaveId')
    user_id = session['user']['oid']
    content = request.json.get('content')
    scenario_names = request.json.get('scenarioNames')
    current_table_ids = list(table_data.keys())
    table_data_json = json.dumps(table_data)

    table_ids_str = ','.join(map(str, current_table_ids))

    app.logger.info(f"snapshot id = {snapshot_id}")
    app.logger.info(f"user id = {user_id}")

    existing_snapshot = Snapshot.query.filter_by(id=snapshot_id, user_id=user_id).first()
    existing_snapshot.content = content
    existing_snapshot.table_ids = table_ids_str
    existing_snapshot.table_data = table_data_json
    existing_snapshot.scenario_names = scenario_names

    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/load_snapshot')
def load_snapshot():
    global table_data
    user_id = session['user']['oid']
    snapshot = Snapshot.query.filter_by(user_id=user_id).first()
    table_data = json.loads(snapshot.table_data)
    content_list = snapshot.content
    table_ids_list = snapshot.table_ids
    app.logger.info(table_data.keys())
    return jsonify({'content': content_list, 'table_ids': table_ids_list})


@app.route('/get_saves', methods=['GET'])
def get_saves():

    user_saves = Snapshot.query.filter_by(user_id=session['user']['oid']).all()
    saves_data = []

    for save in user_saves:
        save_info = {
            'DT_RowId': save.id,
            'name': save.name,
            'table_ids': save.table_ids
        }
        saves_data.append(save_info)

    return jsonify({'data': saves_data})


@app.route('/toggle_states', methods=['POST'])
def toggle_states():
    try:
        data = request.json

        return jsonify({"message": "Toggle states saved successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/load_selected_row', methods=['GET', 'POST'])
def notify_selected_row():
    if request.method == 'POST':
        save_id = request.json.get('selectedSaveId')
        session['save_id'] = save_id
        return jsonify({'status': 'POST request procecssed successfully'})

    elif request.method == 'GET':
        save_id = session.get('save_id')
        session.pop('save_id', None)
        save = Snapshot.query.filter_by(id=save_id, user_id=session['user']['oid']).first()
        if not save:
            return jsonify({'error': 'Unathorized access'}), 403
        else:
            content_list = save.content
            table_ids_list = save.table_ids
            scenario_names = save.scenario_names
            table_data = json.loads(save.table_data)
            app.logger.info(table_data.keys())
            return jsonify({'content': content_list, 'table_ids': table_ids_list, 'scenario_names':scenario_names})


results = {}

seas_index_table_name = 'seas_index'
ST_db_table_name = 'ST_header'
LT_db_table_name = "LT_header"
laydown_table_name = "laydown"


num_weeks = 1000


def prep_rev_per_stream(stream, budget, cost_per_dict, carryover_dict, alpha_dict, beta_dict):
    cost_per_stream = cost_per_dict.get(stream, 1e-6)  # Set a small non-zero default cost
    # print("cpu:")
    # print(cost_per_stream)
    allocation = budget / cost_per_stream
    # print('allocation:')
    # print(allocation)
    pct_laydown = []
    for x in range(len(recorded_impressions[stream])):
        try:
            pct_laydown.append(recorded_impressions[stream][x] / sum(recorded_impressions[stream]))
        except:
            pct_laydown.append(0)
    # print("pct_laydown:")
    # print(pct_laydown)
    pam = [pct_laydown[i] * allocation for i in range(len(pct_laydown))]
    carryover_list = []
    carryover_list.append(pam[0])
    for x in range(1, len(pam)):
        carryover_val = pam[x] + carryover_list[x - 1] * carryover_dict[stream]
        carryover_list.append(carryover_val)
    # print("carryover list:")
    # print(carryover_list)
    rev_list = []
    for x in carryover_list:
        rev_val = beta_dict[stream] * (1 - np.exp(-alpha_dict[stream] * x))
        rev_list.append(rev_val)
    # print("rev list")
    # print(rev_list)
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
        # print(x)
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
        # print(x)
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
# stream = 'ATLTVSuper FoodsBSBakersDog'
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
                  # 'ST Carryover', 'ST Alpha', 'ST Beta', 'LT Carryover', 'LT Alpha', 'LT Beta',
                  'Laydown']

for col in table_df.columns:
    if col not in dataTable_cols:
        table_df.drop(columns=col, inplace=True)

table_df.insert(0, 'row_id', range(1, len(table_df) + 1))
table_dict = table_df.to_dict("records")
for var in table_dict:
    var['Laydown'] = laydown[var['Channel'] + "_" + var['Region'] + "_" + var['Brand']].tolist()

table_data = {"1": deepcopy(table_dict)}
bud = sum(ST_header['Current Budget'].to_list())

# %% --------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------

inputs_per_result = {}
output_df_per_result = {}

def optimise(ST_input, LT_input, laydown, seas_index, blend, obj_func, max_budget, exh_budget, ftol, ssize, table_id, scenario_name):

    global results
    global output_df_per_result

    

    try:
        with app.app_context():
            result, time_elapsed, output_df = Optimise.blended_profit_max_scipy(ST_input=ST_input, LT_input=LT_input, laydown=laydown, seas_index=seas_index, return_type=blend, objective_type=obj_func, max_budget=max_budget, exh_budget=exh_budget, method='SLSQP', scenario_name=scenario_name, tolerance=ftol, step=ssize)
            app.logger.info(f"Task completed: {result} in {time_elapsed} time")
            results[table_id] = result
            output_df_per_result[table_id] = output_df
            # print(f"total results: {results}")
            socketio.emit('opt_complete', {'data': table_id})
    except Exception as e:
        with app.app_context():
            app.logger.info(f"Error in task callback causing optimisation not to run: {str(e)}")
            socketio.emit('opt_complete', {'data': table_id, 'exception':str(e)})


@socketio.on('optimise')
def run_optimise(dataDict):

    data = dict(dataDict.get('dataToSend'))
    global inputs_per_result
    table_id = str(data['tableID'])
    ST_header_copy = deepcopy(ST_header)
    LT_header_copy = deepcopy(LT_header)
    laydown_copy = deepcopy(laydown)
    seas_index_copy = deepcopy(seas_index)

    app.logger.info("REACHING OPT METHOD")
    
    try:
        obj_func = data['objectiveValue']
        exh_budget = data['exhaustValue']
        max_budget = int(data['maxValue'])
        ftol_input = float(data['ftolValue'])
        ssize_input = float(data['ssizeValue'])
        scenario_name = data['tabName']
        num_weeks = 1000
        blend = data['blendValue']
        disabled_rows = list(data['disabledRows'])
        print(f"disabled row ids: {disabled_rows}")

        current_table_df = pd.DataFrame.from_records(deepcopy(table_data[table_id]))
        removed_rows_df = current_table_df[current_table_df.row_id.isin(disabled_rows)].copy()
        removed_rows_df['Opt Channel'] = removed_rows_df.apply(
            lambda row: '_'.join([str(row['Channel']), str(row['Region']), str(row['Brand'])]), axis=1)

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
        
        if "dates" in data:
          
            app.logger.info('dates found in data')
            print("dates in the datatosend")
            #print(data['dates'][0][:10])
            #print(data['dates'][1][:10])
            start_date = datetime.strptime(data['dates'][0][:10], "%Y-%m-%d")
            end_date = datetime.strptime(data['dates'][1][:10], "%Y-%m-%d")
            app.logger.info(f"adding optimisation between start date: {start_date} and end date: {end_date} to queue")
            #print(f"start data: {start_date}, end_date: {end_date}, laydown_copy dates: {laydown_copy['Date']}")
            laydown_copy = laydown_copy[(laydown_copy["Date"] >= start_date) & (laydown_copy["Date"] <= end_date)]
            seas_index_copy = seas_index_copy[(laydown_copy["Date"] >= start_date) & (seas_index_copy["Date"] <= end_date)]
            #print(laydown_copy)
            #print(seas_index_copy)
            app.logger.info(start_date)
            app.logger.info(end_date)

        app.logger.info(
            f"retrieved from the server: table id = {table_id}, objective function = {obj_func}, exhaust budget = {exh_budget}, max budget = {max_budget}, blended = {blend}")



        #print(f"laydown = {laydown_copy}")
        #print(f"CPU = {[entry['CPU'] for entry in ST_input]}")

        inputs_dict = {'ST_input': ST_input, 'LT_input': LT_input, 'laydown': laydown_copy, 'seas_index': seas_index_copy}

        #print(f"inputs per result: {inputs_per_result}")
        inputs_per_result[table_id] = deepcopy(inputs_dict)
        #print(f"inputs per result: {inputs_per_result}")
        min_spend_cap_list = [float(entry['Min Spend Cap']) for entry in ST_input]
        min_spend_cap_dict = dict(zip(streams, min_spend_cap_list))
        laydown_copy.set_index('Date', inplace=True)
        #print(min_spend_cap_dict)
        #socketio.start_background_task(target=optimise, ST_input=ST_input, LT_input=LT_input, laydown=laydown_copy, seas_index=seas_index_copy, blend=blend, obj_func=obj_func, max_budget=max_budget, exh_budget=exh_budget, ftol=ftol_input, ssize=ssize_input, table_id = table_id, scenario_name = scenario_name)
        task_queue.put((ST_input, LT_input, laydown_copy, seas_index_copy, blend, obj_func, max_budget, exh_budget, ftol_input, ssize_input, table_id, scenario_name))
    except Exception as e:
        app.logger.info('Error in user inputs')
        socketio.emit('opt_complete', {'data': table_id, 'exception': str(e)})

    return jsonify({'status': 'Task started in the background'})

def run_optimise_task():
    while True:
        # Get the task from the queue (blocks until a task is available)
        task = task_queue.get()
        if task is None:
            break
        
        # Unpack the task arguments
        ST_input, LT_input, laydown_copy, seas_index_copy, blend, obj_func, max_budget, exh_budget, ftol, ssize, table_id, scenario_name = task
        
        # Run the optimise task with provided arguments
        optimise(ST_input=ST_input, LT_input=LT_input, laydown=laydown_copy, seas_index=seas_index_copy, blend=blend, obj_func=obj_func, max_budget=max_budget, exh_budget=exh_budget, ftol=ftol, ssize=ssize, table_id=table_id, scenario_name=scenario_name)
        
        # Mark the task as done
        task_queue.task_done()

# Start the thread to run optimise tasks
optimise_thread = threading.Thread(target=run_optimise_task)
optimise_thread.daemon = True  # Set the thread as a daemon so it exits when the main thread exits
optimise_thread.start()

@app.route('/results_output', methods=['POST'])
def results_output():
    global inputs_per_result
    tab_names = dict(request.json)
    print(tab_names)
    #print(inputs_per_result)
    output = create_output(output_df_per_result=output_df_per_result)

    try:
        output.to_sql('Optimised CSV', engine, if_exists='replace', index=False)
        app.logger.info("output (results) uploaded to cb successfully")
    except:
        app.logger.info("output (resutls) db upload failed")

    return jsonify({"message": "csv exported successfully"})

def create_output(output_df_per_result):
    concat_df = pd.DataFrame()
    for key, value in output_df_per_result.items():
        concat_df = pd.concat([concat_df, value])
    
    return concat_df


@socketio.on("collect_data")
def chart_data():
    global chart_data
    try:
        conn = engine.connect()
        query = text('SELECT * FROM "Optimised CSV";')

        db_result = conn.execute(query)
        rows = db_result.fetchall()
        columns = db_result.keys()
        result_df = pd.DataFrame(rows, columns=columns)
        db_result.close()
        result_df['Date'] = pd.to_datetime(result_df['Date'])
        result_df['MonthYear'] = result_df['Date'].dt.strftime('%b %Y')
        result_df = result_df.groupby(
            ['Opt Channel', 'Scenario', 'Budget/Revenue', 'Region', 'Brand', 'Channel Group', 'Channel',
             'MonthYear']).sum(numeric_only=True)
        result_df.reset_index(inplace=True)
        result_df = result_df.sort_values(by='MonthYear')
        chart_data = []
        
        for index, row in result_df.iterrows():
            a = dict(row)
            chart_data.append(a)

        dropdown_options = {}
        for column in result_df.columns:
            if column not in ['Opt Channel', 'Value']:
                if column == 'Budget/Revenue':
                    dropdown_options[column] = [value for value in result_df[column].unique() if "Budget" not in value]
                else:
                    dropdown_options[column] = result_df[column].unique().tolist()

        socketio.emit('dropdown_options', {'options': dropdown_options})
        print("Dropdown options sent")

        socketio.emit('chart_data', {'chartData': chart_data})
        print("chart_data sent")

    except SQLAlchemyError as e:
        print('Error executing query:', str(e))

    finally:
        if 'conn' in locals():
            conn.close()

@socketio.on("apply_filter")
def handle_apply_filter(filter_data):
    try:
        filters = filter_data

        if "Budget/Revenue" in filters and filters["Budget/Revenue"]:
            if "Budget" not in filters["Budget/Revenue"]:
                filters["Budget/Revenue"].append("Budget")
        else:
            filters["Budget/Revenue"] = []

        print('Received filter data:', filters)
        apply_filters(filters)
    except KeyError:
        print("KeyError: 'Budget/Revenue' not found in filter_data")

def apply_filters(filters):
    try:
        filtered_data = []
        print(filters)

        for data_point in chart_data:
            include_data_point = True

            for key, values in filters.items():
                if values and data_point[key] not in values:
                    include_data_point = False
                    break

            if include_data_point:
                filtered_data.append(data_point)

        socketio.emit('filtered_data', {'filtered_data': filtered_data})
        print("Filtered chart data sent")
        print("Filtered data length:", len(filtered_data))

    except Exception as e:
        print('Error applying filter:', str(e))

@socketio.on("response_data")
def chart_response():
    global chart_response
    global dropdown_options1
    try:
        conn = engine.connect()
        tables = ["Curves_Channel_Response_Blended", "Curves_Channel_Response_LT", "Curves_Channel_Response_ST"]
        chart_response = []

        for table in tables:
            query = text(f'SELECT * FROM "{table}";')
            db_result = conn.execute(query)

            col_names = db_result.keys()
            for x in db_result.fetchall():
                a = dict(zip(col_names, x))
                a["Optimisation Type"] = table.split("_")[3].upper()
                a["region_brand"] = f"{a['Region']}_{a['Brand']}"
                a["region_brand_opt"] = f"{a['region_brand']}_{a['Optimisation Type']}"
                chart_response.append(a)

        dropdown_options1 = {}
        for column in ["Region", "Brand", "Channel Group", "Channel", "Optimisation Type", "region_brand",
                       "region_brand_opt"]:
            dropdown_options1[column] = list(set(row[column] for row in chart_response))

        default_option = dropdown_options1["region_brand"][0]
        default_option = default_option + "_" + chart_response[0]["Optimisation Type"]
        chart_response_default = [row for row in chart_response if row["region_brand_opt"] == default_option]

        print(default_option)

        socketio.emit('dropdown_options1', {'options': dropdown_options1})
        print("Curve Dropdown options sent")

        socketio.emit('chart_response', {'chartResponse': chart_response_default})
        print("chart_response sent")

    except SQLAlchemyError as e:
        print('Error executing query:', str(e))

    finally:
        if 'conn' in locals():
            conn.close()


@socketio.on("budget_data")
def chart_budget():
    global chart_budget
    try:
        conn = engine.connect()
        query = text('SELECT * FROM "Curves_Horizon";')

        db_result = conn.execute(query)
        chart_budget = []
        col_names = db_result.keys()
        for x in db_result.fetchall():
            a = dict(zip(col_names, x))
            a["region_brand"] = f"{a['Region']}_{a['Brand']}"
            chart_budget.append(a)

        default_option = dropdown_options1["region_brand"][0]
        chart_budget_default = [row for row in chart_budget if row["region_brand"] == default_option]

        print(default_option)

        socketio.emit('chart_budget', {'chartBudget': chart_budget_default})
        print("chart_budget sent")

    except SQLAlchemyError as e:
        print('Error executing query:', str(e))

    finally:
        if 'conn' in locals():
            conn.close()


@socketio.on("roi_data")
def chart_roi():
    global chart_roi
    try:
        conn = engine.connect()
        query = text('SELECT * FROM "Curves_Optimal_ROI";')

        db_result = conn.execute(query)
        chart_roi = []
        col_names = db_result.keys()
        for x in db_result.fetchall():
            a = dict(zip(col_names, x))
            a["region_brand"] = f"{a['Region']}_{a['Brand']}"
            chart_roi.append(a)

        default_option = dropdown_options1["region_brand"][0]
        chart_roi_default = [row for row in chart_roi if row["region_brand"] == default_option]

        socketio.emit('chart_roi', {'chartROI': chart_roi_default})
        print("chart_roi sent")

    except SQLAlchemyError as e:
        print('Error executing query:', str(e))

    finally:
        if 'conn' in locals():
            conn.close()


@socketio.on("budget_response_data")
def chart_budget_response():
    global chart_budget_response
    try:
        conn = engine.connect()
        query = text('SELECT * FROM "Curves_Budget_Response";')

        db_result = conn.execute(query)
        chart_budget_response = []
        col_names = db_result.keys()
        for x in db_result.fetchall():
            a = dict(zip(col_names, x))
            a["region_brand"] = f"{a['Region']}_{a['Brand']}"
            chart_budget_response.append(a)

        default_option = dropdown_options1["region_brand"][0]
        chart_budget_response_default = [row for row in chart_budget_response if row["region_brand"] == default_option]

        socketio.emit('chart_budget_response', {'chartBudget_response': chart_budget_response_default})
        print("chart_budget_response sent")

    except SQLAlchemyError as e:
        print('Error executing query:', str(e))

    finally:
        if 'conn' in locals():
            conn.close()


@socketio.on("apply_filter_curve")
def handle_curve_filter(curve_filter_data):
    try:
        curve_filters = curve_filter_data
        if 'Region' in curve_filters and 'Brand' in curve_filters and 'Optimisation Type' in curve_filters:
            curve_filters['region_brand_opt'] = f"{curve_filters['Region']}_{curve_filters['Brand']}_{curve_filters['Optimisation Type']}"
        if 'Region' in curve_filters and 'Brand' in curve_filters:
            curve_filters['region_brand'] = f"{curve_filters['Region']}_{curve_filters['Brand']}"

        print('Received filter data:', curve_filters)
        unique_region_brand_opt = set(row["region_brand"] for row in chart_budget)
        print("Unique values in chart_budget:", unique_region_brand_opt)

        apply_curve_filters(chart_response, curve_filters, 'filtered_data_response')
        apply_curve_filters(chart_budget, curve_filters, 'filtered_data_budget')
        apply_curve_filters(chart_roi, curve_filters, 'filtered_data_roi')
        apply_curve_filters(chart_budget_response, curve_filters, 'filtered_data_budget_response')

    except Exception as e:
        print('Error applying filters:', str(e))

def apply_curve_filters(data, curve_filters, event_name):
    try:
        filtered_data = []

        if data == chart_response:
            filter_key = 'region_brand_opt'
        else:
            filter_key = 'region_brand'

        for data_point in data:
            include_data_point = True

            if filter_key == 'region_brand_opt':
                data_point_filter = f"{data_point['region_brand_opt']}"
            else:
                data_point_filter = f"{data_point['region_brand']}"

            relevant_filters = {key: values for key, values in curve_filters.items() if key in data_point}

            for key, values in relevant_filters.items():
                if values and data_point[key] not in values:
                    include_data_point = False
                    break

            if include_data_point:
                filtered_data.append(data_point)

        socketio.emit(event_name, {'filtered_data': filtered_data})
        print("Filtered chart data sent for", event_name)
        print("Filtered data length:", len(filtered_data))

    except Exception as e:
        print('Error applying filter:', str(e))

@app.route('/blueprint_results')
def blueprint_results():
    return render_template('blueprint_results.html')


@app.route('/blueprint_curve')
def blueprint_curve():
    return render_template('blueprint_curveresults.html')


@app.route('/date_range', methods=['GET', 'POST'])
def date_range():
    start_date = list(laydown_dates)[1]
    app.logger.info(start_date)
    end_date = list(laydown_dates)[-1]
    app.logger.info(end_date)
    return jsonify({"startDate": start_date, "endDate": end_date})

@login_required
@app.route('/blueprint')
def blueprint():
    app.logger.info(laydown_dates)
    return render_template('blueprint.html', user_id=session['user']['oid'])


@app.route('/get_table_ids', methods=['GET'])
def get_table_ids():
    table_ids = list(table_data.keys())
    return jsonify({"success": True, "tableIds": table_ids})


@app.route('/table_ids_sync', methods=['POST'])
def table_ids_sync():
    try:

        received_data = request.get_json()
        received_table_ids = received_data.get('tableIDs', [])
        # parsed_data = parse_qs(received_data)
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


@app.route('/sync_tab_counter', methods=['GET'])
def sync_tab_counter():
    last_number = list(table_data.keys())[-1]
    return jsonify({'lastNumber': last_number})


@app.route('/create_copy', methods=['POST'])
def create_copy():
    global table_data

    tableID = str(request.form.get('tableID'))

    if tableID not in table_data.keys():
        table_data[tableID] = deepcopy(table_dict)

    app.logger.info(table_data.keys())

    return jsonify({"success": True, "table_id": tableID})


@app.route('/channel_delete', methods=['POST'])
def channel_delete():
    deleted_tab = str(request.json.get("tabID"))
    app.logger.info(f"deleted tab: {deleted_tab}")
    table_data.pop(deleted_tab)
    return jsonify({"success": "tab removed succesfully"})


@app.route('/channel_main', methods=['GET'])
def channel_main():
    app.logger.info(table_data.keys())
    return jsonify(table_data)


@app.route('/table_data_editor', methods=['POST'])
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


@app.route('/export_data')
def export_data():
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        all_input = pd.read_sql_table('All_Channel_Inputs', engine)
        laydown = pd.read_sql_table('All_Laydown', engine)
        all_index = pd.read_sql_table('All_Index', engine)
        # ST_incr_rev= pd.read_sql_table('All_Incremental_Revenue_ST', engine)
        # LT_incr_rev = pd.read_sql_table('All_Incremental_Revenue_LT', engine)

        all_input.to_excel(writer, sheet_name='All Inputs', index=False)
        laydown.to_excel(writer, sheet_name='Laydown', index=False)
        all_index.to_excel(writer, sheet_name='Seasonal Index', index=False)

    excel_buffer.seek(0)
    
    if session['user']['oid'] != None:
        user_id = session['user']['oid']
        return send_file(excel_buffer, download_name=f'{user_id}_Input_File.xlsx', as_attachment=True)
    else:
        pass


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # for user in user_data:
        #     add_user(user)
        socketio.run(app=app)