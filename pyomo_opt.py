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

    def profit_max(channel_input, laydown, max_budget, exh_budget="yes", num_weeks=1000):
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

        laydown = laydown.drop(columns="Time_Period")
        
        model = ConcreteModel()

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
            
            cost_per_stream = cost_per_dict.get(stream, 1e-6)  # Set a small non-zero default cost
          
            allocation = current_budget_dict[stream] / cost_per_stream
  
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
                rev_val = beta * ((1 - exp(-alpha_dict[stream]*x)))
                rev_list.append(rev_val)

            total_rev = sum(rev_list)
            infsum = 0
            for n in range(1, num_weeks):
                infsum += carryover_list[-1] * (1-carryover_dict[stream])**n
            total_rev = total_rev + infsum
            return total_rev

        def calculated_roi_per_stream(stream):

            roi = rev_per_stream(stream, model.beta[stream]) / current_budget_dict[stream]
            return roi

        model.roi_constraint = ConstraintList()
        for stream in streams:
            def roi_expr(model):
                return rev_per_stream(stream, model.beta[stream]) / current_budget_dict[stream]
            model.roi_constraint.add(expr=roi_expr(model) == current_roi_dict[stream])

        model.obj = Objective(expr=sum((calculated_roi_per_stream(stream) - current_roi_dict[stream]) ** 2 for stream in streams), sense=minimize)
        
        solver = SolverFactory('ipopt', executable = r"C:\Ipopt\bin\ipopt.exe")

        results = solver.solve(model, tee=True)  # Use tee=True to see the solver's output

        if results.solver.termination_condition == TerminationCondition.optimal:
            # Get the optimal beta values
            optimal_beta_values = {stream: value(model.beta[stream]) for stream in streams}
            return optimal_beta_values
        else:
            raise ValueError("Solver could not find a feasible solution")


# %% --------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------

laydown = pd.read_csv('Y:/2023/Nestle CPW/UK/6. Blueprint Work (RF)/UK_Laydown_v4.csv')
channel_input = pd.read_csv('Y:/2023/Nestle CPW/UK/6. Blueprint Work (RF)/UK_Channel_Inputs_v4.csv')
incr_rev = pd.read_csv('Y:/2023/Nestle CPW/UK/6. Blueprint Work (RF)/UK_Incremental_Revenue_v4.csv')
channel_dict = {"data":channel_input.to_dict("records")}
laydown.drop(columns="Time_Period", inplace=True)
# %%
