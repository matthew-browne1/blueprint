# %% --------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------

import numpy as np
import pandas as pd
from pyomo.environ import *
from pyomo.opt import SolverFactory
import statsmodels as sm
import optuna 
import math

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


