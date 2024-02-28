
# %% --------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------

from flask import Flask, render_template, send_file, jsonify, request, url_for, redirect, flash
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
from sqlalchemy.exc import SQLAlchemyError
import urllib.parse
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import secrets

app = Flask(__name__)

engine = create_engine('postgresql://postgres:'+urllib.parse.quote_plus("Gde3400@@")+'@192.168.1.2:5432/CPW Blueprint')

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:'+urllib.parse.quote_plus("Gde3400@@")+'@192.168.1.2:5432/CPW Blueprint'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secrets.token_hex()
app.config['SESSION_COOKIE_SECURE'] = True

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

# OPTIMISER FILE PATHS

laydown_filepath = os.path.join(sys.path[0], "optimiser input data/UK_Laydown_v3.csv")
channel_json = os.path.join(sys.path[0], "data/channel.json")
channel_input = pd.read_csv("optimiser input data/UK_Channel_Inputs_v3.csv")
channel_input.drop(columns='Unnamed: 0', inplace=True)

channel_dict = {1:channel_input.to_dict("records")}
ST_laydown = pd.read_csv(laydown_filepath)
ST_laydown = ST_laydown.fillna(0)

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
    
    if 'dates' in data:
        start_date = data['dates'][0]
        end_date = data['dates'][1]
        ST_laydown = ST_laydown[(ST_laydown["Time-Period"] >= start_date) & (ST_laydown["Time-Period"] <= end_date)]
        

    ST_channel_input = table_data[table_id]

    global results
    streams = [entry['Channel'] for entry in ST_channel_input]


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

        def daily_budget_from_pct_laydown(stream):
            
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
        fpath = 'C:/Users/adedoyin.showunmi/PycharmProjects/blueprint/optimiser output data'
        csv_data = pd.read_csv(fpath + '/optimiser results stacked v2.csv')
        chart_data = csv_data.to_dict(orient='records')
        return jsonify(chart_data)

    except Exception as e:
        print('Error reading CSV file:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500

#     try:
#         conn = engine.connect()
#         query = text('SELECT * FROM "Optimised CSV";')
#
#         db_result = conn.execute(query)
#         #print(tp_result.fetchall())
#         chart_data = []
#         col_names = db_result.keys()
#         for x in db_result.fetchall():
#             a = dict(zip(col_names, x))
#             chart_data.append(a)
#
#         return jsonify(chart_data)
#
#     except SQLAlchemyError as e:
#         print('Error executing query:', str(e))
#         return jsonify({'error': 'Internal Server Error'}), 500
#
#     finally:
#         if 'conn' in locals():
#             conn.close()
#
# np.random.seed(42)
@app.route('/chart_response', methods = ['GET'])
def chart_response():
    try:
        fpath = 'C:/Users/adedoyin.showunmi/PycharmProjects/blueprint/optimiser output data'
        csv_data = pd.read_csv(fpath + '/response_curve_data.csv')
        chart_response = csv_data.to_dict(orient='records')
        return jsonify(chart_response)

    except Exception as e:
        print('Error reading CSV file:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/chart_budget', methods = ['GET'])
def chart_budget():
    try:
        fpath = 'C:/Users/adedoyin.showunmi/PycharmProjects/blueprint/optimiser output data'
        csv_data = pd.read_csv(fpath + '/budget_curve_data.csv')
        chart_budget = csv_data.to_dict(orient='records')
        return jsonify(chart_budget)

    except Exception as e:
        print('Error reading CSV file:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500


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
    start_date = list(ST_laydown_dates)[1]
    print(start_date)
    end_date = list(ST_laydown_dates)[-1]
    print(end_date)
    return jsonify({"startDate":start_date, "endDate":end_date})

@app.route('/blueprint')
@login_required
def blueprint():
    print(ST_laydown_dates)
    return render_template('Budget Optimiser.html', current_user = current_user)

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

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=True)  # Use Flask-Login's login_user
            print(f"User {username} logged in successfully.")
            print(current_user.user_info)
            return redirect(url_for('home'))
        else:
            print(f"Failed login attempt for user {username}.")
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('/home'))

if __name__ == '__main__':
     with app.app_context():

        db.create_all()

        app.run(host="0.0.0.0", debug=True)


