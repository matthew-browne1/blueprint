import numpy as np
import pandas as pd
from scipy.optimize import minimize
from numba import jit
import time

class Optimise:
    @jit
    def adstock(PAM, a):
        #print(PAM)
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

    def rev_per_stream(stream, budget, cost_per_dict, carryover_dict, alpha_dict, beta_dict, recorded_impressions, date_list, seas_dict, nns_mc, vol, num_weeks):
        cost_per_stream = cost_per_dict.get(stream, 1e-6)  # Set a small non-zero default cost
        allocation = budget / cost_per_stream

        pct_laydown = np.array(recorded_impressions[stream]) / sum(recorded_impressions[stream]) if sum(recorded_impressions[stream]) != 0 else np.zeros(len(recorded_impressions[stream]))
        # print(sum(pct_laydown))

        pam = pct_laydown * allocation
        
        carryover_list = Optimise.adstock(pam, carryover_dict[stream])

        rev_list = Optimise.dim_returns(alpha_dict[stream], beta_dict[stream], carryover_list)

        indexed_vals = rev_list * seas_dict[stream]

        # print(f"length of indexed_vals list is: {len(indexed_vals)}")
        # print(f"length of date list is: {len(date_list)}")
        
        if vol:
            # Convert date_list and indexed_vals to a DataFrame
            indexed_revs_with_date_df = pd.DataFrame({
                'Date': date_list,
                'Indexed_Revenue': indexed_vals
            })
            
            # Add a 'Year' column to the DataFrame
            indexed_revs_with_date_df['Year'] = pd.to_datetime(indexed_revs_with_date_df['Date']).dt.year
            
            try:
                stream_name, country, brand = stream.split("_")
            except Exception as e:
                print(e)
            
            filtered_nns_mc = nns_mc[
                (nns_mc['Country'] == country) & 
                (nns_mc['Brand'] == brand)
            ]

            # Merge the DataFrames on 'Year'
            merged_df = pd.merge(indexed_revs_with_date_df, filtered_nns_mc, on='Year')

            # Calculate the volume using vectorized operations
            merged_df['Volume'] = merged_df['Indexed_Revenue'] / (merged_df['NNS'] * merged_df['MC'])

            # Sum the volumes to get the total revenue
            total_rev = merged_df['Volume'].sum()

            return total_rev

        else:

            total_rev = np.sum(indexed_vals)

            return total_rev


    def total_rev_per_stream(stream, budget, ST_cost_per_dict, ST_carryover_dict, ST_alpha_dict, ST_beta_dict,
                            LT_cost_per_dict, LT_carryover_dict, LT_alpha_dict, LT_beta_dict, recorded_impressions, date_list,
                            seas_dict, nns_mc, vol, num_weeks, return_type):
        ST_rev = Optimise.rev_per_stream(stream, budget, ST_cost_per_dict, ST_carryover_dict, ST_alpha_dict, ST_beta_dict,
                                recorded_impressions, date_list, seas_dict, nns_mc, vol, num_weeks)
        LT_rev = Optimise.rev_per_stream(stream, budget, LT_cost_per_dict, LT_carryover_dict, LT_alpha_dict, LT_beta_dict,
                                recorded_impressions, date_list, seas_dict, nns_mc, vol, num_weeks)

        if return_type == 'st':
            return ST_rev
        elif return_type == 'lt':
            return LT_rev
        elif return_type == 'blend':
            return ST_rev + LT_rev
        else:
            return 0


    def profit_objective(budgets, *args):
        streams, ST_cost_per_dict, ST_carryover_dict, ST_alpha_dict, ST_beta_dict,LT_cost_per_dict, LT_carryover_dict, LT_alpha_dict, LT_beta_dict, recorded_impressions, date_list, seas_dict, nns_mc, num_weeks, max_budget, exh_budget, return_type, objective_type = args

        if objective_type == 'volume':
            vol = True
        else:
            vol = False

        total_rev = sum(
            Optimise.total_rev_per_stream(stream, budgets[i], ST_cost_per_dict, ST_carryover_dict, ST_alpha_dict, ST_beta_dict,
                                LT_cost_per_dict, LT_carryover_dict, LT_alpha_dict, LT_beta_dict,
                                recorded_impressions, date_list, seas_dict, nns_mc, vol, num_weeks, return_type) for i, stream in enumerate(streams))
        total_budget = sum(budgets)

        if objective_type == 'profit':
            return -(total_rev - total_budget)
        elif objective_type == 'roi':
            return -(total_rev / total_budget)
        elif objective_type == 'revenue':
            return -total_rev
        elif objective_type == 'volume':
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

    def output_rev_per_stream(stream, budget, cost_per_dict, carryover_dict, alpha_dict, beta_dict, recorded_impressions,
                          seas_dict, num_weeks):
        cost_per_stream = cost_per_dict.get(stream, 1e-6)  # Set a small non-zero default cost
        allocation = budget / cost_per_stream

        pct_laydown = np.array(recorded_impressions[stream]) / sum(recorded_impressions[stream]) if sum(
            recorded_impressions[stream]) != 0 else np.zeros(len(recorded_impressions[stream]))
        # print(sum(pct_laydown))

        pam = pct_laydown * allocation
        #print(pam)
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
        # total_rev += infsumb
        return indexed_vals

    def blended_profit_max_scipy(ST_input, LT_input, laydown, seas_index, nns_mc, return_type, objective_type, max_budget,
                             exh_budget, method, scenario_name, step=1*10**-5, tolerance=1*10**-5,
                             num_weeks=1000):
        print(type(ST_input))
        
        if objective_type == "roi":
            print("objective type is roi")
            step = 1*10**-25
            tolerance = 1*10**-25
        
        streams = [entry['Opt Channel'] for entry in ST_input]

        current_budget_list = [entry['Current Budget'] for entry in ST_input]
        current_budget_dict = dict(zip(streams, current_budget_list))

        min_spend_cap_list = [float(entry['Min Spend Cap']) for entry in ST_input]
        min_spend_cap_dict = dict(zip(streams, min_spend_cap_list))

        max_spend_cap_list = [float(entry['Max Spend Cap']) for entry in ST_input]
        max_spend_cap_dict = dict(zip(streams, max_spend_cap_list))

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

        ST_beta_list = [float(entry['ST Beta']) if 'ST Beta' in entry and not pd.isna(entry['ST Beta']) and entry[
            'ST Beta'] != np.inf else 0.0 for entry in ST_input]
        ST_beta_dict = dict(zip(streams, ST_beta_list))

        LT_beta_list = [float(entry['LT Beta']) if 'LT Beta' in entry and not pd.isna(entry['LT Beta']) and entry[
            'LT Beta'] != np.inf else 0.0 for entry in LT_input]
        LT_beta_dict = dict(zip(streams, LT_beta_list))

        recorded_impressions = {}
        for x in laydown.columns:
            recorded_impressions[x] = laydown[x].to_list()
        
        date_list = laydown.index.tolist()

        seas_dict = {}
        for x in seas_index.columns:
            seas_dict[x] = seas_index[x].to_list()

        args = (streams, ST_cost_per_dict, ST_carryover_dict, ST_alpha_dict, ST_beta_dict,
                LT_cost_per_dict, LT_carryover_dict, LT_alpha_dict, LT_beta_dict,
                recorded_impressions, date_list, seas_dict, nns_mc, num_weeks, max_budget, exh_budget, return_type, objective_type)

        #initial_budgets = [min(max_spend_cap_dict[stream], max_budget / len(streams)) for stream in streams]
        initial_budgets = [current_budget_dict[stream] for stream in streams]

        bounds = [(min_spend_cap_dict[stream], max_spend_cap_dict[stream]) for stream in streams]

        constraints = []
        if exh_budget:
            constraints.append({'type': 'eq', 'fun': lambda budgets: max_budget - sum(budgets)})
        else:
            constraints.append({'type': 'ineq', 'fun': lambda budgets: sum(budgets) - max_budget})
        print(constraints)

        def optimization_callback(xk):
            # Add any relevant information you want to print or check at each iteration
            print("Current solution:", xk)

        start_time = time.time()
        result = minimize(Optimise.profit_objective, initial_budgets, args=args, bounds=bounds, constraints=constraints,
                        method=method,
                        # callback=optimization_callback,
                        options={'disp': True, 'maxiter': 10000, 'eps': step, 'ftol': tolerance})
        end_time = time.time()
        elapsed_time_seconds = end_time - start_time
        # result = minimize(profit_objective_with_penalty, initial_budgets, args=args, bounds=bounds, method='Powell')#, method=method)

        # result = differential_evolution(profit_objective_with_penalty, bounds, args=args, disp=True)

        opt_budgets_dict = dict(zip(streams, result.x))

        opt_revenues_ST = {'Date': list(laydown.index)}
        opt_revenues_LT = {'Date': list(laydown.index)}
        opt_laydown = {'Date': list(laydown.index)}
        curr_revenue_ST = {'Date': list(laydown.index)}
        curr_revenue_LT = {'Date': list(laydown.index)}
        curr_laydown = {'Date': list(laydown.index)}
        for stream in streams:
            opt_revenues_ST[stream] = Optimise.output_rev_per_stream(stream, opt_budgets_dict[stream],                                                       ST_cost_per_dict,
                                                                                ST_carryover_dict, ST_alpha_dict,
                                                                                ST_beta_dict,
                                                                                recorded_impressions, seas_dict,
                                                                                num_weeks=1000)
            opt_revenues_LT[stream] = Optimise.output_rev_per_stream(stream, opt_budgets_dict[stream],
                                                                    LT_cost_per_dict,
                                                                    LT_carryover_dict, LT_alpha_dict,
                                                                    LT_beta_dict,
                                                                    recorded_impressions, seas_dict,
                                                                    num_weeks=1000)
            curr_revenue_ST[stream] = Optimise.output_rev_per_stream(stream, current_budget_dict[stream],
                                                                                ST_cost_per_dict,
                                                                                ST_carryover_dict, ST_alpha_dict,
                                                                                ST_beta_dict,
                                                                                recorded_impressions, seas_dict,
                                                                                num_weeks=1000)
            curr_revenue_LT[stream] = Optimise.output_rev_per_stream(stream, current_budget_dict[stream],
                                                                    LT_cost_per_dict,
                                                                    LT_carryover_dict, LT_alpha_dict,
                                                                    LT_beta_dict,
                                                                    recorded_impressions, seas_dict,
                                                                    num_weeks=1000)
        opt_revenues_ST_df = pd.DataFrame.from_dict(opt_revenues_ST).set_index('Date').stack().reset_index()
        opt_revenues_ST_df.columns = ['Date', 'Opt Channel', 'Value']
        opt_revenues_ST_df['Scenario'] = scenario_name
        opt_revenues_ST_df['Budget/Revenue'] = 'ST Revenue'
        opt_revenues_LT_df = pd.DataFrame.from_dict(opt_revenues_LT).set_index('Date').stack().reset_index()
        opt_revenues_LT_df.columns = ['Date', 'Opt Channel', 'Value']
        opt_revenues_LT_df['Scenario'] = scenario_name
        opt_revenues_LT_df['Budget/Revenue'] = 'LT Revenue'

        #################################################
        print("attempting to sum laydown")
        opt_laydown = laydown / laydown.sum()
        for stream in streams:
            opt_laydown[stream] = opt_laydown[stream] * opt_budgets_dict[stream]
        opt_laydown = opt_laydown.stack().reset_index()
        opt_laydown.columns = ['Date', 'Opt Channel', 'Value']
        opt_laydown['Scenario'] = scenario_name
        opt_laydown['Budget/Revenue'] = 'Budget'
        #################################################

        curr_revenue_ST_df = pd.DataFrame.from_dict(curr_revenue_ST).set_index('Date').stack().reset_index()
        curr_revenue_ST_df.columns = ['Date', 'Opt Channel', 'Value']
        curr_revenue_ST_df['Scenario'] = scenario_name + ' (Unoptimised)'
        curr_revenue_ST_df['Budget/Revenue'] = 'ST Revenue'
        curr_revenue_LT_df = pd.DataFrame.from_dict(curr_revenue_LT).set_index('Date').stack().reset_index()
        curr_revenue_LT_df.columns = ['Date', 'Opt Channel', 'Value']
        curr_revenue_LT_df['Scenario'] = scenario_name + ' (Unoptimised)'
        curr_revenue_LT_df['Budget/Revenue'] = 'LT Revenue'
        
        #################################################
        print("attempting to sum curr laydown")
        curr_laydown = laydown / laydown.sum()
        for stream in streams:
            curr_laydown[stream] = curr_laydown[stream] * current_budget_dict[stream]
        curr_laydown = curr_laydown.stack().reset_index()
        curr_laydown.columns = ['Date', 'Opt Channel', 'Value']
        curr_laydown['Scenario'] = scenario_name + ' (Unoptimised)'
        curr_laydown['Budget/Revenue'] = 'Budget'
        #################################################

        output_df = pd.concat(
            [curr_laydown, curr_revenue_ST_df, curr_revenue_LT_df, opt_laydown, opt_revenues_ST_df, opt_revenues_LT_df])
        output_df = pd.merge(output_df,
                            pd.DataFrame.from_dict(ST_input)[['Opt Channel', 'Country', 'Brand', 'Channel Group', 'Channel']].drop_duplicates(),
                            on='Opt Channel')

        if result.success:
            print("Optimal Solution Found:")
            for stream in streams:
                print(f"{stream} Budget: {opt_budgets_dict[stream]}")
            print(f"Maximized Profit: {-result.fun}")
        else:
            print("Solver did not find an optimal solution.")
            print(f"Solution failed using budget input of: {max_budget} with max total spend cap of: {sum(max_spend_cap_list)}")

        return opt_budgets_dict, elapsed_time_seconds, output_df

class Beta:

    def prep_rev_per_stream(stream, budget, cost_per_dict, carryover_dict, recorded_impressions, seas_dict, alpha_dict, beta_dict, num_weeks=1000):
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


    def prep_total_rev_per_stream(stream, budget, ST_cost_per_dict, ST_carryover_dict, ST_alpha_dict, ST_beta_dict, LT_cost_per_dict, LT_carryover_dict, LT_alpha_dict, LT_beta_dict):

        ST_rev = Beta.prep_rev_per_stream(stream, budget, ST_cost_per_dict, ST_carryover_dict, ST_alpha_dict, ST_beta_dict)
        LT_rev = Beta.prep_rev_per_stream(stream, budget, LT_cost_per_dict, LT_carryover_dict, LT_alpha_dict, LT_beta_dict)
        total_rev = ST_rev + LT_rev
        return total_rev


    def beta_calculation(header, laydown, seas_dict, inc_rev, stlt):

        # Show column headers without underscores!

        header.columns = [x.replace("_", " ") for x in header.columns.tolist()]
        
        laydown.fillna(0)
        
        for x in laydown.columns.tolist():
            if x not in header['Opt Channel'].tolist() and x != 'Date':
                # print(x)
                laydown.drop(columns=[x], inplace=True)

        streams = []
        for stream in header['Opt Channel']:
            streams.append(str(stream))

        for stream in streams:
            header.loc[header['Opt Channel'] == stream, 'Current Budget'] = sum(laydown[stream])

            header.loc[header['Opt Channel'] == stream, f'{stlt.upper()} Revenue'] = sum(inc_rev[stream])
        print(header)
        header[f'{stlt.upper()} Current ROI'] = header[f'{stlt.upper()} Revenue'] / header['Current Budget']

        header_dict = header.to_dict("records")

        cost_per_list = [float(entry['CPU']) for entry in header_dict]
        cost_per_dict = dict(zip(streams, cost_per_list))

        carryover_list = [float(entry[f'{stlt.upper()} Carryover']) for entry in header_dict]
        carryover_dict = dict(zip(streams, carryover_list))

        beta_dict = dict(zip(streams, [1] * len(streams)))

        alpha_list = [float(entry[f'{stlt.upper()} Alpha']) for entry in header_dict]
        alpha_dict = dict(zip(streams, alpha_list))
        raw_input_data = header.to_dict("records")
        current_budget_list = [entry['Current Budget'] for entry in raw_input_data]
        current_budget_dict = dict(zip(streams, current_budget_list))

        recorded_impressions = {}
        for x in laydown.columns:
            recorded_impressions[x] = laydown.fillna(0)[x].to_list()

        beta_calc_rev_dict = {'Date': list(laydown.Date)}
        for stream in list(streams):
            beta_calc_rev_dict[stream] = Beta.prep_rev_per_stream(stream, current_budget_dict[stream], cost_per_dict,
                                                                carryover_dict, recorded_impressions, seas_dict, alpha_dict, beta_dict)
            sum(beta_calc_rev_dict[stream])
        beta_calc_df = pd.DataFrame(beta_calc_rev_dict)[list(streams)].sum().reset_index()
        beta_calc_df.columns = ['Opt Channel', 'Calc_Rev']
        beta_calc_df = pd.merge(beta_calc_df, header[['Opt Channel', f'{stlt.upper()} Revenue']], on='Opt Channel')
        beta_calc_df[f'{stlt.upper()} Beta'] = np.where(beta_calc_df['Calc_Rev'] == 0, 0,
                                        beta_calc_df[f'{stlt.upper()} Revenue'] / beta_calc_df['Calc_Rev'])
        opt_betas_dict = dict(zip(streams, beta_calc_df[f'{stlt.upper()} Beta'].tolist()))

        header[f'{stlt.upper()} Beta'] = list(opt_betas_dict.values())

        # header['LT Revenue'] = header['Current Budget'] * header['LT Current ROI']

        # LT_header_dict = header.to_dict("records")

        # LT_cost_per_list = [float(entry['CPU']) for entry in LT_header_dict]
        # LT_cost_per_dict = dict(zip(streams, LT_cost_per_list))

        # LT_carryover_list = [float(entry['LT Carryover']) for entry in LT_header_dict]
        # LT_carryover_dict = dict(zip(streams, LT_carryover_list))

        # LT_beta_dict = dict(zip(streams, [1] * len(streams)))

        # LT_alpha_list = [float(entry['LT Alpha']) for entry in LT_header_dict]
        # LT_alpha_dict = dict(zip(streams, LT_alpha_list))
        # raw_input_data = header.to_dict("records")
        # current_budget_list = [entry['Current Budget'] for entry in raw_input_data]
        # current_budget_dict = dict(zip(streams, current_budget_list))

        # recorded_impressions = {}
        # for x in laydown.columns:
        #     recorded_impressions[x] = laydown.fillna(0)[x].to_list()

        # beta_calc_rev_dict_LT = {'Date': list(laydown.Date)}
        # for stream in list(streams):
        #     beta_calc_rev_dict_LT[stream] = Beta.prep_rev_per_stream(stream, current_budget_dict[stream], LT_cost_per_dict, LT_carryover_dict, recorded_impressions, seas_dict, LT_alpha_dict, LT_beta_dict)
        #     sum(beta_calc_rev_dict_ST[stream])
        # beta_calc_df = pd.DataFrame(beta_calc_rev_dict_ST)[list(streams)].sum().reset_index()
        # beta_calc_df.columns = ['Opt Channel', 'Calc_Rev']
        # beta_calc_df = pd.merge(beta_calc_df, header[['Opt Channel', 'LT Revenue']], on='Opt Channel')
        # beta_calc_df['LT Beta'] = np.where(beta_calc_df['Calc_Rev'] == 0, 0,
        #                                 beta_calc_df['LT Revenue'] / beta_calc_df['Calc_Rev'])
        # LT_opt_betas_dict = dict(zip(streams, beta_calc_df['LT Beta'].tolist()))

        # header['LT Beta'] = list(LT_opt_betas_dict.values())

        header_copy = header.copy()

        return header_copy

        

        

