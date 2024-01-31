import pandas as pd
import numpy as np
import statsmodels.api as sm
import optuna 
import math
from io import StringIO
import sys
# disable chained assignments
pd.options.mode.chained_assignment = None
class alpha_opt:

    # view_mod = initial statsmodels OLS fit call (sm.OLS)
    # X = independent variables
    # y = dependent variable
    # opt_vars = list of variables in X that we are fitting the curve for (optimising for alpha)
    # t_val_con = number (from 0 to 1) for the t_value constraint. (e.g. 0.2)
    # n_trials = number of optuna trials to run
    # priority_vars = list of non dummy var column names
    # filter_method = "min_violating_constraints" or "min_aic"
    # returns dataframe with applied alpha value from best trial

    def optimise(view_mod, X, y, cross, date_id, opt_vars, t_val_con=0.25, base_pct_con=0.5, n_trials=10000,
                 priority_vars=[], ar1_bool=False, base_pct_bool=True, filter_method='min_violating_constraints', output_log_filepath='G:/5. Development/TMO 3.0/Curve Optimiser/alpha_opt_log.txt'):

        pct_change_violating_vars = []
        sc_change_violating_vars = []
        pct_change_vio_base_vars = []

        def objective(trial):
            
            orig_tvalue = list(view_mod.tvalues)
            # Create a copy of the X DataFrame to avoid modifying the original data
            new_X = X.copy()
            X_cols = list(X.columns)
            modified_X = X.loc[:, opt_vars].copy()

            for col in opt_vars:

                x_max = modified_X[col].max()

                decimal_places = math.floor(math.log10(x_max))
                range_start = (10 ** (-decimal_places)) / 10
                range_end = 9 * range_start

                alpha = trial.suggest_float(f'alpha_{col}', range_start, range_end)

                modified_X[col] = 1 - np.exp(-alpha * X[col])

            new_X = new_X.drop(opt_vars, axis=1)
            final_X = pd.concat([new_X, modified_X], axis=1, sort=False)
            
            trial_model = sm.OLS(y, final_X).fit()

            if ar1_bool:
                X_temp = final_X.copy()
                y_temp = y.copy()
                
                for col in y.columns:
                    y_name = col

                data_temp = pd.merge(X_temp.reset_index(), y_temp.reset_index(), how="left", on=[cross, date_id] )
                errors = list(trial_model.resid)

                derrors = data_temp.loc[:, cross:date_id]
                derrors["errors"] = errors
                derrors['prev_errors'] = derrors.groupby(cross)["errors"].shift()

                err_model = sm.OLS(derrors.dropna()['errors'],derrors.dropna()['prev_errors'])
                err_res = err_model.fit()

                rho = err_res.params[0]

                #Get X_columns and shift by cross section
                X_t = data_temp[X_cols+[cross]]
                X_t_1 = X_t.groupby(cross).shift()

                #Do rho transform and remove cross secrion
                X_transform = X_t.drop(cross,axis=1) - rho*X_t_1

                X_transform["AR(1)"] = rho*data_temp.groupby(cross)[y_name].shift(1)

                nan_indices = X_transform[pd.isnull(X_transform).any(axis=1)].index
                for i in nan_indices:
                    X_transform.iloc[i] = [(1-rho)**0.5*j for j in list(data_temp[X_cols].iloc[i])]+[0]
                    data_temp[y_name].iloc[i] = (1-rho)**(0.5)*(data_temp[y_name].iloc[i]-trial_model.resid[i])
                
                data_temp = data_temp.set_index([cross, date_id])

                rf = sm.OLS(list(data_temp[y_name]),X_transform)
                result = rf.fit()

                aic = result.aic
                trial_tvalue = list(result.tvalues)
            else:
                aic = trial_model.aic
                trial_tvalue = list(trial_model.tvalues)

            print(f"aic score: {aic}")


            arr1 = np.array(orig_tvalue)
            arr2 = np.array(trial_tvalue)

            orig_tvalue_dict = dict(zip(X_cols, orig_tvalue))
            model_tvalue_dict = dict(zip(X_cols, trial_tvalue))

            x = t_val_con
            z = base_pct_con

            sc_list = {}
            lt_list = {}
            lt2_list = {}
            sc_list_out = {}
            lt_list_out = {}
            lt2_list_out = {}

            for col in X_cols:
                if orig_tvalue_dict[col] < 0:
                    sc_list[col] = (model_tvalue_dict[col])
                else:
                    sc_list[col] = -1*model_tvalue_dict[col]
            
            for key, value in sc_list.items():
                if value > 0:
                    sc_list_out[key] = value
            print(f"vars violating sc constraint: {sc_list_out}")
            sc_change_violating_vars.append(sc_list_out)
            c0 = 0
            c0 = 1000*sum(sc_list_out.values())

            for col in opt_vars:

                lt_list[col] = -1*(((model_tvalue_dict[col] - orig_tvalue_dict[col]) / orig_tvalue_dict[col]) + x)

            for key, value in lt_list.items():

                if value > 0:
                    lt_list_out[key] = value
            pct_change_violating_vars.append(lt_list_out)
            c1 = 1000*sum(lt_list_out.values())

            if base_pct_bool:   # input for obj

                for col in [x for x in X_cols if x not in opt_vars]:

                    lt2_list[col] = -1*(((model_tvalue_dict[col] - orig_tvalue_dict[col]) / orig_tvalue_dict[col]) + z)

                for key, value in lt2_list.items():

                    if value > 0:
                        lt2_list_out[key] = value
                pct_change_vio_base_vars.append(lt2_list_out)
                c2 = 1000*sum(lt_list_out.values())

            print(f"vars violating pct change constraint: {lt_list_out}")
            if base_pct_bool:
                print(f"base vars violating pct change constraint: {lt2_list_out}")
                trial.set_user_attr("constraint", (c0, c1, c2))
            else:
                trial.set_user_attr("constraint", (c0, c1))

            return aic

        def constraints(trial):
            return trial.user_attrs["constraint"]
        
        sampler = optuna.samplers.NSGAIISampler(constraints_func=constraints)

        # Create an Optuna study
        output_buffer = StringIO()
        sys.stdout = output_buffer

        study = optuna.create_study(directions=['minimize'], sampler=sampler)
        study.optimize(objective, n_trials=n_trials)

        best_trial = None
        best_value = float('inf')
        lowest_sc_score = float('inf')
        lowest_lt_score = float('inf')
        lowest_l2_score = float('inf')
        all_trials = list(study.trials)
        disallowed_trials = []
        potential_trials = []

        for trial in all_trials:

            trial_sc_score = trial.user_attrs["constraint"][0]
            trial_pct_change_score = trial.user_attrs["constraint"][1]
            trial_sc_vio_dict = sc_change_violating_vars[trial.number]
            trial_lt_vio_dict = pct_change_violating_vars[trial.number]
            if base_pct_bool:
                trial_base_pct_dict = pct_change_vio_base_vars[trial.number]
                trial_base_pct_score = trial.user_attrs["constraint"][2]
            else:
                trial_base_pct_score = 0
                trial_base_pct_dict = {}

            if trial_sc_score == 0 and trial_pct_change_score == 0 and trial_base_pct_score == 0 and trial.value < best_value:
                best_value = trial.value
                best_trial = trial

        if best_trial is None:

            for trial in all_trials:

                trial_sc_score = trial.user_attrs["constraint"][0]
                trial_pct_change_score = trial.user_attrs["constraint"][1]
                trial_sc_vio_dict = sc_change_violating_vars[trial.number]
                trial_lt_vio_dict = pct_change_violating_vars[trial.number]
                if base_pct_bool:
                    trial_base_pct_dict = pct_change_vio_base_vars[trial.number]
                    trial_base_pct_score = trial.user_attrs["constraint"][2]
                else:
                    trial_base_pct_score = 0
                    trial_base_pct_dict = {}

                # [priority vars] + opt_vars  must remain same sign, take as input

                trial_sc_vio_var_list = []

                for x in list(trial_sc_vio_dict.keys()):
                    if x in opt_vars:
                        trial_sc_vio_var_list.append(x)
                    if x in priority_vars:
                        trial_sc_vio_var_list.append(x)

                if trial_sc_vio_var_list != []:
                    print(f"trial {trial.number} cannot be chosen as {trial_sc_vio_var_list} violates sc change constraint")
                    if trial not in disallowed_trials:
                        disallowed_trials.append(trial)
                    continue

                for var in opt_vars:
                    if var in list(trial_sc_vio_dict.keys()) and var in list(trial_lt_vio_dict.keys()):
                        print(f"trial {trial.number} cannot be chosen as opt var {var} violates sc + pct change constraints")
                        if trial not in disallowed_trials:
                            disallowed_trials.append(trial)
                        continue
                if trial not in disallowed_trials:
                    print(f"trial {trial.number} is a potential trial with no priority var or opt var sc violations, or any opt var pct change violations and a score of {trial.value}")                
                    potential_trials.append(trial)

            for x in potential_trials:
                if x in disallowed_trials:
                    potential_trials.remove(x)
                # take base variable pct_change const - allow base vars to fluctuate more - first elif statement, least important constraint, ignore it and check for best trial
            sorted_pot_trials = sorted(potential_trials, key=lambda x: x.value)
            print("top 5 potential trials:")
            if potential_trials != []:
                for i in range(5):
                    print(sorted_pot_trials[i])
                    print(f"vars violating sc change: {sc_change_violating_vars[sorted_pot_trials[i].number]}")
                    print(f"vars violating lt change: {pct_change_violating_vars[sorted_pot_trials[i].number]}")
                    print(f"base vars violating lt change: {pct_change_vio_base_vars[sorted_pot_trials[i].number]}")
            else:
                # IN POTENTIAL TRIALS THERE ARE NO TRIALS WITH ANY OPT VAR OR PRIORITY VAR VIOLATIONS
                # IN THE CASE THAT THERE ARE NO POTENTIAL TRIALS AT ALL, WE RE RUN THE OPTIMISER, WITH A MODIFIED OPT_VARS LIST
                repeat_opt_var_vio_dict = {}
                opt_var_vals = []
                for x in opt_vars:
                    opt_var_vals.append(0)
                opt_dict = dict(zip(opt_vars, opt_var_vals))
                for trial in disallowed_trials:
                    for x in opt_vars:
                        if x in list(sc_change_violating_vars[trial.number].keys()):
                            new_val = opt_dict[x] + 1
                            opt_dict[x] = new_val

                opt_vars = [x for x in opt_vars if opt_dict[x] != n_trials]
                
                filtered_study = optuna.create_study(directions=['minimize'], sampler=sampler)
                filtered_study.optimize(objective, n_trials=n_trials)

                # FILTER

                best_trial = None
                best_value = float('inf')
                lowest_sc_score = float('inf')
                lowest_lt_score = float('inf')
                lowest_l2_score = float('inf')
                all_trials = list(study.trials)
                disallowed_trials = []
                potential_trials = []

                for trial in all_trials:

                    trial_sc_score = trial.user_attrs["constraint"][0]
                    trial_pct_change_score = trial.user_attrs["constraint"][1]
                    trial_sc_vio_dict = sc_change_violating_vars[trial.number]
                    trial_lt_vio_dict = pct_change_violating_vars[trial.number]
                    if base_pct_bool:
                        trial_base_pct_dict = pct_change_vio_base_vars[trial.number]
                        trial_base_pct_score = trial.user_attrs["constraint"][2]
                    else:
                        trial_base_pct_score = 0
                        trial_base_pct_dict = {}

                    if trial_sc_score == 0 and trial_pct_change_score == 0 and trial_base_pct_score == 0 and trial.value < best_value:
                        best_value = trial.value
                        best_trial = trial

                if best_trial is None:

                    for trial in all_trials:

                        trial_sc_score = trial.user_attrs["constraint"][0]
                        trial_pct_change_score = trial.user_attrs["constraint"][1]
                        trial_sc_vio_dict = sc_change_violating_vars[trial.number]
                        trial_lt_vio_dict = pct_change_violating_vars[trial.number]
                        if base_pct_bool:
                            trial_base_pct_dict = pct_change_vio_base_vars[trial.number]
                            trial_base_pct_score = trial.user_attrs["constraint"][2]
                        else:
                            trial_base_pct_score = 0
                            trial_base_pct_dict = {}

                        # [priority vars] + opt_vars  must remain same sign, take as input

                        trial_sc_vio_var_list = []

                        for x in list(trial_sc_vio_dict.keys()):
                            if x in opt_vars:
                                trial_sc_vio_var_list.append(x)
                            if x in priority_vars:
                                trial_sc_vio_var_list.append(x)

                        if trial_sc_vio_var_list != []:
                            print(f"trial {trial.number} cannot be chosen as {trial_sc_vio_var_list} violates sc change constraint")
                            if trial not in disallowed_trials:
                                disallowed_trials.append(trial)
                            continue

                        for var in opt_vars:
                            if var in list(trial_sc_vio_dict.keys()) and var in list(trial_lt_vio_dict.keys()):
                                print(f"trial {trial.number} cannot be chosen as opt var {var} violates sc + pct change constraints")
                                if trial not in disallowed_trials:
                                    disallowed_trials.append(trial)
                                continue
                        if trial not in disallowed_trials:
                            print(f"trial {trial.number} is a potential trial with no priority var or opt var sc violations, or any opt var pct change violations and a score of {trial.value}")                
                            potential_trials.append(trial)

                    for x in potential_trials:
                        if x in disallowed_trials:
                            potential_trials.remove(x)


            if filter_method == "min_violating_constraints":

                low_const_pot_list = []
                for x in potential_trials:
                    if len(sc_change_violating_vars[x.number]) == min([len(x) for x in sc_change_violating_vars]):
                        low_const_pot_list.append(x)
                

                low_const_base_pot_list = []
                if base_pct_bool:
                    for x in low_const_pot_list:
                        if len(pct_change_vio_base_vars[x.number]) == min([len(x) for x in pct_change_vio_base_vars]):
                            low_const_base_pot_list.append(x)
                    low_const_pot_list = low_const_base_pot_list

                low_const_sorted = sorted(low_const_pot_list, key=lambda x: x.value)
                if low_const_sorted == []:
                    print('no potential trials - exiting optimiser!')
                else:
                    print(f"trial with fewest number of constraint violations with lowest aic: {low_const_sorted[0]}")
                    print(low_const_sorted[0].params)
                    best_trial = low_const_sorted[0]

            elif filter_method == "min_aic":
                if low_const_sorted == []:
                    print('no potential trials - exiting optimiser!')
                else:
                    pot_trial_aic_list = [x.value for x in potential_trials]
                    print(f"trial with best aic score while still having constraint violations:{potential_trials[pot_trial_aic_list.index(min(pot_trial_aic_list))]}")
                    print(potential_trials[pot_trial_aic_list.index(min(pot_trial_aic_list))].params)
                    best_trial = potential_trials[pot_trial_aic_list.index(min(pot_trial_aic_list))]

        # APPLY ALPHAS OF BEST TRIAL AND RETURN X, ADDING AR1 TERM IF NEEDED
        if best_trial is not None:
            new_X = X.copy()
            X_cols = list(X.columns)
            modified_X = X.loc[:, opt_vars].copy()
            alpha_dict = best_trial.params

            for key, value in alpha_dict.items():

                modified_X[key[6:]] = 1 - np.exp(-value * X[key[6:]])

            new_X = new_X.drop(opt_vars, axis=1)

            final_X = pd.concat([new_X, modified_X], axis=1, sort=False)
            final_y = y.copy()

            trial_model = sm.OLS(y, final_X).fit()

            if ar1_bool:

                X_temp = final_X.copy()
                y_temp = y.copy()

                for col in y.columns:
                    y_name = col

                data_temp = pd.merge(X_temp.reset_index(), y_temp.reset_index(), how="left", on=[cross, date_id] )
                errors = list(trial_model.resid)

                derrors = data_temp.loc[:, cross:date_id]
                derrors["errors"] = errors
                derrors['prev_errors'] = derrors.groupby(cross)["errors"].shift()

                err_model = sm.OLS(derrors.dropna()['errors'],derrors.dropna()['prev_errors'])
                err_res = err_model.fit()

                rho = err_res.params[0]

                #Get X_columns and shift by cross section
                X_t = data_temp[X_cols+[cross]]
                X_t_1 = X_t.groupby(cross).shift()

                #Do rho transform and remove cross secrion
                X_transform = X_t.drop(cross,axis=1) - rho*X_t_1

                X_transform["AR(1)"] = rho*data_temp.groupby(cross)[y_name].shift(1)

                nan_indices = X_transform[pd.isnull(X_transform).any(axis=1)].index
                for i in nan_indices:
                    X_transform.iloc[i] = [(1-rho)**0.5*j for j in list(data_temp[X_cols].iloc[i])]+[0]
                    data_temp[y_name].iloc[i] = (1-rho)**(0.5)*(data_temp[y_name].iloc[i]-trial_model.resid[i])
                final_y = data_temp[y_name].copy()
                final_X = X_transform.copy()
        else:
            final_y = y.copy()
            final_X = X.copy()
            alpha_dict = None

        captured_output = output_buffer.getvalue()
        sys.stdout = sys.__stdout__
        

        return final_y, final_X, alpha_dict, captured_output