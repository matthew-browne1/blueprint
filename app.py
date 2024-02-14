
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
# from pyomo_opt import Optimiser
from sqlalchemy import create_engine, text, Column, DateTime, Integer, func
from sqlalchemy.orm import Session, declarative_base
import datetime
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
import io
import pyutilib.subprocess.GlobalData

pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False

class Optimiser:

    # channel_input = dictionary 
    # laydown = dataframe
    # obj_func = string
    # exh_budget = string yes or no
    # max_budget = integer

    def profit_max(channel_input, laydown, seas_index, max_budget, exh_budget="yes", num_weeks=1000):
        print(laydown.columns)
        #laydown.drop(columns="Time_Period", inplace=True)
        model = ConcreteModel()
        
        streams = [entry['Channel'] for entry in channel_input]

        spend_cap_list = [float(entry['Max_Spend_Cap']) for entry in channel_input]
        spend_cap_dict = dict(zip(streams, spend_cap_list))
      
        cost_per_list = [float(entry['CPU']) for entry in channel_input]
        cost_per_dict = dict(zip(streams, cost_per_list))
  
        carryover_list = [float(entry['Carryover']) for entry in channel_input]
        carryover_dict = dict(zip(streams, carryover_list))
       
        beta_list = [float(entry['Beta']) for entry in channel_input]
        beta_dict = dict(zip(streams, beta_list))
 
        alpha_list = [float(entry['Alpha']) for entry in channel_input]
        alpha_dict = dict(zip(streams, alpha_list))
        
        recorded_impressions = {}
        for x in laydown.columns:
            recorded_impressions[x] = laydown[x].to_list()

        seas_dict = {}
        for x in seas_index.columns:
            seas_dict[x] = seas_index[x].to_list()
    
        model.stream_budget = Var(streams, within=NonNegativeReals)

        model.budget_constraints = ConstraintList()
        for stream in streams:
            model.budget_constraints.add(expr=model.stream_budget[stream] <= spend_cap_dict[stream])

        model.non_zero_spend_constraints = ConstraintList()
        for stream in streams:
            model.non_zero_spend_constraints.add(model.stream_budget[stream] >= 1.0)

        def rev_per_stream(stream, budget):
            
            cost_per_stream = cost_per_dict.get(stream, 1e-6)  # Set a small non-zero default cost
            print("cpu:")
            print(cost_per_stream)
            allocation = budget / cost_per_stream
            print('allocation:')
            print(allocation)
            pct_laydown = []
            for x in range(len(recorded_impressions[stream])):
                try:
                    pct_laydown.append(recorded_impressions[stream][x]/sum(recorded_impressions[stream]))
                except:
                    pct_laydown.append(0)
            print("pct_laydown:")
            print(pct_laydown)
            pam = [pct_laydown[i]*allocation for i in range(len(pct_laydown))]
            carryover_list = []
            carryover_list.append(pam[0])
            for x in range(1,len(pam)):
                carryover_val = pam[x] + carryover_list[x-1]*carryover_dict[stream]
                carryover_list.append(carryover_val)
            print("carryover list:")
            print(carryover_list)
            rev_list = []
            for x in carryover_list:
                rev_val = beta_dict[stream] * ((1 - exp(-alpha_dict[stream]*x))) 
                rev_list.append(rev_val)
            print("rev list")
            print(rev_list)
            indexed_vals = [a * b for a, b in zip(rev_list, seas_dict[stream])]
            total_rev = sum(indexed_vals)
            infsum = 0
            for n in range(1, num_weeks):
                infsum += carryover_list[-1] * (1-carryover_dict[stream])**n
            total_rev = total_rev + infsum
            return total_rev

        def profit_expr(model):
            total_rev = sum(model.revenue_expr[stream] for stream in streams)
            total_budget = sum(model.stream_budget[stream] for stream in streams)
            return total_rev - total_budget

        model.revenue_expr = Expression(streams, rule=lambda model, stream: rev_per_stream(stream, model.stream_budget[stream]))
        model.profit_expr = Expression(rule=profit_expr)
        model.prof_max = Objective(expr=model.profit_expr, sense=maximize)

        def use_entire_budget_rule(model):
            return sum(model.stream_budget[stream] for stream in streams) == max_budget
        
        def budget_cap(model):
            return sum(model.stream_budget[stream] for stream in streams) <= max_budget
        model.budget_cap_constraint = Constraint(rule=budget_cap)
        if exh_budget == "yes":
            model.use_entire_budget_constraint = Constraint(rule=use_entire_budget_rule)

        def min_roi_constraint_rule(model, stream):
            return model.revenue_expr[stream] / model.stream_budget[stream] >= 0.00001
        model.min_roi_constraints = Constraint(streams, rule=min_roi_constraint_rule)

        solver = SolverFactory('ipopt', executable = r"C:\Ipopt\bin\ipopt.exe")

        results = solver.solve(model)

        if results.solver.termination_condition == TerminationCondition.optimal:
            opt_budgets = [model.stream_budget[stream].value for stream in streams]
            opt_budgets_dict = dict(zip(streams, opt_budgets))
            print("Optimal Solution Found:")
            for stream in streams:
                print(f"{stream} Budget: {model.stream_budget[stream].value}")
            print(f"Maximised Profit: {model.prof_max()}")
        else:
            print("Solver did not find an optimal solution.")
            print(f"solution failed using budget input of: {max_budget} with max total spend cap of: {sum(spend_cap_list)}")

        return opt_budgets_dict

    def revenue_max(channel_input, laydown, exh_budget, max_budget, num_weeks=1000):
        laydown.drop(columns="Time_Period", inplace=True)
        model = ConcreteModel()

        streams = [entry['Channel'] for entry in channel_input]

        spend_cap_list = [float(entry['Max_Spend_Cap']) for entry in channel_input]
        spend_cap_dict = dict(zip(streams, spend_cap_list))
  
        cost_per_list = [float(entry['CPU']) for entry in channel_input]
        cost_per_dict = dict(zip(streams, cost_per_list))
       
        carryover_list = [float(entry['Carryover']) for entry in channel_input]
        carryover_dict = dict(zip(streams, carryover_list))
     
        beta_list = [float(entry['Beta']) for entry in channel_input]
        beta_dict = dict(zip(streams, beta_list))
    
        alpha_list = [float(entry['Alpha']) for entry in channel_input]
        alpha_dict = dict(zip(streams, alpha_list))
       
        recorded_impressions = {}
        for x in laydown.columns:
            recorded_impressions[x] = laydown[x].to_list()
       
        model.stream_budget = Var(streams, within=NonNegativeReals)

        model.budget_constraints = ConstraintList()
        for stream in streams:
            model.budget_constraints.add(expr=model.stream_budget[stream] <= spend_cap_dict[stream])

        model.non_zero_spend_constraints = ConstraintList()
        for stream in streams:
            model.non_zero_spend_constraints.add(model.stream_budget[stream] >= 1.0)

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
                rev_val = beta_dict[stream] * ((1 - exp(-alpha_dict[stream]*x)))
                rev_list.append(rev_val)
            total_rev = sum(rev_list)
            infsum = 0
            for n in range(1, num_weeks):
                infsum += carryover_list[-1] * (1-carryover_dict[stream])**n
            total_rev = total_rev + infsum
            return total_rev

        model.revenue_expr = Expression(streams, rule=lambda model, stream: rev_per_stream(stream, model.stream_budget[stream]))

        model.rev_max = Objective(expr=sum(model.revenue_expr[stream] for stream in streams), sense=maximize)  

        def use_entire_budget_rule(model):
            return sum(model.stream_budget[stream] for stream in streams) == max_budget
        def budget_cap(model):
            return sum(model.stream_budget[stream] for stream in streams) <= max_budget
        model.budget_cap_constraint = Constraint(rule=budget_cap)
        
        if exh_budget == "yes":
            model.use_entire_budget_constraint = Constraint(rule=use_entire_budget_rule)

        def min_roi_constraint_rule(model, stream):
            return model.revenue_expr[stream] / model.stream_budget[stream] >= 0.00001
        model.min_roi_constraints = Constraint(streams, rule=min_roi_constraint_rule)

        solver = SolverFactory('ipopt', executable = r"C:\Ipopt\bin\ipopt.exe")

        results = solver.solve(model)

        if results.solver.termination_condition == TerminationCondition.optimal:
            opt_budgets = [model.stream_budget[stream].value for stream in streams]
            opt_budgets_dict = dict(zip(streams, opt_budgets))
            print("Optimal Solution Found:")
            for stream in streams:
                print(f"{stream} Budget: {model.stream_budget[stream].value}")
            print(f"Maximised Revenue: {model.rev_max()}")
        else:
            print("Solver did not find an optimal solution.")

        return opt_budgets_dict

    def roi_max(channel_input, laydown, exh_budget, max_budget, num_weeks=1000):
        laydown.drop(columns="Time_Period", inplace=True)
        model = ConcreteModel()

        streams = [entry['Channel'] for entry in channel_input]

        spend_cap_list = [float(entry['Max_Spend_Cap']) for entry in channel_input]
        spend_cap_dict = dict(zip(streams, spend_cap_list))
      
        cost_per_list = [float(entry['CPU']) for entry in channel_input]
        cost_per_dict = dict(zip(streams, cost_per_list))
        
        carryover_list = [float(entry['Carryover']) for entry in channel_input]
        carryover_dict = dict(zip(streams, carryover_list))
      
        beta_list = [float(entry['Beta']) for entry in channel_input]
        beta_dict = dict(zip(streams, beta_list))
 
        alpha_list = [float(entry['Alpha']) for entry in channel_input]
        alpha_dict = dict(zip(streams, alpha_list))
      
        recorded_impressions = {}
        for x in laydown.columns:
            recorded_impressions[x] = laydown[x].to_list()
    
        model.stream_budget = Var(streams, within=NonNegativeReals)

        model.budget_constraints = ConstraintList()
        for stream in streams:
            model.budget_constraints.add(expr=model.stream_budget[stream] <= spend_cap_dict[stream])

        model.non_zero_spend_constraints = ConstraintList()
        for stream in streams:
            model.non_zero_spend_constraints.add(model.stream_budget[stream] >= 1.0)

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
                rev_val = beta_dict[stream] * ((1 - exp(-alpha_dict[stream]*x)))
                rev_list.append(rev_val)
            total_rev = sum(rev_list)
            infsum = 0
            for n in range(1, num_weeks):
                infsum += carryover_list[-1] * (1-carryover_dict[stream])**n
            total_rev = total_rev + infsum
            return total_rev

        def roi_expr(model):
            rev_list = np.array([model.revenue_expr[stream] for stream in streams])
            budget_list = np.array([model.stream_budget[stream] for stream in streams])
            return sum(rev_list/budget_list)

        model.revenue_expr = Expression(streams, rule=lambda model, stream: rev_per_stream(stream, model.stream_budget[stream]))

        model.roi_expr = Expression(rule=roi_expr)

        model.roi_max = Objective(expr=model.roi_expr, sense=maximize)

        def use_entire_budget_rule(model):
            return sum(model.stream_budget[stream] for stream in streams) == max_budget
        def budget_cap(model):
            return sum(model.stream_budget[stream] for stream in streams) <= max_budget
        model.budget_cap_constraint = Constraint(rule=budget_cap)
        
        if exh_budget == "yes":
            model.use_entire_budget_constraint = Constraint(rule=use_entire_budget_rule)

        def min_roi_constraint_rule(model, stream):
            return model.revenue_expr[stream] / model.stream_budget[stream] >= 0.00001
        model.min_roi_constraints = Constraint(streams, rule=min_roi_constraint_rule)

        solver = SolverFactory('ipopt', executable = r"C:\Ipopt\bin\ipopt.exe")

        results = solver.solve(model)

        if results.solver.termination_condition == TerminationCondition.optimal:
            opt_budgets = [model.stream_budget[stream].value for stream in streams]
            opt_budgets_dict = dict(zip(streams, opt_budgets))
            print("Optimal Solution Found:")
            for stream in streams:
                print(f"{stream} Budget: {model.stream_budget[stream].value}")
            print(f"Maximised ROI: {model.roi_max()}")
        else:
            print("Solver did not find an optimal solution.")

        return opt_budgets_dict
    

    def beta_opt(channel_input, laydown, num_weeks=1000):
        laydown.drop(columns="Time_Period", inplace=True)
        model = ConcreteModel()
        print("initialising beta opt")
        streams = [entry['Channel'] for entry in channel_input]

        recorded_impressions = {}
        for x in laydown.columns:
            recorded_impressions[x] = [float(i) for i in laydown[x].to_list()]
        
        cost_per_list = [float(entry['CPU']) for entry in channel_input]
        cost_per_dict = dict(zip(streams, cost_per_list))
        
        carryover_list = [float(entry['Carryover']) for entry in channel_input]
        carryover_dict = dict(zip(streams, carryover_list))

        alpha_list = [float(entry['Alpha']) for entry in channel_input]
        alpha_dict = dict(zip(streams, alpha_list))

        current_budget_list = [entry['Current_Budget'] for entry in channel_input]
        current_budget_dict = dict(zip(streams, current_budget_list))

        current_roi_list = [entry['Current_ROI'] for entry in channel_input]
        current_roi_dict = dict(zip(streams, current_roi_list))

        model.beta = Var(streams, within=NonNegativeReals)

        def rev_per_stream(stream, beta):
            print(f"calculating revenue per stream for {stream}")
            cost_per_stream = cost_per_dict.get(stream, 1e-6)  # Set a small non-zero default cost
            print(f"cpu: {cost_per_stream}")
            allocation = current_budget_dict[stream] / cost_per_stream
            print(f"allocation: {allocation}")
            pct_laydown = []
            for x in range(len(recorded_impressions[stream])):
                try:
                    pct_laydown.append(recorded_impressions[stream][x]/sum(recorded_impressions[stream]))
                except:
                    pct_laydown.append(0)
            print(f"pct_laydown: {pct_laydown}")
            pam = [pct_laydown[i]*allocation for i in range(len(pct_laydown))]
            print(f"pam: {pam}")
            carryover_list_str = []
            carryover_list_str.append(pam[0])
            for x in range(1,len(pam)):
                carryover_val = pam[x] + carryover_list_str[x-1]*carryover_dict[stream]
                carryover_list_str.append(carryover_val)
            print(f"carryover_list: {carryover_list_str}")
            rev_list = []
            for x in carryover_list_str:
                rev_val = beta * ((1 - exp(-alpha_dict[stream]*x)))
                rev_list.append(rev_val)
            print(f"rev_list: {rev_list}")
            total_rev = sum(rev_list)
            print(f"total revenue: {total_rev}")
            infsum = 0
            for n in range(1, num_weeks):
                infsum += carryover_list_str[-1] * (carryover_dict[stream])**n
            print(f"sum to infinity integer: {infsum} for stream: {stream}")
            total_rev = total_rev + infsum
            return total_rev

        def calculated_roi_per_stream(stream, beta):

            roi = rev_per_stream(stream, beta) / current_budget_dict[stream]
            return roi
        
        # manually calcualte betas
        # set betas to 1 and then find the revs

        print(f"ROIs with beta = 1: {dict(zip(streams,[calculated_roi_per_stream(stream,1) for stream in streams]))}")
        manual_betas = [a / b for a, b in zip(current_roi_list, [calculated_roi_per_stream(stream,1) for stream in streams])]
        
        return dict(zip(streams, manual_betas))
    
    def blended_profit_max(ST_input, LT_input, laydown, seas_index, max_budget, exh_budget="yes", num_weeks=1000):

        model = ConcreteModel()
        
        streams = [entry['Channel'] for entry in ST_input]

        spend_cap_list = [float(entry['Max_Spend_Cap']) for entry in ST_input]
        spend_cap_dict = dict(zip(streams, spend_cap_list))
      
        ST_cost_per_list = [float(entry['CPU']) for entry in ST_input]
        ST_cost_per_dict = dict(zip(streams, ST_cost_per_list))
        LT_cost_per_list = [float(entry['CPU']) for entry in LT_input]
        LT_cost_per_dict = dict(zip(streams, LT_cost_per_list))
  
        ST_carryover_list = [float(entry['Carryover']) for entry in ST_input]
        ST_carryover_dict = dict(zip(streams, ST_carryover_list))
        LT_carryover_list = [float(entry['Carryover']) for entry in LT_input]
        LT_carryover_dict = dict(zip(streams, LT_carryover_list))
       
        ST_beta_list = [float(entry['Beta']) for entry in ST_input]
        ST_beta_dict = dict(zip(streams, ST_beta_list))
        LT_beta_list = [float(entry['Beta']) for entry in LT_input]
        LT_beta_dict = dict(zip(streams, LT_beta_list))
 
        ST_alpha_list = [float(entry['Alpha']) for entry in ST_input]
        ST_alpha_dict = dict(zip(streams, ST_alpha_list))
        LT_alpha_list = [float(entry['Alpha']) for entry in LT_input]
        LT_alpha_dict = dict(zip(streams, LT_alpha_list))
        
        app.logger.info(f"from within pyomo_opt method: spend cap dict: {spend_cap_dict}, ST cpu: {ST_cost_per_dict}, LT cpu: {LT_cost_per_dict}, ST carryover dict: {ST_carryover_dict}, LT carryover dict: {LT_carryover_dict}, ST beta dict: {ST_beta_dict}, LT beta dict: {LT_beta_dict}, ST alpha dict: {ST_alpha_dict}, LT alpha dict: {LT_alpha_dict}")

        recorded_impressions = {}
        for x in laydown.columns:
            recorded_impressions[x] = laydown[x].to_list()

        seas_dict = {}
        for x in seas_index.columns:
            seas_dict[x] = seas_index[x].to_list()
    
        model.stream_budget = Var(streams, within=NonNegativeReals)

        model.budget_constraints = ConstraintList()
        for stream in streams:
            model.budget_constraints.add(expr=model.stream_budget[stream] <= spend_cap_dict[stream])

        model.non_zero_spend_constraints = ConstraintList()
        for stream in streams:
            model.non_zero_spend_constraints.add(model.stream_budget[stream] >= 1.0)

        def rev_per_stream(stream, budget, cost_per_dict, carryover_dict, alpha_dict, beta_dict):
            
            cost_per_stream = cost_per_dict.get(stream, 1e-6)  # Set a small non-zero default cost
            app.logger.info(f"cpu for {stream}: {cost_per_stream}")
            allocation = budget / cost_per_stream
            app.logger.info(f'allocation: {allocation}')
            pct_laydown = []
            for x in range(len(recorded_impressions[stream])):
                try:
                    pct_laydown.append(recorded_impressions[stream][x]/sum(recorded_impressions[stream]))
                except:
                    pct_laydown.append(0)
            app.logger.info(f"pct_laydown: {pct_laydown}")
            pam = [pct_laydown[i]*allocation for i in range(len(pct_laydown))]
            carryover_list = []
            carryover_list.append(pam[0])
            for x in range(1,len(pam)):
                carryover_val = pam[x] + carryover_list[x-1]*carryover_dict[stream]
                carryover_list.append(carryover_val)
            app.logger.info(f"carryover list: {carryover_list}")
            rev_list = []
            for x in carryover_list:
                rev_val = beta_dict[stream] * ((1 - exp(-alpha_dict[stream]*x))) 
                rev_list.append(rev_val)
            app.logger.info(f"rev list: {rev_list}")
            indexed_vals = [a * b for a, b in zip(rev_list, seas_dict[stream])]
            total_rev = sum(indexed_vals)
            infsum = 0
            for n in range(1, num_weeks):
                infsum += carryover_list[-1] * (1-carryover_dict[stream])**n
            total_rev = total_rev + infsum
            return total_rev

        def profit_expr(model):
            total_rev = sum(model.revenue_expr[stream] for stream in streams)
            total_budget = sum(model.stream_budget[stream] for stream in streams)
            return total_rev - total_budget

        def total_rev_per_stream(stream, budget):
            ST_rev = rev_per_stream(stream, budget, ST_cost_per_dict, ST_carryover_dict, ST_alpha_dict, ST_beta_dict)
            LT_rev = rev_per_stream(stream, budget, LT_cost_per_dict, LT_carryover_dict, LT_alpha_dict, LT_beta_dict)
            total_rev = ST_rev + LT_rev
            return total_rev

        model.revenue_expr = Expression(streams, rule=lambda model, stream: total_rev_per_stream(stream, model.stream_budget[stream]))

        model.profit_expr = Expression(rule=profit_expr)
        model.prof_max = Objective(expr=model.profit_expr, sense=maximize)

        def use_entire_budget_rule(model):
            return sum(model.stream_budget[stream] for stream in streams) == max_budget
        
        def budget_cap(model):
            return sum(model.stream_budget[stream] for stream in streams) <= max_budget
        model.budget_cap_constraint = Constraint(rule=budget_cap)
        if exh_budget == "yes":
            model.use_entire_budget_constraint = Constraint(rule=use_entire_budget_rule)

        def min_roi_constraint_rule(model, stream):
            return model.revenue_expr[stream] / model.stream_budget[stream] >= 0.00001
        model.min_roi_constraints = Constraint(streams, rule=min_roi_constraint_rule)
      
        ipopt_executable = os.path.join('/site/wwwroot/Ipopt/bin/ipopt')

        solver = SolverFactory('ipopt', executable = ipopt_executable)
        results = solver.solve(model, tee=True)

        if results.solver.termination_condition == TerminationCondition.optimal:
            opt_budgets = [model.stream_budget[stream].value for stream in streams]
            opt_budgets_dict = dict(zip(streams, opt_budgets))
            app.logger.info("Optimal Solution Found:")
            for stream in streams:
                app.logger.info(f"{stream} Budget: {model.stream_budget[stream].value}")
            app.logger.info(f"Maximised Profit: {model.prof_max()}")
        else:
            print("Solver did not find an optimal solution.")
            print(f"solution failed using budget input of: {max_budget} with max total spend cap of: {sum(spend_cap_list)}")

        return opt_budgets_dict

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
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['DEBUG'] = True

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

class DatabaseHandler(logging.Handler):
    def emit(self, record):
        try:
            message = self.format(record)
            db.session.add(Log(message=message))
            db.session.commit()
        except Exception:
            self.handleError(record)

database_handler = DatabaseHandler()
database_handler.setLevel(logging.DEBUG)
app.logger.addHandler(database_handler)

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

    app.logger.info(f"snapshot id = {snapshot_id}")
    app.logger.info(f"user id = {user_id}")

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

laydown_query = 'select * FROM "laydown"'
laydown_fetched = pd.read_sql(laydown_query, con=engine)
ST_query = f'SELECT * FROM "ST_header"'
ST_input_fetched = pd.read_sql(ST_query, con=engine)
LT_query = f'SELECT * FROM "LT_header"'
LT_input_fetched = pd.read_sql(LT_query, con=engine)
si_query = f'SELECT * FROM "seas_index"'
seas_index_fetched = pd.read_sql(si_query, con=engine)

bud = sum(ST_input_fetched['Current_Budget'].to_list())
streams = []
for stream in ST_input_fetched['Channel']:
    streams.append(str(stream))

laydown = laydown_fetched
ST_header_dict = ST_input_fetched.to_dict("records")
LT_header_dict = LT_input_fetched.to_dict("records")
seas_index = seas_index_fetched.to_dict("records")

laydown_dates = laydown['Time_Period']

### TABLE DATA ###

table_df = ST_input_fetched.copy()

dataTable_cols = ['Channel', 'Carryover', 'Alpha', 'Beta', 'Current_Budget', 'Min_Spend_Cap', 'Max_Spend_Cap', 'Laydown']

for col in table_df.columns:
    if col not in dataTable_cols:
        table_df.drop(columns=col, inplace=True)

table_dict = table_df.to_dict("records")

table_data = {"1":table_dict}
for var in table_data["1"]:
    var['Laydown'] = laydown[var['Channel']].tolist()

# %% --------------------------------------------------------------------------
# 
# -----------------------------------------------------------------------------

@app.route('/optimise', methods = ['POST'])
def optimise():

    if request.method == "POST":
        data = request.json
    app.logger.info("REACHING OPT METHOD")
    table_id = str(data['tableID'])
    obj_func = data['objectiveValue']
    exh_budget = data['exhaustValue']
    max_budget = int(data['maxValue'])
    num_weeks = 1000
    blend = data['blendValue']
    
    # if 'dates' in data:
    #     app.logger.info('dates found in data')
    #     start_date = data['dates'][0]
    #     end_date = data['dates'][1]
    #     laydown = laydown[(laydown["Time-Period"] >= start_date) & (laydown["Time-Period"] <= end_date)]
    #     app.logger.info(start_date)
    #     app.logger.info(end_date)

    app.logger.info(f"retrieved from the server: table id = {table_id}, objective function = {obj_func}, exhaust budget = {exh_budget}, max budget = {max_budget}, blended = {blend}")
    
    # NEED TO ADD HANDLING SO THAT EDITS MADE TO TABLE DATA ARE ADDED TO THE ST_HEADER

    app.logger.info(f"laydown = {laydown}")
    app.logger.info(f"CPU = {[entry['CPU'] for entry in ST_header_dict]}")

    global results

    streams = [entry['Channel'] for entry in ST_header_dict]

    if blend.lower() == "blend":
        if obj_func.lower() == "profit":
            results[table_id] = Optimiser.blended_profit_max(ST_input = ST_header_dict, LT_input=LT_header_dict, laydown=laydown, seas_index=seas_index_fetched, exh_budget='yes', max_budget=max_budget, num_weeks=num_weeks)
            app.logger.info(results[table_id])
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
        app.logger.info(results)

        return jsonify(results), 200

@app.route('/results_output', methods = ['POST'])
def results_output():

    tab_names = dict(request.json)

    raw_input_data = ST_input_fetched.to_dict("records")
    
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
        app.logger.info(f"results from optimiser:{results}")
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

    app.logger.info(concat_df.info())
    try:
        concat_df.to_sql('Optimised CSV', engine, if_exists='replace', index=False)
        app.logger.info("csv uploaded to db successfully")
    except:
        app.logger.info("csv db upload failed")

    return jsonify({"message":"csv exported successfully"})

@app.route('/chart_data', methods = ['GET'])
def chart_data():
    try:
        conn = engine.connect()
        query = text('SELECT * FROM "Optimised CSV";')

        db_result = conn.execute(query)
        #app.logger.info(tp_result.fetchall())
        chart_data = []
        col_names = db_result.keys()
        for x in db_result.fetchall():
            a = dict(zip(col_names, x))
            chart_data.append(a)
       
        return jsonify(chart_data)
    
    except SQLAlchemyError as e:
        app.logger.info('Error executing query:', str(e))
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
    app.logger.info(f"lobf={lobf}")
    lobf_dict = dict(zip(poly_x, lobf))
    data = {
        "x": poly_x.tolist(),
        "y": poly_y.tolist(),
        "lobf": dict(sorted(lobf_dict.items()))
    }
    app.logger.info(data)
    return jsonify(data)

@app.route('/blueapp.logger.info_results')
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
    channel_dict = ST_input_fetched.to_dict("records")
    for var in channel_dict:
        var['Laydown'] = laydown[var['Channel']].tolist()
    if tableID not in table_data.keys():
        table_data[tableID] = table_dict
    app.logger.info(table_data.keys())
    return jsonify({"success": True, "table_id": tableID})

@app.route('/channel', methods = ['GET', 'PUT'])
def channel():
    app.logger.info("reaching /channel")
    if request.method == 'GET':
        app.logger.info("getting")
        return jsonify(table_data)

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

if __name__ == '__main__':
     with app.app_context():

        db.create_all()
        # for user in user_data:
        #     add_user(user)
        app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000), debug=True)
