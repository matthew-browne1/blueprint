# %% --------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
from flask import Flask, render_template, send_file, jsonify, request, url_for, redirect, flash, session, current_app
from flask_socketio import SocketIO, emit, join_room, leave_room
import numpy as np
import pandas as pd
import json
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text, Column, DateTime, Integer, func, UUID
import uuid
from datetime import datetime, date, time
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask_bcrypt import Bcrypt
import logging
from optimiser import Optimise, Beta
from io import BytesIO
from copy import deepcopy
import app_config
from flask_session import Session
import msal
from functools import wraps
from queue import Queue
from opt_threads import CustomThread
import pickle
import traceback

#from azure import identity

app = Flask(__name__)
socketio = SocketIO(app=app, manage_session=False, async_mode="eventlet")

#, async_mode='eventlet'

app.config.from_object(app_config)
secret_key = os.urandom(24)
app.secret_key = secret_key

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

session_queues = {}

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
    content = db.Column(db.LargeBinary, nullable=False)
    scenario_names = db.Column(db.LargeBinary, nullable=False)
    user_id = db.Column(db.Text, nullable=False)
    table_data = db.Column(db.Text, nullable=False)

active_sessions = {}

@app.route("/")
def index():
    #if not session.get("user"):
    #    return redirect(url_for("login"))

    if not session.get("user"):
        app.logger.info("rendering index.html, user does not exist in session")
        
        session["flow"] = _build_auth_code_flow(scopes=app_config.SCOPE)
        return render_template('index.html', auth_url=session["flow"]["auth_uri"], version=msal.__version__)
    else:
        user_name = session['user']['name']
        app.logger.info("rendering index.html, user exists in session")
        app.logger.info(session["user"]['oid'])
        return render_template('index.html', user=session["user"], user_name = user_name, version=msal.__version__)
    
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
        session['inputs_per_result'] = {}
        session['chart_data'] = []
        session['chart_response'] = []
        session['filtered_data'] = []
        session['filtered_curve_data'] = []
        session['queue'] = []
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        session.modified = True
        _save_cache(cache)
        app.logger.info("all session variables added to session object")
    except ValueError:  # Usually caused by CSRFF
        pass  # Simply ignore them
    return redirect(url_for("blueprint"))

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
    table_data_json = json.dumps(session['table_data'])

    # Check if a snapshot with the same name already exists for the current user
    existing_snapshot = Snapshot.query.filter_by(name=snapshot_name, user_id=user_id).first()

    
    pickled_string = pickle.dumps(content)
    pickled_scenario_names = pickle.dumps(scenario_names)
    if existing_snapshot:
        # Update the existing snapshot
        existing_snapshot.content = pickled_string
        existing_snapshot.scenario_names = pickled_scenario_names
        existing_snapshot.table_data = table_data_json
    else:
        # Create a new snapshot
        new_snapshot = Snapshot(name=snapshot_name, content=pickled_string, scenario_names=pickled_scenario_names, user_id=user_id,
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
    content = pickle.dumps(request.json.get('content'))
    scenario_names = request.json.get('scenarioNames')
    pickled_scenario_names = pickle.dumps(scenario_names)
    table_data_json = json.dumps(table_data)

    app.logger.info(f"snapshot id = {snapshot_id}")
    app.logger.info(f"user id = {user_id}")

    existing_snapshot = Snapshot.query.filter_by(id=snapshot_id, user_id=user_id).first()
    existing_snapshot.content = content
    existing_snapshot.table_data = table_data_json
    existing_snapshot.scenario_names = pickled_scenario_names

    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})



@app.route('/get_saves', methods=['GET'])
def get_saves():

    user_saves = Snapshot.query.filter_by(user_id=session['user']['oid']).all()
    saves_data = []

    for save in user_saves:
        table_ids = list(dict(pickle.loads(save.content)).keys())
        save_info = {
            'DT_RowId': save.id,
            'name': save.name,
            'table_ids': table_ids        
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
            content_list = pickle.loads(save.content)
            scenario_names = pickle.loads(save.scenario_names)
            session['table_data'] = json.loads(save.table_data)
            app.logger.info(f"current table ids: {session['table_data'].keys()}")
            return jsonify({'content': content_list, 'scenario_names':scenario_names})


seas_index_table_name = 'seas_index'
ST_db_table_name = 'ST_header'
LT_db_table_name = "LT_header"
laydown_table_name = "laydown"

num_weeks = 1000

country_to_region = {
    'Mexico': 'NA',
    'Brazil': 'LATAM',
    'Chile': 'LATAM',
    'UK': 'EUR',
    'France': 'EUR',
    'Germany': 'EUR',
    'Poland': 'EUR',
    'Australia': 'AOA'
}
header = pd.read_sql_table('All_Channel_Inputs', engine)
# Show column headers without underscores!
header.columns = [x.replace("_", " ") for x in header.columns.tolist()]
header.rename(columns={'Region':'Country'}, inplace=True)

header['Region'] = header['Country'].map(country_to_region).fillna('Other')
laydown = pd.read_sql_table('All_Laydown', engine)
laydown_dates = laydown['Date']
seas_index = pd.read_sql_table('All_Index', engine)

ST_inc_rev = pd.read_sql_table('All_Incremental_Revenue_ST', engine)
LT_inc_rev = pd.read_sql_table('All_Incremental_Revenue_LT', engine)

nns_mc = pd.read_sql_table("NNS_MC", engine)

table_df = header.copy()

dataTable_cols = ['Region', 'Country', 'Brand', 'Channel', 'Current Budget', 'Min Spend Cap', 'Max Spend Cap',
                  'Laydown']

for col in table_df.columns:
    if col not in dataTable_cols:
        table_df.drop(columns=col, inplace=True)

table_df.insert(0, 'row_id', range(1, len(table_df) + 1))
table_dict = table_df.to_dict("records")
for var in table_dict:
    var['Laydown'] = laydown[var['Channel'] + "_" + var['Country'] + "_" + var['Brand']].tolist()

table_data = {"1": deepcopy(table_dict)}
bud = sum(header['Current Budget'].to_list())


# %% --------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------

@socketio.on('optimise')
def run_optimise(dataDict):
    session_id = session.get('session_id')
    join_room(session_id)
    data = dict(dataDict.get('dataToSend'))
    
    table_id = str(data['tableID'])
    app.logger.info(f"optimising current table with ID:{table_id}")
    header_copy = deepcopy(header)
    laydown_copy = deepcopy(laydown)
    seas_index_copy = deepcopy(seas_index)
    ST_inc_rev_copy = deepcopy(ST_inc_rev)
    LT_inc_rev_copy = deepcopy(LT_inc_rev)
    nns_copy = deepcopy(nns_mc)
    streams = []
    for stream in header_copy['Opt Channel']:
        streams.append(str(stream))
    app.logger.info("REACHING OPT METHOD")
    
    try:
        obj_func = data['objectiveValue']
        exh_budget = data['exhaustValue']
        max_budget = int(data['maxValue'])
        scenario_name = data['tabName']
        app.logger.info(f"printing scenario name received from front end:{scenario_name}")
        blend = data['blendValue']
        disabled_rows = list(data['disabledRows'])
        app.logger.info(f"disabled row ids: {disabled_rows}")
        app.logger.info(f"current keys of table data in session:{session['table_data'].keys()}")
        # if table_id not in list(session['table_data'].keys()):
        #     session['table_data'][table_id] = deepcopy(table_dict)
        #     app.logger.info(f"table_data in {session['user']['name']}'s session added to table id: {table_id}")
        
        current_table_df = pd.DataFrame.from_records(deepcopy(table_data[table_id]))
        removed_rows_df = current_table_df[current_table_df.row_id.isin(disabled_rows)].copy()
        removed_rows_df['Opt Channel'] = removed_rows_df.apply(
            lambda row: '_'.join([str(row['Channel']), str(row['Country']), str(row['Brand'])]), axis=1)

        disabled_opt_channels = list(removed_rows_df['Opt Channel'])

        for col in current_table_df.columns:
            header_copy[col] = current_table_df[col]

        header_copy = header_copy[~(header_copy['Opt Channel'].isin(disabled_opt_channels))]

        laydown_copy = laydown_copy.drop(columns=disabled_opt_channels, errors='ignore')
        seas_index_copy = seas_index_copy.drop(columns=disabled_opt_channels, errors='ignore')
        
        if "dates" not in data:
            start_date = list(laydown_dates)[0]
            end_date = list(laydown_dates)[-1]
        else:
            start_date = datetime.strptime(data['dates'][0][:10], "%Y-%m-%d")
            end_date = datetime.strptime(data['dates'][1][:10], "%Y-%m-%d")
            app.logger.info(f"{session['user']['oid']}, dates found in data")
        
        laydown_copy = laydown_copy[(laydown_copy["Date"] >= start_date) & (laydown_copy["Date"] <= end_date)]
        seas_index_copy = seas_index_copy[(laydown_copy["Date"] >= start_date) & (seas_index_copy["Date"] <= end_date)]
        ST_inc_rev_copy = ST_inc_rev_copy[(ST_inc_rev_copy["Date"] >= start_date) & (ST_inc_rev_copy['Date'] <= end_date)]
        LT_inc_rev_copy = LT_inc_rev_copy[(LT_inc_rev_copy["Date"] >= start_date) & (LT_inc_rev_copy['Date'] <= end_date)]

        app.logger.info(
            f"retrieved from the server: table id = {table_id}, objective function = {obj_func}, exhaust budget = {exh_budget}, max budget = {max_budget}, blended = {blend}")

        ST_header = Beta.beta_calculation(header_copy, laydown_copy, seas_index_copy, ST_inc_rev_copy, 'st')

        LT_header = Beta.beta_calculation(header_copy, laydown_copy, seas_index_copy, LT_inc_rev_copy, 'lt')
      
        inputs_dict = {'ST_input': ST_header, 'LT_input': LT_header, 'laydown': laydown_copy, 'seas_index': seas_index_copy}

        session["inputs_per_result"][table_id] = deepcopy(inputs_dict)

        laydown_copy.set_index('Date', inplace=True)

        session_id = session['session_id']
        queue = session_queues.setdefault(session_id, Queue())
    
        queue.put((ST_header.to_dict("records"), LT_header.to_dict("records"), laydown_copy, seas_index_copy, nns_copy, blend, obj_func, max_budget, exh_budget, table_id, scenario_name))

        if not queue.empty():
            result, output_df = start_optimise_thread(session_id)
            session['output_df_per_result'][table_id] = output_df
            session['results'][table_id] = result
            app.logger.info(f"keys currently present in {session['user']['oid']}'s output_df_per_result session object: {session['output_df_per_result'].keys()}")
            session.modified = True
            app.logger.info("opt complete, hiding overlay")
            app.logger.info(session['output_df_per_result'].keys())
            app.logger.info(session['results'].keys())
            
    except Exception as e:
        app.logger.info(f"error adding optimisation job to the queue: {str(e)}")
        socketio.emit('opt_complete', {'data': table_id, 'exception': str(e)})

    return jsonify({'status': 'Task started in the background'})


def run_optimise_task(session_id):
    with app.app_context():
        queue = session_queues.get(session_id)
        if queue is None:
            return  # No queue found for this session
        while True:
            
            app.logger.info(f"job picked up from queue with session id: {session_id}")

            task = queue.get()
            
            ST_input, LT_input, laydown_copy, seas_index_copy, nns_copy, blend, obj_func, max_budget, exh_budget, table_id, scenario_name = task
            
            try:
                with app.app_context():
                    result, time_elapsed, output_df = Optimise.blended_profit_max_scipy(ST_input=ST_input, LT_input=LT_input, laydown=laydown_copy, seas_index=seas_index_copy, nns_mc=nns_copy, return_type=blend, objective_type=obj_func, max_budget=max_budget, exh_budget=exh_budget, method='SLSQP', scenario_name=scenario_name)
                    app.logger.info(f"Task completed: {result} in {time_elapsed} time")
                    
                    socketio.emit('opt_complete', {'data': table_id})
                    queue.task_done()
                    return result, output_df

            except Exception as e:
        
                app.logger.info(f"Error in task callback causing optimisation not to run: {str(e)}")
                
                socketio.emit('opt_complete', {'data': table_id, 'exception':str(e)})
                queue.task_done()
            

def start_optimise_thread(session_id):
    optimise_thread = CustomThread(target=run_optimise_task, args=(session_id,))
    optimise_thread.daemon = True
    optimise_thread.start()
    result, output_df = optimise_thread.join()

    app.logger.info("printing result added to session object from customthread class")
   
    return result, output_df


@app.route('/results_output', methods=['POST'])
def results_output():
    
    with app.app_context():
        tab_names = dict(request.json)
        print(tab_names)
        app.logger.info(f"results_output endpoint printing output df keys: {session['output_df_per_result'].keys()}")
        
        #print(inputs_per_result)
        output = create_output(output_df_per_result=session["output_df_per_result"])
        #print(output)
        
        output['Date'] = pd.to_datetime(output['Date'])
        output['Year'] = output['Date'].dt.year
        nns_mc_copy = deepcopy(nns_mc)
        merged_output = pd.merge(output, nns_mc_copy, on=['Country','Brand','Year'], how='left')
        merged_output.fillna(1, inplace=True)
        merged_output['Volume'] = merged_output['Value'] / (merged_output['NNS']*merged_output['MC'])
    
        try:
            merged_output.to_sql(f'Blueprint_results_{session["user"]["oid"]}', engine, if_exists='replace', index=False)
            app.logger.info("results uploaded to db successfully")
            return jsonify({"message": "results uploaded to db successfully"})
        except Exception as e:
            app.logger.info("results failed to upload to the db", str(e))
            return jsonify({"message": "results export failed"})
        

def create_output(output_df_per_result):
    concat_df = pd.DataFrame()
    for key, value in output_df_per_result.items():
        concat_df = pd.concat([concat_df, value])
    
    return concat_df


@socketio.on("collect_data")
def chart_data(data):
    session_id = session.get('session_id')
    join_room(session_id)
    session['chart_data'] = []
    metric = data['metric']

    try:
        conn = engine.connect()
        query = text(f'SELECT * FROM "Blueprint_results_{session["user"]["oid"]}";')
        db_result = conn.execute(query)
        rows = db_result.fetchall()
        columns = db_result.keys()
        result_df = pd.DataFrame(rows, columns=columns)
        db_result.close()
        result_df['Date'] = pd.to_datetime(result_df['Date'])
        result_df['MonthYear'] = result_df['Date'].dt.strftime('%b %Y')
        result_df = result_df.groupby(
            ['Opt Channel', 'Scenario', 'Budget/Revenue', 'Country', 'Brand', 'Channel Group', 'Channel',
             'MonthYear']).sum(numeric_only=True)
        result_df.reset_index(inplace=True)
        result_df = result_df.sort_values(by='MonthYear')

        for index, row in result_df.iterrows():
            a = dict(row)
            session['chart_data'].append(a)
        session.modified = True
        dropdown_options = {}
        for column in result_df.columns:
            if column not in ['Opt Channel', 'Value', 'Volume']:
                if column == 'Budget/Revenue':
                    dropdown_options[column] = [value for value in result_df[column].unique() if "Budget" not in value]
                else:
                    dropdown_options[column] = result_df[column].unique().tolist()
        
        socketio.emit('dropdown_options', {'options': dropdown_options})
        app.logger.info("Dropdown options sent")

        socketio.emit('chart_data', {'chartData': session['chart_data'], 'metric':metric, 'sessionID':session_id})
        app.logger.info("chart_data sent")

    except SQLAlchemyError as e:
        app.logger.info('Error executing query:', str(e))

    finally:
        if 'conn' in locals():
            conn.close()

@socketio.on("apply_filter")
def handle_apply_filter(data):
    session_id = session.get('session_id')
    join_room(session_id)
    try:
        filters = data['filters']
        metric = data['metric']
        app.logger.info(filters)
        app.logger.info(metric)
        if "Budget/Revenue" in filters and filters["Budget/Revenue"]:
            if "Budget" not in filters["Budget/Revenue"]:
                filters["Budget/Revenue"].append("Budget")
        else:
            filters["Budget/Revenue"] = []

        app.logger.info('Received filter data:', filters)
        apply_filters(filters, metric)
    except KeyError:
        app.logger.info("KeyError: 'Budget/Revenue' not found in filter_data")
    

def apply_filters(filters, metric):
    session_id = session.get('session_id')
    try:
        session['filtered_data'] = []
        app.logger.info(filters)
 
        for data_point in session['chart_data']:
            include_data_point = True

            for key, values in filters.items():
                if values and data_point[key] not in values:
                    include_data_point = False
                    break

            if include_data_point:
                session['filtered_data'].append(data_point)
        session.modified = True
        socketio.emit('filtered_data', {'filtered_data': session['filtered_data'], 'metric':metric, 'sessionID':session_id})
        app.logger.info("Filtered chart data sent")
        app.logger.info("Filtered data length:", len(session['filtered_data']))

    except Exception as e:
        app.logger.info('Error applying filter:', str(e))

@socketio.on("volval")
def volval_swap(data):
    session_id = session.get('session_id')
    join_room(session_id)
    metric = str(data['metric'])

    try:
        socketio.emit('filtered_data', {'filtered_data': session['filtered_data'], 'metric':metric})
        app.logger.info(metric)
    except Exception as e:
        app.logger.info(e)
        app.logger.info(metric)
        socketio.emit('chart_data', {'chartData': session['chart_data'], 'metric':metric})

            

@socketio.on("response_data")
def chart_response():
    session_id = session.get('session_id')
    join_room(session_id)
    
    try:
        conn = engine.connect()
        tables = ["Curves_Channel_Response_Blended", "Curves_Channel_Response_LT", "Curves_Channel_Response_ST"]
     

        for table in tables:
            query = text(f'SELECT * FROM "{table}";')
            db_result = conn.execute(query)

            col_names = db_result.keys()
            for x in db_result.fetchall():
                a = dict(zip(col_names, x))
                a["Optimisation Type"] = table.split("_")[3].upper()
                a["country_brand"] = f"{a['Country']}_{a['Brand']}"
                a["country_brand_opt"] = f"{a['country_brand']}_{a['Optimisation Type']}"
                session['chart_response'].append(a)

        session['dropdown_options1'] = {}
        for column in ["Country", "Brand", "Channel Group", "Channel", "Optimisation Type", "country_brand",
                       "country_brand_opt"]:
            session['dropdown_options1'][column] = list(set(row[column] for row in session['chart_response']))

        default_option = session['dropdown_options1']["country_brand"][0]
        default_option = default_option + "_" + session['chart_response'][0]["Optimisation Type"]
        chart_response_default = [row for row in session['chart_response'] if row["country_brand_opt"] == default_option]

 
        session.modified = True
        socketio.emit('dropdown_options1', {'options': session['dropdown_options1']})
        app.logger.info("Curve Dropdown options sent")

        socketio.emit('chart_response', {'chartResponse': chart_response_default})
        app.logger.info("chart_response sent")

    except SQLAlchemyError as e:
        app.logger.info('Error executing query:', str(e))

    finally:
        if 'conn' in locals():
            conn.close()


@socketio.on("budget_data")
def chart_budget():
    session_id = session.get('session_id')
    join_room(session_id)
    try:
        conn = engine.connect()
        query = text('SELECT * FROM "Curves_Horizon";')

        db_result = conn.execute(query)
        session['chart_budget'] = []
        col_names = db_result.keys()
        for x in db_result.fetchall():
            a = dict(zip(col_names, x))
            a["country_brand"] = f"{a['Country']}_{a['Brand']}"
            session['chart_budget'].append(a)

        dropdown_options1 = {}
        for column in ["Country", "Brand", "Channel Group", "Channel", "Optimisation Type", "country_brand",
                       "country_brand_opt"]:
            dropdown_options1[column] = list(set(row[column] for row in session['chart_response']))

        default_option = dropdown_options1["country_brand"][0]
        chart_budget_default = [row for row in session['chart_budget'] if row["country_brand"] == default_option]

 
        session.modified = True
        socketio.emit('chart_budget', {'chartBudget': chart_budget_default})
        app.logger.info("chart_budget sent")

    except SQLAlchemyError as e:
        app.logger.info('Error executing query:', str(e))

    finally:
        if 'conn' in locals():
            conn.close()


@socketio.on("roi_data")
def chart_roi():
    session_id = session.get('session_id')
    join_room(session_id)
    try:
        conn = engine.connect()
        query = text('SELECT * FROM "Curves_Optimal_ROI";')

        db_result = conn.execute(query)
        session['chart_roi'] = []
        col_names = db_result.keys()
        for x in db_result.fetchall():
            a = dict(zip(col_names, x))
            a["country_brand"] = f"{a['Country']}_{a['Brand']}"
            session['chart_roi'].append(a)

        dropdown_options1 = {}
        for column in ["Country", "Brand", "Channel Group", "Channel", "Optimisation Type", "country_brand",
                       "country_brand_opt"]:
            dropdown_options1[column] = list(set(row[column] for row in session['chart_response']))

        default_option = dropdown_options1["country_brand"][0]
        chart_roi_default = [row for row in session['chart_roi'] if row["country_brand"] == default_option]
        session.modified = True
        socketio.emit('chart_roi', {'chartROI': chart_roi_default})
        app.logger.info("chart_roi sent")

    except SQLAlchemyError as e:
        app.logger.info('Error executing query:', str(e))

    finally:
        if 'conn' in locals():
            conn.close()

@socketio.on("budget_response_data")
def chart_budget_response():
    session_id = session.get('session_id')
    join_room(session_id)
    try:
        conn = engine.connect()
        query = text('SELECT * FROM "Curves_Budget_Response";')

        db_result = conn.execute(query)
        session['chart_budget_response'] = []
        col_names = db_result.keys()
        for x in db_result.fetchall():
            a = dict(zip(col_names, x))
            a["region_brand"] = f"{a['Region']}_{a['Brand']}"
            session['chart_budget_response'].append(a)
        
        dropdown_options1 = {}
        for column in ["Country", "Brand", "Channel Group", "Channel", "Optimisation Type", "country_brand",
                       "country_brand_opt"]:
            dropdown_options1[column] = list(set(row[column] for row in session['chart_response']))

        default_option = dropdown_options1["country_brand"][0]
        chart_budget_response_default = [row for row in session['chart_budget_response'] if row["country_brand"] == default_option]
        session.modified = True
        socketio.emit('chart_budget_response', {'chartBudget_response': chart_budget_response_default})
        app.logger.info("chart_budget_response sent")

    except SQLAlchemyError as e:
        app.logger.info('Error executing query:', str(e))

    finally:
        if 'conn' in locals():
            conn.close()

@socketio.on("tv_data")
def tv_data_process():
    try:
        conn = engine.connect()
        query = text('SELECT * FROM "Optimal_TV_Laydown";')
        db_result = conn.execute(query)
        rows = db_result.fetchall()
        col_names = db_result.keys()
        result_df = pd.DataFrame(rows, columns=col_names)
        def country_brand_combine(row):
            return row['Country'] + '_' + row['Brand']
        result_df['country_brand'] = result_df.apply(country_brand_combine, axis=1)
        result_df['Date'] = pd.to_datetime(result_df['Date'])
        result_df['MonthYear'] = result_df['Date'].dt.strftime('%b %Y')
        result_df = result_df.groupby(
            ['Opt Channel', 'Scenario', 'Budget/Revenue', 'Country', 'Brand', 'Channel Group', 'Channel', 'Optimised', 'MonthYear', 'country_brand']).sum(numeric_only=True)
        result_df.reset_index(inplace=True)
        result_df = result_df.sort_values(by='MonthYear')
        chart_data = []
        for index, row in result_df.iterrows():
            a = dict(row)
            chart_data.append(a)
        app.logger.info("printing chart data for tv data")
        session['tv_data'] = chart_data
        socketio.emit('tv_chart_data', {'tv_chartData':session['tv_data']})
    except SQLAlchemyError as e:
        app.logger.info('Error executing query:', str(e))

    finally:
        if 'conn' in locals():
            conn.close()

@socketio.on("apply_filter_curve")
def handle_curve_filter(curve_filter_data):
    session_id = session.get('session_id')
    join_room(session_id)
    try:
        curve_filters = curve_filter_data
        if 'Country' in curve_filters and 'Brand' in curve_filters and 'Optimisation Type' in curve_filters:
            curve_filters['country_brand_opt'] = f"{curve_filters['Country']}_{curve_filters['Brand']}_{curve_filters['Optimisation Type']}"
        if 'Country' in curve_filters and 'Brand' in curve_filters:
            curve_filters['country_brand'] = f"{curve_filters['Country']}_{curve_filters['Brand']}"

        app.logger.info('Received filter data:', curve_filters)
        unique_country_brand_opt = set(row["country_brand"] for row in chart_budget)
        app.logger.info("Unique values in chart_budget:", unique_country_brand_opt)

        apply_curve_filters(session['chart_response'], curve_filters, 'filtered_data_response')
        apply_curve_filters(session['chart_budget'], curve_filters, 'filtered_data_budget')
        apply_curve_filters(session['chart_roi'], curve_filters, 'filtered_data_roi')
        apply_curve_filters(session['chart_budget_response'], curve_filters, 'filtered_data_budget_response')
        apply_curve_filters(session['tv_data'], curve_filters, 'filtered_tv_chartData')
        session.modified = True

    except Exception as e:
        app.logger.info('Error applying filters:', str(e))

def apply_curve_filters(data, curve_filters, event_name):
    session['filtered_curve_data'] = []
    try:
        
        if data == session['chart_response']:
            filter_key = 'country_brand_opt'
        else:
            filter_key = 'country_brand'

        for data_point in data:
            include_data_point = True

            if filter_key == 'country_brand_opt':
                data_point_filter = f"{data_point['country_brand_opt']}"
            else:
                data_point_filter = f"{data_point['country_brand']}"

            relevant_filters = {key: values for key, values in curve_filters.items() if key in data_point}

            for key, values in relevant_filters.items():
                if values and data_point[key] not in values:
                    include_data_point = False
                    break

            if include_data_point:
                session['filtered_curve_data'].append(data_point)
        session.modified = True
        socketio.emit(event_name, {'filtered_data': session['filtered_curve_data']})
        app.logger.info("Filtered chart data sent for", event_name)
        app.logger.info("Filtered chart data length:", len(session['filtered_curve_data']))

    except Exception as e:
        app.logger.info('Error applying filter:', str(e))

@app.route('/blueprint_results')
def blueprint_results():
    if session['user']['oid']:
        return render_template('blueprint_results.html')
    else:
        return redirect(url_for("login"))
    


@app.route('/blueprint_curve')
def blueprint_curve():
    if session['user']['oid']:
        return render_template('blueprint_curveresults.html')
    else:
        return redirect(url_for("login"))


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
    try:
        user_name = session['user']['name']
        user_id = session['user']['oid']
    except Exception as e:
        print("NO OID FOUND IN USER ATTRIBUTE CLAIMS")
        user_id = "temp"
        return redirect(url_for("login"))
    session['table_data'] = {"1": deepcopy(table_dict)}
    session['output_df_per_result'] = {}
    session['results'] = {}
    session.modified = True
    app.logger.info(laydown_dates)
    return render_template('blueprint.html', user_id=user_id, user_name=user_name)

@app.route('/get_session_id', methods=['GET'])
def get_session_id():
    session_id = session.get('session_id')  
    return jsonify({'session_id': session_id})

@app.route('/get_table_ids', methods=['GET'])
def get_table_ids():
    table_ids = list(session['table_data'].keys())
    return jsonify({"success": True, "tableIds": table_ids})


@app.route('/table_ids_sync', methods=['POST'])
def table_ids_sync():
    try:

        received_data = request.get_json()
        received_table_ids = received_data.get('tableIDs', [])
        # parsed_data = parse_qs(received_data)
        received_table_ids = list(map(str, received_data['tableIDs']))

        app.logger.info(f"received table ids: {received_table_ids}")

        for table_id in list(session['table_data'].keys()):
            if table_id not in received_table_ids:
                del session['table_data'][table_id]
                del session['output_df_per_result'][table_id]
                del session['results'][table_id]
                app.logger.info(f"deleted tab: {table_id}")
        session.modified = True
        print(f"table_ids_sync endpoint: {session['table_data'].keys()}")
        return jsonify({'success': True, 'message': 'Table data updated successfully'})

    except KeyError:
        app.logger.info("tableIDs not found in ajax post request.")
        return jsonify({'status': 'error', 'message': 'Invalid request data'}), 400
    except Exception as e:

        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/sync_tab_counter', methods=['GET'])
def sync_tab_counter():
    last_number = list(session['table_data'].keys())[-1]
    return jsonify({'lastNumber': last_number})


@app.route('/create_copy', methods=['POST'])
def create_copy():

    tableID = str(request.form.get('tableID'))

    session['table_data'][tableID] = deepcopy(table_dict)
    app.logger.info(f"table_data in {session['user']['name']}'s session added to table id: {tableID}")
    session.modified = True
    return jsonify({"success": True, "table_id": tableID})


@app.route('/channel_delete', methods=['POST'])
def channel_delete():
    try:
        deleted_tab = str(request.json.get("tabID"))
        app.logger.info(f"deleted tab: {deleted_tab}")
        session['table_data'].pop(deleted_tab)
        session['output_df_per_result'].pop(deleted_tab)
        session['results'].pop(deleted_tab)
        session.modified = True
        print(f"channel_delete endpoint: {session['table_data'].keys()}")
        return jsonify({"success": "tab removed succesfully"})
    except Exception as e:
        return jsonify({"exception": "error removing tab"})


@app.route('/channel_main', methods=['GET'])
def channel_main():
    app.logger.info(f"channel_main endpoint table_data keys: {session['table_data'].keys()}")
    return jsonify(session['table_data'])


@app.route('/table_data_editor', methods=['POST'])
def table_data_editor():

    try:
        data = request.get_json()
        print(data)
        table_id = str(data['tableId'])
        print(table_id)
        target_table = session['table_data'][table_id]
        if data['action'] == 'edit':
            for row_id, changes in data['data'].items():
                row_index = int(row_id) - 1
                for field, new_value in changes.items():
                    session['table_data'][table_id][row_index][field] = new_value
        print(f"table_data_editor endpoint: {session['table_data'].keys()}")
        session.modified = True
        return jsonify(data=target_table)
    except Exception as e:
        print("error processing data:", str(e))
        response = {
            'data': 'error',
            'status': 'error'
        }
    print(f"table_data_editor (error) endpoint: {session['table_data'].keys()}")
    return jsonify(response)


@app.route('/export_data')
def export_data():
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        all_input = pd.read_sql_table('All_Channel_Inputs', engine)
        laydown = pd.read_sql_table('All_Laydown', engine)
        all_index = pd.read_sql_table('All_Index', engine)

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