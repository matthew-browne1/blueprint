import numpy as np
import pandas as pd
from scipy.optimize import minimize
from numba import jit

class Optimise:
    @jit
    def adstock(PAM, a):
        newdata = PAM
        for i in range(1, len(PAM)):
            newdata[i] += a * newdata[i - 1]
        return newdata


    # Weighted diminishing returns
    @jit
    def dim_returns(alpha, beta, cv):
        return ((1 - np.exp(-alpha * cv)) * beta)

    @jit
    def infsum(rev, a, wks):
        return np.sum(rev[-1] * a ** np.arange(1, wks))

    def rev_per_stream(stream, budget, cost_per_dict, carryover_dict, alpha_dict, beta_dict, recorded_impressions, seas_dict, num_weeks):
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
        total_rev = np.sum(indexed_vals)
        # print(total_rev)

        # infsum = np.sum(carryover_list[-1] * carryover_dict[stream] ** np.arange(1, num_weeks))
        #
        # total_rev += infsum
        return total_rev


    def total_rev_per_stream(stream, budget, ST_cost_per_dict, ST_carryover_dict, ST_alpha_dict, ST_beta_dict,
                            LT_cost_per_dict, LT_carryover_dict, LT_alpha_dict, LT_beta_dict, recorded_impressions,
                            seas_dict, num_weeks, return_type):
        ST_rev = Optimise.rev_per_stream(stream, budget, ST_cost_per_dict, ST_carryover_dict, ST_alpha_dict, ST_beta_dict,
                                recorded_impressions, seas_dict, num_weeks)
        LT_rev = Optimise.rev_per_stream(stream, budget, LT_cost_per_dict, LT_carryover_dict, LT_alpha_dict, LT_beta_dict,
                                recorded_impressions, seas_dict, num_weeks)

        if return_type == 'st':
            return ST_rev
        elif return_type == 'lt':
            return LT_rev
        elif return_type == 'blend':
            return ST_rev + LT_rev
        else:
            return 0


    def profit_objective(budgets, *args):
        streams, ST_cost_per_dict, ST_carryover_dict, ST_alpha_dict, ST_beta_dict,LT_cost_per_dict, LT_carryover_dict, LT_alpha_dict, LT_beta_dict, recorded_impressions, seas_dict, num_weeks, return_type, objective_type = args
        total_rev = sum(
            Optimise.total_rev_per_stream(stream, budgets[i], ST_cost_per_dict, ST_carryover_dict, ST_alpha_dict, ST_beta_dict,
                                LT_cost_per_dict, LT_carryover_dict, LT_alpha_dict, LT_beta_dict,
                                recorded_impressions, seas_dict, num_weeks, return_type) for i, stream in enumerate(streams))
        total_budget = sum(budgets)

        if objective_type == 'profit':
            return -(total_rev - total_budget)
        elif objective_type == 'roi':
            return -(total_rev / total_budget)
        elif objective_type == 'revenue':
            return -total_rev
        else:
            return 0

    def profit_objective_with_penalty(budgets, *args):
        streams, ST_cost_per_dict, ST_carryover_dict, ST_alpha_dict, ST_beta_dict, \
        LT_cost_per_dict, LT_carryover_dict, LT_alpha_dict, LT_beta_dict, recorded_impressions, seas_dict, num_weeks, max_budget, exh_budget, return_type, objective_type = args

        total_rev = sum(
            Optimise.total_rev_per_stream(stream, budgets[i], ST_cost_per_dict, ST_carryover_dict, ST_alpha_dict, ST_beta_dict,
                                LT_cost_per_dict, LT_carryover_dict, LT_alpha_dict, LT_beta_dict,
                                recorded_impressions, seas_dict, num_weeks, return_type) for i, stream in enumerate(streams))
        total_budget = np.sum(budgets)
        penalty = 0.0

        if exh_budget == 'yes':
            # If exhausting budget, penalize for deviation from the max budget
            penalty = np.abs(total_budget - max_budget) * 1e6  # You can adjust the penalty factor
        else:
            # If non-exhausting budget, penalize for exceeding the max budget
            penalty = np.maximum(0, total_budget - max_budget) * 1e6  # You can adjust the penalty factor

        if objective_type == 'Profit':
            return -(total_rev - total_budget - penalty)
        elif objective_type == 'ROI':
            return -((total_rev - penalty) / total_budget)
        elif objective_type == 'Revenue':
            return -(total_rev - penalty)
        else:
            return 0

    def constraint_func(budgets, max_budget, exh_budget):
        if exh_budget == 'yes':
            return sum(budgets) - max_budget
        else:
            return max_budget - sum(budgets)


    def blended_profit_max_scipy(ST_input, LT_input, laydown, seas_index, return_type, objective_type, max_budget, exh_budget, method, num_weeks=1000):

        streams = [entry['Opt Channel'] for entry in ST_input]

        recorded_impressions = {}
        for x in laydown.columns:
            recorded_impressions[x] = laydown[x].to_list()

        seas_dict = {}
        for x in seas_index.columns:
            seas_dict[x] = seas_index[x].to_list()

        max_spend_cap_list = [float(entry['Max Spend Cap']) for entry in ST_input]
        max_spend_cap_dict = dict(zip(streams, max_spend_cap_list))

        min_spend_cap_list = [float(entry['Min Spend Cap']) for entry in ST_input]
        min_spend_cap_dict = dict(zip(streams, min_spend_cap_list))

        ST_cost_per_list = [float(entry['CPU']) if 'CPU' in entry else 0.0 for entry in ST_input]
        ST_cost_per_dict = dict(zip(streams, ST_cost_per_list))
        LT_cost_per_list = [float(entry['CPU']) if 'CPU' in entry else 0.0 for entry in LT_input]
        LT_cost_per_dict = dict(zip(streams, LT_cost_per_list))

        ST_carryover_list = [float(entry['ST Carryover']) if 'ST Carryover' in entry else 0.0 for entry in ST_input]
        ST_carryover_dict = dict(zip(streams, ST_carryover_list))
        LT_carryover_list = [float(entry['LT Carryover']) if 'LT Carryover' in entry else 0.0 for entry in LT_input]
        LT_carryover_dict = dict(zip(streams, LT_carryover_list))

        ST_alpha_list = [float(entry['ST Alpha']) if 'ST Alpha' in entry else 0.0 for entry in ST_input]
        ST_alpha_dict = dict(zip(streams, ST_alpha_list))
        LT_alpha_list = [float(entry['LT Alpha']) if 'LT Alpha' in entry else 0.0 for entry in LT_input]
        LT_alpha_dict = dict(zip(streams, LT_alpha_list))

        ST_beta_list = [float(entry['ST Beta']) if 'ST Beta' in entry and not pd.isna(entry['ST Beta']) and entry['ST Beta'] != np.inf else 0.0 for entry in ST_input]
        ST_beta_dict = dict(zip(streams, ST_beta_list))

        LT_beta_list = [float(entry['LT Beta']) if 'LT Beta' in entry and not pd.isna(entry['LT Beta']) and entry['LT Beta'] != np.inf else 0.0 for entry in LT_input]
        LT_beta_dict = dict(zip(streams, LT_beta_list))


        args = (streams, ST_cost_per_dict, ST_carryover_dict, ST_alpha_dict, ST_beta_dict,
                LT_cost_per_dict, LT_carryover_dict, LT_alpha_dict, LT_beta_dict,
                recorded_impressions, seas_dict, num_weeks, return_type, objective_type)

        initial_budgets = [min(max_spend_cap_dict[stream], max_budget / len(streams)) for stream in streams]

        bounds = [(min_spend_cap_dict[stream], max_spend_cap_dict[stream]) for stream in streams]

        constraints = []
        if exh_budget == 'yes':
            constraints.append({'type': 'eq', 'fun': lambda budgets: max_budget - sum(budgets)})
        else:
            constraints.append({'type': 'ineq', 'fun': lambda budgets:  sum(budgets) - max_budget})
        print(constraints)

        # def optimization_callback(xk):
        #     # Add any relevant information you want to print or check at each iteration
        #     print("Current solution:", xk)

        result = minimize(Optimise.profit_objective, initial_budgets, args=args, bounds=bounds, constraints=constraints, method=method, options={'disp': True, 'maxiter': 10000})

        # result = minimize(profit_objective_with_penalty, initial_budgets, args=args, bounds=bounds, method='Powell')#, method=method)

        # result = differential_evolution(profit_objective_with_penalty, bounds, args=args, disp=True)

        opt_budgets_dict = dict(zip(streams, result.x))

        if result.success:
            print("Optimal Solution Found:")
            for stream in streams:
                print(f"{stream} Budget: {opt_budgets_dict[stream]}")
            print(f"Maximized Profit: {-result.fun}")
        else:
            print("Solver did not find an optimal solution.")
            print(f"Solution failed using budget input of: {max_budget} with max total spend cap of: {sum(max_spend_cap_list)}")

        return opt_budgets_dict


# %% --------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------

