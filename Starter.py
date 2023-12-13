
# %% --------------------------------------------------------------------------
# initial setup
# -----------------------------------------------------------------------------

from pbiembedservice import PbiEmbedService
from utils import Utils
from flask import Flask, render_template, send_file, jsonify, request, url_for, redirect
from modelsum import test_model
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib
matplotlib.use("agg")
import numpy as np
import pandas as pd
import seaborn as sns
import base64
import random
import json
import os
import sys
from io import BytesIO
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import parse_qs
from pyomo_opt import Optimiser
from sqlalchemy import create_engine, text, Column, DateTime, Integer
from sqlalchemy.orm import Session, declarative_base
import datetime
from sqlalchemy.exc import SQLAlchemyError
import urllib.parse
import traceback
import psycopg2
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import secrets
from werkzeug.security import check_password_hash

app = Flask(__name__)

engine = create_engine('postgresql://postgres:'+urllib.parse.quote_plus("Gde3400@@")+'@192.168.1.2:5432/CPW Blueprint')

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:'+urllib.parse.quote_plus("Gde3400@@")+'@192.168.1.2:5432/CPW Blueprint'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secrets.token_hex()

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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


csvfile = os.path.join(sys.path[0], "Bakers_Dog_Meal_Conv.csv")
GROUPED_VARS = os.path.join(sys.path[0], "data/grouped_vars.json")
settings_json = os.path.join(sys.path[0], "data/settings.json")
annual_profile_jpg = os.path.join(sys.path[0], "static/images/annual_profile.png")
adstock_json = os.path.join(sys.path[0], "data/adstock.json")
channel_inputs_filepath = os.path.join(sys.path[0], "channel inputs.csv")

# VARIABLE_LIST = os.path.join(sys.path[0], "data/table.json")

json_dest = os.path.join(sys.path[0], "data/table.json")
data_dest = os.path.join(sys.path[0], "data/data.json")
varlist_dest = os.path.join(sys.path[0], "data/varlist.json")
sign_json = os.path.join(sys.path[0], "data/sign.json")
set_json = os.path.join(sys.path[0], "data/setGroups.json")
input_file = json_dest
output_file = data_dest

def csv_to_json(filepath):
    df = pd.read_csv(filepath)
    jsonstring = pd.DataFrame.to_json(df)
    json_object = json.dumps(jsonstring, indent=4)
    with open(channel_json, "w") as outfile:
        outfile.write(json.loads(json_object))
    pass

@app.route('/data', methods=['GET', 'POST', 'DELETE'])
def handle_ajax():
    with open(output_file) as file:
        data = json.load(file)
    print(request.content_type)
    print(request.method)

    if request.method == 'POST':
        payload = request.get_data(parse_form_data=True)
        decoded_payload = payload.decode()
        parsed_payload = parse_qs(decoded_payload)

        if 'action' in parsed_payload:
            action = parsed_payload['action'][0]
            print(action)

            if action == 'create':
                new_variable = parsed_payload.get('data[0][variable]', [''])[0]
                new_adstock = parsed_payload.get('data[0][adstock]', [''])[0]

                max_row_id = max(int(row['DT_RowId'][3:]) for row in data['data'])
                new_row_id = f'row{max_row_id + 1}'

                # Create a new row with the provided data
                new_row = {
                    'DT_RowId': new_row_id,
                    'variable': new_variable,
                    'toggle': '',
                    'inModel': '',
                    'coefficient': '',
                    'stdError': '',
                    't_value': '',
                    'p_value': '',
                    '95CILow': '',
                    '95CIHigh': '',
                    'insig': '',
                    'adstock': new_adstock,
                    'pctCont': ''
                }

                # Append the new row to the data list
                data['data'].append(new_row)

                with open(output_file, 'w') as file:
                    json.dump(data, file, indent=4)

                return jsonify(new_row)

            elif action == 'edit':
                print(parsed_payload.items())
                for updated_row_key, updated_row_value in parsed_payload.items():
                    print(updated_row_key)
                    print(updated_row_value)
                    row_index = None

                    if updated_row_key.startswith('data[row'):
                        row_index = updated_row_key.split('row')[1].split(']')[0]
                        print(row_index)

                    if row_index is not None:
                        for row in data['data']:

                            if str(row['DT_RowId']) == "row" + row_index:
                                print(row_index)
                                print("jejeje")
                                if updated_row_key.endswith('][variable]'):
                                    if row['variable'] != updated_row_value[0]:
                                        row['variable'] = updated_row_value[0]
                                        print(row['variable'])
                                        break
                                elif updated_row_key.endswith('][adstock]'):
                                    if row['adstock'] != updated_row_value[0]:
                                        row['adstock'] = updated_row_value[0]
                                        print(row['adstock'])
                                        break

                    with open(output_file, 'w') as file:
                        json.dump(data, file, indent=4)

                        response = {
                            'data': [
                                {
                                    'DT_RowId': row['DT_RowId'],
                                    'variable': row['variable'],
                                    'toggle': row['toggle'],
                                    'inModel': row['inModel'],
                                    'coefficient': row['coefficient'],
                                    'stdError': row['stdError'],
                                    't_value': row['t_value'],
                                    'p_value': row['p_value'],
                                    '95CILow': row['95CILow'],
                                    '95CIHigh': row['95CIHigh'],
                                    'insig': row['insig'],
                                    'adstock': row['adstock'],
                                    'pctCont': row['pctCont']
                                }

                            ]
                        }
                        print(response)
                        return jsonify(response)
            elif action == "remove":
                empty_obj = {}
                return jsonify(empty_obj)

    elif request.method == 'GET':
        print("getting")
        response_data = data['data']

        response = {
            'data': response_data,
        }
        return jsonify(response)


    elif request.method == 'DELETE':
        row_id = request.args.get('row_id', '')

        for row in data['data']:
            if row['DT_RowId'] == row_id:
                data['data'].remove(row)
                break

        with open(output_file, 'w') as file:
            json.dump(data, file, indent=4)

        response = {'status': 'success', 'message': 'Row deleted successfully'}
        return jsonify(response)

    response = {'status': 'error', 'message': 'Invalid request'}
    return jsonify(response)


@app.route('/toggle_states', methods = ['POST'])
def toggle_states():
    try:
        data = request.json
        print(data)
        print(type(data))
        toggle_states = data
        print(toggle_states)
        return jsonify({"message": "Toggle states saved successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# OPTIMISER FILE PATHS

laydown_filepath = os.path.join(sys.path[0], "optimiser input data/UK_Laydown_v3.csv")
channel_json = os.path.join(sys.path[0], "data/channel.json")
channel_input = pd.read_csv("optimiser input data/UK_Channel_Inputs_v3.csv")
channel_input.drop(columns='Unnamed: 0', inplace=True)

channel_dict = {1:channel_input.to_dict("records")}
ST_laydown = pd.read_csv(laydown_filepath)
ST_laydown = ST_laydown.fillna(0)
print(ST_laydown.columns)
streams = []
for var in channel_dict[1]:
    streams.append(var['Channel'])

ST_laydown_dates = ST_laydown['Time_Period']

with open(channel_json, "w") as file:
    json.dump(channel_dict, file, indent=4)

with open(channel_json) as file:
    ST_channel_input = json.load(file)



opt_betas_dict = Optimiser.beta_opt(laydown=ST_laydown, channel_input=channel_dict[1])
channel_input['Beta'] = list(opt_betas_dict.values())
channel_dict = {"1":channel_input.to_dict("records")}
table_data = channel_dict
for var in table_data["1"]:
    var['Laydown'] = ST_laydown[var['Channel']].tolist()

max_budget = 0
results = {}
# %% --------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------

@app.route('/optimise', methods = ['POST'])
def optimise():

    if request.method == "POST":
        data = request.json
    
    table_id = str(data['tableID'])
    obj_func = data['objectiveValue']
    exh_budget = data['exhaustValue']
    max_budget = int(data['maxValue'])
    num_weeks = 1000
    blend = data['blendValue']
    
    ST_channel_input = table_data[table_id]

    global results
    streams = [entry['Channel'] for entry in ST_channel_input]

    LT_laydown = ST_laydown
    LT_channel_input = ST_channel_input

    if blend.lower() == "blend":
        if obj_func.lower() == "profit":
            ST_res = list(Optimiser.profit_max(channel_input = ST_channel_input, laydown = ST_laydown, exh_budget=exh_budget, max_budget=max_budget, num_weeks=num_weeks).values())
            LT_res = list(Optimiser.profit_max(channel_input = LT_channel_input, laydown = LT_laydown, exh_budget=exh_budget, max_budget=max_budget, num_weeks=num_weeks).values())
            blend_list = list(np.add(ST_res, LT_res))
            blend_res = dict(zip(streams, blend_list))
            results[table_id] = blend_res
        elif obj_func.lower() == 'revenue':
            ST_res = list(Optimiser.revenue_max(channel_input = ST_channel_input, laydown = ST_laydown, exh_budget=exh_budget, max_budget=max_budget, num_weeks=num_weeks).values())
            LT_res = list(Optimiser.revenue_max(channel_input = LT_channel_input, laydown = LT_laydown, exh_budget=exh_budget, max_budget=max_budget, num_weeks=num_weeks).values())
            blend_list = list(np.add(ST_res, LT_res))
            blend_res = dict(zip(streams, blend_list))
            results[table_id] = blend_res
        elif obj_func.lower() == 'roi':
            ST_res = list(Optimiser.roi_max(channel_input = ST_channel_input, laydown = ST_laydown, exh_budget=exh_budget, max_budget=max_budget, num_weeks=num_weeks).values())
            LT_res = list(Optimiser.roi_max(channel_input = LT_channel_input, laydown = LT_laydown, exh_budget=exh_budget, max_budget=max_budget, num_weeks=num_weeks).values())
            blend_list = list(np.add(ST_res, LT_res))
            blend_res = dict(zip(streams, blend_list))
            results[table_id] = blend_res
        
        return jsonify(results), 200
    elif blend.lower() == "st":
        if obj_func.lower() == "profit":
            results[table_id] = Optimiser.profit_max(channel_input = ST_channel_input, laydown = ST_laydown, exh_budget=exh_budget, max_budget=max_budget, num_weeks=num_weeks)
        elif obj_func.lower() == 'revenue':
            results[table_id] = Optimiser.revenue_max(channel_input = ST_channel_input, laydown = ST_laydown, exh_budget=exh_budget, max_budget=max_budget)
        elif obj_func.lower() == 'roi':
            results[table_id] = Optimiser.roi_max(channel_input = ST_channel_input, laydown = ST_laydown, exh_budget=exh_budget, max_budget=max_budget)
        return jsonify(results), 200
    elif blend.lower() == "lt":
        if obj_func.lower() == "profit":
            results[table_id] = Optimiser.profit_max(channel_input = LT_channel_input, laydown = LT_laydown, exh_budget=exh_budget, max_budget=max_budget, num_weeks=num_weeks)
        elif obj_func.lower() == 'revenue':
            results[table_id] = Optimiser.revenue_max(channel_input = LT_channel_input, laydown = LT_laydown, exh_budget=exh_budget, max_budget=max_budget)
        elif obj_func.lower() == 'roi':
            results[table_id] = Optimiser.roi_max(channel_input = LT_channel_input, laydown = LT_laydown, exh_budget=exh_budget, max_budget=max_budget)
        print(results)
        return jsonify(results), 200

@app.route('/results_output', methods = ['POST'])
def results_output():

    tab_names = dict(request.json)

    raw_input_data = channel_input.to_dict("records")
    
    current_budget_list = [entry['Current_Budget'] for entry in raw_input_data]
    current_budget_dict = dict(zip(streams, current_budget_list))

    cost_per_list = [float(entry['CPU']) for entry in raw_input_data]
    cost_per_dict = dict(zip(streams, cost_per_list))

    current_budget_laydown_dict = {'Time_Period':list(ST_laydown_dates)}
    for stream in streams:
        current_budget_laydown_dict[stream] = [i * cost_per_dict[stream] for i in list(ST_laydown.fillna(0)[stream])]
    ST_laydown['Time_Period'] = ST_laydown_dates
    ST_laydown.set_index("Time_Period", inplace=True)

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
    for x in ST_laydown.columns:
        recorded_impressions[x] = ST_laydown.fillna(0)[x].to_list()

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

    current_rev_dict = {'Time_Period':list(ST_laydown.index)}

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
        opt_rev_dict = {'Time_Period':list(ST_laydown.index)}
        for stream in streams:
            opt_rev_dict[stream] = rev_per_stream(stream, current_budget_dict[stream])

        def daily_budget_from_pct_laydown(stream, budget):
            cost_per_stream = cost_per_dict.get(stream, 1e-6)  # Set a small non-zero default cost
            
            pct_laydown = []
            for x in range(len(recorded_impressions[stream])):
                try:
                    pct_laydown.append(recorded_impressions[stream][x]/sum(recorded_impressions[stream]))
                except:
                    pct_laydown.append(0)
            return pct_laydown

        opt_budget_laydown_dict = {'Time_Period':list(ST_laydown.index)}
        for stream in streams:
            opt_budget_laydown_dict[stream] = [i * opt_budget_dict[stream] for i in daily_budget_from_pct_laydown(stream, opt_budget_dict[stream])]

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

        opt_rev_dict = {'Time_Period':list(ST_laydown.index)}
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
    
    concat_df['Time_Period'] = pd.to_datetime(concat_df['Time_Period'], format="%d/%m/%Y").dt.date
    
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
    data = {
        "x": poly_x.tolist(),
        "y": poly_y.tolist(),
        "lobf": lobf.tolist()
    }

    return jsonify(data)

@app.route('/blueprint_results')
def blueprint_results():
    return render_template('blueprint_results.html')

@app.route('/date_range', methods = ['GET','POST'])
def date_range():
    start_date = list(ST_laydown_dates)[1]
    print(start_date)
    end_date = list(ST_laydown_dates)[-1]
    print(end_date)
    return jsonify({"startDate":start_date, "endDate":end_date})

@app.route('/budget_optimiser')
def budget_optimiser():
    return render_template('Budget Optimiser.html')

@app.route('/create_copy', methods = ['POST'])
def create_copy():
    global table_data

    tableID = str(request.form.get('tableID'))
    channel_dict = channel_input.to_dict("records")
    for var in channel_dict:
        var['Laydown'] = ST_laydown[var['Channel']].tolist()
    if tableID not in table_data.keys():
        table_data[tableID] = channel_dict
    print(len(table_data))
    return jsonify({"success": True, "table_id": tableID})

import copy
@app.route('/channel', methods = ['GET', 'PUT'])
def channel():
    print("reaching /channel")
    if request.method == 'GET':
        print("getting")
        return jsonify(table_data)

@app.route('/channel_delete', methods = ['POST'])
def channel_delete():
    deleted_tab = str(request.json.get("tabID"))
    print(deleted_tab)
    table_data.pop(deleted_tab)
    return jsonify({"success":"tab removed succesfully"})

@app.route('/channel_main', methods = ['GET'])
def channel_main():
    print(table_data.keys())
    
    return jsonify(table_data)

@app.route('/varlist', methods = ['GET', 'POST'])
def varlist():

    with open(varlist_dest) as file:
        data = json.load(file)
        data = [entry['variable'] for entry in data['data']]
    with open(set_json) as file:
        setGroups = json.load(file)
    with open(GROUPED_VARS) as file:
        groups = json.load(file)

    vars_in_set = [element for innerList in list(setGroups.values()) for element in
                               innerList]

    # with open(json_dest) as file:
    #     variables = json.load(file)
    #     variables = list(variables['Variable'].values())
    # with open(varlist_dest) as file:
    #     variables = json.load(file)
    #     variables = [entry['variable'] for entry in variables['data']]


    # ------------------------------------------------------------------
    # this updates the sets file when changes to the GV file are made
    # above needs to be replaced with a list of the ungrouped variables and group names


    list_of_vars_in_a_group = [element for innerList in list(groups.values()) for element in
                               innerList]

    vars_not_in_group = [item for item in data if item not in list_of_vars_in_a_group]
    data = list(groups.keys()) + vars_not_in_group


    vars_not_in_set = [item for item in data if item not in vars_in_set]
    data = list(setGroups.keys()) + vars_not_in_set

    vars_in_set = [element for innerList in list(setGroups.values()) for element in innerList]
    print('vars in set', vars_in_set)
    # List of variables that haven't yet been selected
    vars_not_in_set = [item for item in data if item not in vars_in_set]


    if request.method == 'GET':
        print("getting")
        # response_data = data['data']
        response_data = [{'variable': item} for item in data]
        print(response_data)
        response = {
            'data': response_data,
        }
        return jsonify(response)

@app.route('/update_data', methods=['POST'])
def update_data():

    if not request.is_json:
        return jsonify({"message": "Invalid request format"}), 400

    try:
        updated_data = request.get_json()
        data = updated_data  # Update the global data with the new JSON data
        with open(output_file, 'w') as file:
            json.dump(data, file, indent=4)

        return jsonify({"message": "Data updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route('/save_indices', methods=['POST'])
def save_indices():
    data = request.get_json()
    with open(sign_json, 'w') as file:
        json.dump(data, file)
    return jsonify({'message': 'variable sign saved successfully'})

@app.route('/load_indices')
def load_indices():
    try:
        with open(sign_json, 'r') as file:
            icon_indices = json.load(file)
        return jsonify(icon_indices)
    except FileNotFoundError:
        return jsonify({})

# Load configuration for PBI
app.config.from_object('config.BaseConfig')

@app.route('/')
def welcome_page():
    return render_template('Welcome.html')

# Get request required pending login db sorted
@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('Home.html')

@app.route('/login', methods = ['POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('psw')

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('/home'))

@app.route('/data_viewer')
def data_viewer():
    return render_template('Data Viewer.html')

@app.route('/model_creator')
def model_creator():
   
    with open(output_file) as f:
        data = json.load(f)

    with open(GROUPED_VARS) as file:
        groups = json.load(file)

    with open(set_json) as file:
        setGroups = json.load(file)

    # with open(json_dest) as file:
    #     variables = json.load(file)
    #     variables = list(variables['Variable'].values())

    with open(varlist_dest) as file:
        variables = json.load(file)
        variables = [entry['variable'] for entry in variables['data']]

    list_of_vars_in_a_group = [element for innerList in list(groups.values()) for element in
                               innerList]

    # List of variables that haven't yet been selected
    # the following just takes things that are in the original vriable list but not in var in a group.
    vars_not_in_group = [item for item in variables if item not in list_of_vars_in_a_group]
    variables = list(groups.keys()) + vars_not_in_group
    # will need something here to differentiate the vars not in a group to thoese in a group
    setGroups_html = updating_Sets(setGroups)
    variableList_html = updating_variableList(setGroups, variables)
    group_html = updating_modal3(groups, vars_not_in_group)
    dropdown_html = updating_dropdown3(groups)
    columnsForSplit = csv_to_df()
    # columnsForSplit = jsonify({'columnsForSplit': columnsForSplit})

    df = pd.read_csv(csvfile)
    target_var_list = df.columns.to_list()
    

    # print('i made it here', columnsForSplit)

    with open(adstock_json) as file:
        adstock_data = json.load(file)
        adstock = [entry['variable'] for entry in adstock_data['data']]

    return render_template('Model Creator.html', data=data, adstock=adstock, variables=variables, group_html=group_html, dropdown_html=dropdown_html, setGroups_html=setGroups_html, variableList_html=variableList_html, columnsForSplit=columnsForSplit, targetList=target_var_list)


@app.route('/dashboard')
def dashboard():
    return render_template('Dashboard.html')

@app.route('/send_data', methods=['POST'])
def handle_data():
    data = request.get_json()
    # Process the data as needed (e.g., save to a database, perform calculations)
    print(data)
    # Return a response to the frontend if needed
    return jsonify({"message": "Saved successfully!"})

@app.route('/model_landing_page')
def model_landing_page():

    csv_to_json(csvfile)
    with open(output_file) as f:
        data = json.load(f)

    with open(GROUPED_VARS) as file:
        groups = json.load(file)

    with open(set_json) as file:
        setGroups = json.load(file)

    # with open(json_dest) as file:
    #     variables = json.load(file)
    #     variables = list(variables['Variable'].values())

    with open(varlist_dest) as file:
        variables = json.load(file)
        variables = [entry['variable'] for entry in variables['data']]

    list_of_vars_in_a_group = [element for innerList in list(groups.values()) for element in
                               innerList]

    # List of variables that haven't yet been selected
    # the following just takes things that are in the original vriable list but not in var in a group.
    vars_not_in_group = [item for item in variables if item not in list_of_vars_in_a_group]
    variables = list(groups.keys()) + vars_not_in_group
    # will need something here to differentiate the vars not in a group to thoese in a group
    setGroups_html = updating_Sets(setGroups)
    variableList_html = updating_variableList(setGroups, variables)
    group_html = updating_modal3(groups, vars_not_in_group)
    dropdown_html = updating_dropdown3(groups)
    columnsForSplit = csv_to_df()
    # columnsForSplit = jsonify({'columnsForSplit': columnsForSplit})
    print('i made it here', columnsForSplit)

    return render_template('model_landing_page_test.html', data=data , variables=variables, group_html=group_html, dropdown_html=dropdown_html, setGroups_html=setGroups_html, variableList_html=variableList_html, columnsForSplit=columnsForSplit)


@app.route('/grouping_calculations3', methods=['POST'])
def grouping_calculations3():
    default_group_name = ''

    with open(GROUPED_VARS) as file:
        groups = json.load(file)

    # with open(json_dest) as file:
    #     variables = json.load(file)
    #     variables = list(variables['Variable'].values())

    with open(varlist_dest) as file:
        variables = json.load(file)
        variables = [entry['variable'] for entry in variables['data']]

    if request.method == 'POST':

        form_data = request.get_json()
        buttonValue = form_data['buttonValue']

        if buttonValue != 'renaming' and buttonValue !='splitToIncr':
            selected_checkboxes = form_data['selectedList']
            default_group_name = ', '.join(selected_checkboxes)
            print('selecting Incr', default_group_name)
        # When the confirm groups button is pressed
        if buttonValue == 'ButtonConfirmGroup':

            groups, result = updateGroups(groups, form_data, selected_checkboxes)
            selectedGroupList = form_data['selectedGroupList']

            if len(selectedGroupList) > 0:
                default_group_name = ' and '.join(selectedGroupList)
            else:
                default_group_name = ','.join(result)

            group = {default_group_name: result}  # the new group being created
            groups.update(group)  # Updates the groups dictionary, adds the newly created group
            print('seclyterhsth', default_group_name)
        # Adding variabels to existing groups
        if buttonValue == "dropDownChange":

            groups, result = updateGroups(groups, form_data,  selected_checkboxes)
            selectedGroupName = form_data['selectedOption'].replace('Radio', '')
            groups[selectedGroupName].extend(result)  # adds the selected variables to the new group

        # Renaming Existing Groups
        if buttonValue == "renaming":

            old_group_name = form_data.get('previousName')
            new_group_name = form_data.get('newName')

            # loop through dicionary keys
            # replace key where key = oldGroupName with newGroup Name
            if old_group_name in groups.keys():
                groups[new_group_name] = groups.pop(old_group_name)

        # Ungrouping variables
        if buttonValue == "ButtonUngroup":
            selectedGroupList = form_data['selectedGroupList']

            for key in selectedGroupList:
                if key in groups:
                    del groups[key]

            for key, value in groups.items():
                if isinstance(value, list):
                    groups[key] = [x for x in value if x not in selected_checkboxes]
                else:
                    if value in selected_checkboxes:
                        del groups[key]


        # if statement for drag and drop
        if buttonValue == "droppingVariables":

            groups, result = updateGroups(groups, form_data, selected_checkboxes)
            selectedGroupName = form_data['selectedOption'].replace('dropzone', '')

            # adds the selected variables to the new group
            groups[selectedGroupName].extend(result)

        if buttonValue == "splitToIncr":
            # add incr variable to var list
            # dump the json
            new_var = form_data['autoSelectedVariable'] + "_Incremental"

            new_entry = {"variable": new_var}
            with open(varlist_dest) as file:
                variables = json.load(file)

                variables['data'].append(new_entry)
                print(variables)
            with open(varlist_dest, 'w') as file:
                json.dump(variables, file)
                file.flush()
                variables = [entry['variable'] for entry in variables['data']]

        # Get list of grouped vars
        list_of_vars_in_a_group = [element for innerList in list(groups.values()) for element in
                                   innerList]

        # List of variables that haven't yet been selected
        vars_not_in_group = [item for item in variables if item not in list_of_vars_in_a_group]

    for key in list(groups.keys()):
        if not groups[key]:
            del groups[key]

    dropdown_html = updating_dropdown3(groups)
    group_html = updating_modal3(groups, vars_not_in_group)

    with open(GROUPED_VARS, 'w') as file:
        json.dump(groups, file)
        file.flush()


# updates the setgroups upon changes to the group variable tab
    with open(set_json) as file:
        setGroups = json.load(file)
        print('setGroups')
        # need to remove var from set list if group has been removed
        variables = list(groups.keys()) + vars_not_in_group
        setGroups = {key: [value for value in values if value in variables] for key, values in setGroups.items()}
    with open(set_json, 'w') as file:
        json.dump(setGroups, file)
        file.flush()


    return jsonify({'group_html': group_html, 'dropdown_html': dropdown_html, 'default_group_name': default_group_name})


def updateGroups(groups, form_data, selected_checkboxes):

    selectedGroupList = form_data['selectedGroupList']
    result = []

    for key in selectedGroupList:
        result.extend(groups[key])

    for value in selected_checkboxes:
        if value not in result:
            result.append(value)

    for key, value in groups.items():
        if isinstance(value, list):
            groups[key] = [x for x in value if x not in result]
        else:
            if value in result:
                del groups[key]


    return groups, result

def updating_modal3(groups, vars_not_in_group):

    # as all the grouping mechanics are handled here, we should be able to do this at the end of the above function, just looping through
    # the keys and values of the dictionary, as we already do in html.
    group_html = "<ul id='variableUL'>"
    # first looping through the dictionary, doing keys as headings and values as as variables
    for group_name, group_items in groups.items():

        group_html += f"<ul class='dropzones' ondragover='event.preventDefault()' ondrop='handleDrop(event)' id='dropzone{group_name}'><li ondblclick='listenForDoubleClick(this)' draggable= 'true' ondragstart='handleDragStart(event)' class='selectingGroups'  onblur='this.contentEditable=true;' id=editable.'{ group_name }'>{ group_name }</li>"
        group_html += f"<button class='collapsible-button expandingContainer' onclick='collapseExpand(event)'></button>"
        if group_items:
            group_html += "<ul class='content' style='display: block'>"
            for item in group_items:
                group_html += f"<li draggable= 'true' ondragstart='handleDragStart(event)' id='{item}' class='selectingItems content' width='auto' name='{item}' value='checkboxes{item}'>{item}</li>"
            group_html += "</ul>"
        group_html += "</ul>"

    for variable in vars_not_in_group:
        group_html += f"<li draggable= 'true' ondragstart='handleDragStart(event)' id='ind.{ variable }' class='selectingItems' width='auto' name='{variable}' value='checkboxes{ variable }'>{variable}</li> "
    group_html += "</ul>"

    return group_html


def updating_dropdown3(groups):
    # this is the code to dynamically update the dropdown options without refreshing the page.
    dropdown_html = f"<select id='myDropdown' style='width: 200px;'>"
    dropdown_html += f"<option disabled selected>Select a group</option>"
    for key in groups.keys():
        dropdown_html += f"<option  value='Radio{ key }' id='{ key }'  name='radiooo'> { key } </option>"

    dropdown_html += f"</select>"

    return dropdown_html


# Set Calculations
@app.route('/setCalculations', methods = ['POST'])
def setCalculations():

    # load the setGroups JSON file
    # with open(json_dest) as file:
    #     variables = json.load(file)
    #     variables = list(variables['Variable'].values())

    with open(varlist_dest) as file:
        variables = json.load(file)
        variables = [entry['variable'] for entry in variables['data']]


    # ------------------------------------------------------------------
    # this updates the sets file when changes to the GV file are made
    # above needs to be replaced with a list of the ungrouped variables and group names
    with open(GROUPED_VARS) as file:
        groups = json.load(file)

    list_of_vars_in_a_group = [element for innerList in list(groups.values()) for element in
                               innerList]

    vars_not_in_group = [item for item in variables if item not in list_of_vars_in_a_group]
    variables = list(groups.keys()) + vars_not_in_group

    set_name = None
    with open(set_json) as file:
        setGroups = json.load(file)
        # need to remove var from set list if group has been removed
        # setGroups = {key: [value for value in values if value in variables] for key, values in setGroups.items()}
        # print(setGroups)

    if request.method == 'POST':

        form_data = request.get_json()
        buttonValue = form_data['buttonValue']



        # on modal open load sets from JSON
        # if buttonValue == 'openSetModal':
        #     with open(DATA_FILE) as file:
        #         setGroups = json.load(file)
        #         print(setGroups)

        if buttonValue == 'createSet':

            setGroups, set_name = updateSetGroups(setGroups, form_data, buttonValue)

            # with open(DATA_FILE, 'w') as file:
            #     json.dump(setGroups, file)
            #     file.flush()

            # add this new empty set to the setGroups

        elif buttonValue == 'renameSet':
            # read in the old and new group name
            old_group_name = form_data.get('previousName')
            new_group_name = form_data.get('newName')
            # loop through dicionary keys
            # replace key where key = oldGroupName with newGroup Name

            if old_group_name in setGroups.keys():
                setGroups[new_group_name] = setGroups.pop(old_group_name)

        elif buttonValue == "droppingVariables":

            setGroups, set_name = updateSetGroups(setGroups, form_data, buttonValue)

            # selectedGroupName = form_data['selectedOption'].replace('dropzone', '')
            #
            # # adds the selected variables to the new group
            # groups[selectedGroupName].extend(result)



        elif buttonValue == 'deleteSet':

            print('we made it here')
            selectedSets = form_data['selectedSetsList']

            # loop through dictionary, and delete them keys
            for key in selectedSets:
                del setGroups[key]
            print('ergfsreg', setGroups)

        elif buttonValue == 'droppingVariablesBack':

            varsForSetsList = form_data['varsForSetsList']
            for key, value in setGroups.items():
                if isinstance(value, list):
                    setGroups[key] = [x for x in value if x not in varsForSetsList]
                else:
                    if value in varsForSetsList:
                        del setGroups[key]

    for key in list(setGroups.keys()):
        if not setGroups[key]:
            del setGroups[key]

    # update the setGroups JSON
    with open(set_json, 'w') as file:
        json.dump(setGroups, file)
        file.flush()

    print('hello')
    setGroups_html = updating_Sets(setGroups)
    variableList_html = updating_variableList(setGroups, variables)

    return jsonify({'setGroups_html': setGroups_html, 'variableList_html': variableList_html, 'set_name':set_name}), setGroups



# creating the html item for second box.
def updating_Sets(setGroups):

    # with open(DATA_FILE) as file:
    #     setGroups = json.load(file)
    # print(setGroups.items())
    # need to loop through the set groups dictionary and create our html element

    setGroups_html = ''
    for key, value in setGroups.items():
        setGroups_html += f"<li class='dropzones' ondragover='event.preventDefault()' ondrop='handleDropSet(event)' id='dropzone{key}'><p class='allSets' ondblclick='listenForDoubleClickSet(this)' id='editable.{key}'>{key}</p>"
        setGroups_html += f"<button class='collapsible-buttonAG expandingContainerAG' onclick='collapseExpandAG(event)'></button>"
        if value:
            setGroups_html += "<ul class='content' style='display: block'>"
            for item in value:
                setGroups_html += f"<li class='varsForSets' draggable='true' ondragstart='handleDragStartSet(event)'>{item}</li>"
            setGroups_html += "</ul>"
        setGroups_html += "</li>"
    # print(setGroups_html)

    return setGroups_html


def updating_variableList(setGroups, variables):

    # with open(GROUPED_VARS) as file:
    #     groups = json.load(file)
    #
    # list_of_vars_in_a_group = [element for innerList in list(groups.values()) for element in
    #                            innerList]
    #
    # vars_not_in_group = [item for item in variables if item not in list_of_vars_in_a_group]
    # variables = list(groups.keys()) + vars_not_in_group

    vars_in_set = [element for innerList in list(setGroups.values()) for element in innerList]
    print('vars in set', vars_in_set)
    # List of variables that haven't yet been selected
    vars_not_in_set = [item for item in variables if item not in vars_in_set]
    print('vars not in set', vars_not_in_set)
    variableList_html = "<ul id='variableAG'>"
    for value in vars_not_in_set:
        variableList_html += f"<li class='varsForSets' draggable='true' ondragstart='handleDragStartSet(event)'>{value}</li> "
    variableList_html += "</ul>"
    print('variable list', variableList_html)
    return variableList_html



# updates the sets dictionary
def updateSetGroups(setGroups, form_data, buttonValue):

    varsForSetsList = form_data['varsForSetsList']
    result = []
    print('before updating', setGroups)
    for value in varsForSetsList:
        if value not in result:
            result.append(value)

    for key, value in setGroups.items():
        if isinstance(value, list):
            setGroups[key] = [x for x in value if x not in result]
        else:
            if value in result:
                del setGroups[key]

    if buttonValue == 'createSet':
        set_name = 'Set ' + str(len(setGroups.keys()) + 1)
        group = {set_name: result}  # the new group being created
        setGroups.update(group)
        print('updating', setGroups)
    else:
        set_name = None

    if buttonValue == 'droppingVariables':
        selectedSetName = form_data['selectedOption'].replace('dropzone', '')

        # adds the selected variables to the new group
        setGroups[selectedSetName].extend(result)

    return setGroups, set_name

# --------------------------------------------------------------------------------------------------------
# selects columns available for incremental split
@app.route('/checkIncrementalList', methods=['GET'])
def csv_to_df():
    
    # varlist_dest = os.path.join(sys.path[0], "data/varlist.json")
    excelSheet = pd.read_csv(csvfile)
    dy = excelSheet.select_dtypes(exclude=['object', 'datetime'])
    dy = dy.loc[:, (dy.min() > 0)]
    columnsForSplit = list(dy.columns)

     # return jsonify({'columnsForSplit': columnsForSplit})
    return columnsForSplit
# @app.route('/incrementalSplit', methods=['POST'])
# def incrementalSplit():
#     # here want to grab the selected variable, split it into incremental and put it back into the variable list as incremental
#     # grab the value
#     form_data = request.get_json()
#     buttonValue = form_data['buttonValue']
#     varToSplit = form_data['selectedVariableForIncr']
#     print('vartosplit', varToSplit)
#     # need to think about how we want to add it to the incr
#     return


@app.route('/handle_agg', methods=['POST'])
def handle_agg():
    with open(output_file) as file:
        data = json.load(file)

    if not request.is_json:
        return jsonify({"message": "Invalid request format"}), 400

    try:
        # Get the selected data from the frontend
        selected_rows = request.json.get("selectedRows", [])
        if not selected_rows:
            return jsonify({"message": "No rows selected for aggregation"}), 400

        # Get the aggregation methods from the frontend
        column_aggregation = request.json.get("columnAggregation", {})

        # Convert selected_rows to a NumPy array for efficient aggregation
        selected_data = np.array([list(row.values()) for row in selected_rows])

        # Loop through the selected columns and apply aggregation methods
        for column_name in column_aggregation:
            aggregation_method = column_aggregation.get(column_name)
            if aggregation_method == 'sum':
                column_index = data["columns"].index(column_name)
                aggregated_values = np.sum(selected_data[:, column_index].astype(float))
                data["data"][0][column_index] = str(aggregated_values)  # Update the aggregated value
            elif aggregation_method == 'average':
                column_index = data["columns"].index(column_name)
                aggregated_values = np.mean(selected_data[:, column_index].astype(float))
                data["data"][0][column_index] = str(aggregated_values)  # Update the aggregated value

        with open(output_file, 'w') as file:
            json.dump(data, file, indent=4)

        return jsonify({"message": "Data aggregated and updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route('/add_row', methods=['POST'])
def add_row():
    try:
        variable_name = request.form.get("variable")
        var_type = request.form.get("varType")
        with open(output_file, "r") as infile:
            data = json.load(infile)
        
        # Check if a row with the same variable name already exists
        existing_row = next((row for row in data['data'] if row.get('variable') == variable_name), None)
        if existing_row:
            return jsonify({"status": "error", "message": "Duplicate variable name. Row not added."}), 400

        # Generate a new 'DT_RowId' for the new row
        existing_row_ids = [int(row['DT_RowId'][3:]) for row in data['data'] if row.get('DT_RowId', '').startswith('row')]
        max_row_id = max(existing_row_ids) if existing_row_ids else 0
        new_row_id = f'row{max_row_id + 1}'

        new_row = {
            "DT_RowId": new_row_id,
            "variable": variable_name,
            "toggle": "",
            "inModel": "",
            "adstock": None,
            "varType": var_type,
            "coefficient": None,
            "stdError": None,
            "t_value": None,
            "p_value": None,
            "95CILow": None,
            "95CIHigh": None,
            "insig": None,
            "pctCont": None
        }

        data['data'].append(new_row)
        with open(output_file, "w") as outfile:
            json.dump(data, outfile, indent=4)

        return jsonify({"status": "success", "message": "Row added to table2."}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/remove_row", methods=["POST"])
def remove_row():
    try:
        # Get the variable name from the POST request data
        variable_name = request.form.get("variable")

        # Read the entire JSON data from the file
        with open(output_file, "r") as infile:
            data = json.load(infile)

        # Filter out the row with the matching variable name
        updated_data = [row for row in data["data"] if row["variable"] != variable_name]

        # Update the "data" key with the filtered data
        data["data"] = updated_data

        # Write the updated data back to the file
        with open(output_file, "w") as outfile:
            json.dump(data, outfile, indent=4)

        # Debug: Print a message when the removal is successful
        print(f"Row with variable '{variable_name}' removed from table2.")

        # Return success response
        return jsonify({"status": "success", "message": f"Row with variable '{variable_name}' removed from table2."}), 200

    except Exception as e:
        # Debug: Print the exception message for debugging purposes
        print("Error:", str(e))
        # Return error response if something goes wrong
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/getembedinfo', methods=['GET'])
def get_embed_info():
    '''Returns report embed configuration'''

    config_result = Utils.check_config(app)
    if config_result is not None:
        return json.dumps({'errorMsg': config_result}), 500

    try:
        print("trying to call pbiembedservice method")
        embed_info = PbiEmbedService().get_embed_params_for_single_report(app.config['WORKSPACE_ID'], app.config['REPORT_ID'])
        print("called method")
        return embed_info
    except Exception as ex:
        return json.dumps({'errorMsg': str(ex)}), 500


@app.route('/save_settings', methods=['POST'])
def save_settings():
    setData = request.get_json()
    print(setData)
    try:
        with open(settings_json, 'w') as file:
            json.dump(setData, file, indent=4)
        return jsonify({"status": "success", "message": "settings saved to json"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    

@app.route('/load_settings', methods=['GET'])
def load_settings():
    try:
        with open(settings_json, 'r') as f:
            data = json.load(f)
            return jsonify(data)
    except FileNotFoundError:
        return jsonify({})


@app.route('/corr_matrix', methods=['POST'])
def annual_profile_handle():
    try:
        df = pd.read_csv(csvfile)
        numeric_df = df.select_dtypes(include=[np.number])
        numeric_df.dropna(axis=1, how='all', inplace=True)
        numeric_df = numeric_df.loc[:, (numeric_df != 0).any(axis=0)]
        correlation_matrix = numeric_df.corr()
        sns.set(style="white")
        plt.figure(figsize=(16, 12))
        heatmap = sns.heatmap(correlation_matrix, 
                      annot=False, 
                      cmap="coolwarm", 
                      linewidths=.5, 
                      fmt=".2f",  # Format of annotations (two decimal places)
                      cbar=True,   # Include a color bar
                      xticklabels=True, 
                      yticklabels=True)
        plt.xticks(rotation=45)
        heatmap.set_xticklabels(heatmap.get_xticklabels(), fontsize=10)
        heatmap.set_yticklabels(heatmap.get_yticklabels(), fontsize=10)
        plt.savefig("fig.png")
    except e:
        return e
    try:
        return jsonify({"status": "success", "message": "new plot created"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/annual_profile')
def annual_profile():
    return render_template('annual_profile.html')


@app.route('/exog')
def exog():
    table_data = json.load(open('data/data.json', 'r'))
    group_data = json.load(open('data/grouped_vars.json', 'r'))
    set_data = json.load(open('data/setGroups.json', 'r'))
    toggle_json = json.load(open('data/sign.json', 'r'))


@app.route('/load_adstock_settings')
def load_adstock_settings():
    with open(adstock_json, 'r') as json_file:
        data = json.load(json_file)
    return jsonify(data)


@app.route('/save_adstock_settings')
def save_adstock_settings():
    new_data = request.json
    with open(adstock_json, "w") as outfile:
        outfile.write(json.loads(new_data))
    return jsonify({"message": "adstock settings saved successfully"})

if __name__ == '__main__':
     with app.app_context():

        db.create_all()

        app.run(debug=True)


