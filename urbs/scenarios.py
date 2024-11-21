import shutil
import os
import pandas as pd
from openpyxl import load_workbook

# SCENARIO GENERATORS
# In this script a variety of scenario generator functions are defined to
# facilitate scenario definitions.

########################################################################################################################
########################################################################################################################
########################################################################################################################
#############################################----us_szenarios----#######################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################


#base
def scenario_base(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    # do nothing
    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#normal fossil fuel and delayed CO2 pricing
def scenario_1(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not data:
        print("Warning: param_dict is empty.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    elif 'commodity' in data:
        co = data['commodity']
        for stf in data['global_prop'].index.levels[0].tolist():
            # Check if the year (stf) is before 2030
            if stf < 2030:
                # Set CO2 price to 0 for years before 2030
                co.loc[(stf, 'EU27', 'CO2', 'Env'), 'price'] = 0
            else:
                # Keep the existing values for 2030 and later years
                co.loc[(stf, 'EU27', 'CO2', 'Env'), 'price'] = co.loc[(stf, 'EU27', 'CO2', 'Env'), 'price']

        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    else:
        print("Warning: 'commodity' not found in data.")

########################################################################################################################

#high fossil fuel and CO2 prices
def scenario_2(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not data:
        print("Warning: data is empty.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    elif 'commodity' in data:
        co = data['commodity']
        fossil_fuels = ['Lignite', 'Gas', 'Coal', 'Nuclear Fuel']
        for stf in data['global_prop'].index.levels[0].tolist():
            co.loc[(stf, 'EU27', 'CO2', 'Env'), 'price'] *= 1.5
            for fuel in fossil_fuels:
                co.loc[(stf, 'EU27', fuel, 'Stock'), 'price'] *= 1.5
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    else:
        print("Warning: 'commodity' not found in data.")

########################################################################################################################

#normal fossil fuel and zero CO2 pricing
def scenario_3(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not data:
        print("Warning: data is empty.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    elif 'commodity' in data:
        co = data['commodity']
        for stf in data['global_prop'].index.levels[0].tolist():
            co.loc[(stf, 'EU27', 'CO2', 'Env'), 'price'] = 0 #set co2 price to 0
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    else:
        print("Warning: 'commodity' not found in data.")

########################################################################################################################

#high investement into CCUS technology
def scenario_4(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not data:
        print("One or more dictionaries are empty. Returning original data.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

    if 'processes' in data:
        pro = data['processes']
        for stf in data['global_prop'].index.levels[0].tolist():
            if stf >= 2029:
                pro.loc[(stf, 'EU27', 'Coal CCUS'), 'cap-up'] = 9999
                pro.loc[(stf, 'EU27', 'Coal CCUS'), 'inv-cost'] *= 0.9
                pro.loc[(stf, 'EU27', 'Coal Lignite CCUS'), 'cap-up'] = 9999
                pro.loc[(stf, 'EU27', 'Coal Lignite CCUS'), 'inv-cost'] *= 0.9
            if stf >= 2033:
                pro.loc[(stf, 'EU27', 'Gas Plant (CCGT) CCUS'), 'cap-up'] = 9999
                pro.loc[(stf, 'EU27', 'Gas Plant (CCGT) CCUS'), 'inv-cost'] *= 0.9

    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#low investement into CCUS technology
def scenario_5(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not data:
        print("One or more dictionaries are empty. Returning original data.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

    if 'processes' in data:
        pro = data['processes']
        for stf in data['global_prop'].index.levels[0].tolist():
            if stf >= 2029:
                pro.loc[(stf, 'EU27', 'Coal CCUS'), 'cap-up'] = 9999
                pro.loc[(stf, 'EU27', 'Coal CCUS'), 'inv-cost'] *= 1.1
                pro.loc[(stf, 'EU27', 'Coal Lignite CCUS'), 'cap-up'] = 9999
                pro.loc[(stf, 'EU27', 'Coal Lignite CCUS'), 'inv-cost'] *= 1.1
            if stf >= 2033:
                pro.loc[(stf, 'EU27', 'Gas Plant (CCGT) CCUS'), 'cap-up'] = 9999
                pro.loc[(stf, 'EU27', 'Gas Plant (CCGT) CCUS'), 'inv-cost'] *= 1.1
    if 'process_commodity' in data:
        proco = data['process_commodity']
        for stf in data['global_prop'].index.levels[0].tolist():
            proco.loc[(stf, 'Coal CCUS','CO2','Out'),'ratio'] *= 4
            proco.loc[(stf, 'Coal Lignite CCUS', 'CO2', 'Out'), 'ratio'] *= 4
            proco.loc[(stf, 'Gas Plant (CCGT) CCUS', 'CO2', 'Out'), 'ratio'] *= 4
    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#phase out of fossil fuels with anticipated target years

def scenario_6(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not data:
        print("Warning: param_dict is empty.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    elif 'process' in data:
        pro = data['process']
        for stf in data['global_prop'].index.levels[0].tolist():
            print(stf)
            if 'lifetime' in pro.columns:  # Check for the specific timeframe
                try:
                    # Modify the process lifetimes as per the scenario
                    pro.loc[(stf, 'EU27', 'Coal Plant'), 'lifetime'] = 10 #new phaseout years 2024 + value
                    pro.loc[(stf, 'EU27', 'Coal Lignite'), 'lifetime'] = 5 #new phaseout years 2024 + value
                    pro.loc[(stf, 'EU27', 'Gas Plant (CCGT)'), 'lifetime'] = 9 #new phaseout years 2024 + value
                except KeyError as e:
                    print(f"Warning: KeyError for {e}. The process might not exist for 2024.")
            else:
                # If the row is not for 2024, we simply skip it.
                print(f"Skipping year {stf} as it's not 2024.")

        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    else:
        print("Warning: 'process' not found in data.")

########################################################################################################################

#delayed fossil fuel phaseout same as scenario 6
def scenario_7(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not data:
        print("Warning: param_dict is empty.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    elif 'process' in data:
        pro = data['process']
        for stf in data['global_prop'].index.levels[0].tolist():
            print(stf)
            if 'lifetime' in pro.columns:  # Check for the specific timeframe
                try:
                    # Modify the process lifetimes as per the scenario
                    pro.loc[(stf, 'EU27', 'Coal Plant'), 'lifetime'] = 5  # new phaseout years 2024 + value
                    pro.loc[(stf, 'EU27', 'Coal Lignite'), 'lifetime'] = 5  # new phaseout years 2024 + value
                    pro.loc[(stf, 'EU27', 'Gas Plant (CCGT)'), 'lifetime'] = 9  # new phaseout years 2024 + value
                except KeyError as e:
                    print(f"Warning: KeyError for {e}. The process might not exist for 2024.")
            else:
                # If the row is not for 2024, we simply skip it.
                print(f"Skipping year {stf} as it's not 2024.")

        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    else:
        print("Warning: 'process' not found in data.")

########################################################################################################################

#CCUS instead of normal fossil power plants after phase out
def scenario_8(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not data:
        print("One or more dictionaries are empty. Returning original data.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

    if 'processes' in data:
        pro = data['processes']
        for stf in data['global_prop'].index.levels[0].tolist():
            if stf >= 2029:
                pro.loc[(stf, 'EU27', 'Coal CCUS'), 'cap-up'] = 9999
                pro.loc[(stf, 'EU27', 'Coal Lignite CCUS'), 'cap-up'] = 9999
            if stf >= 2033:
                pro.loc[(stf, 'EU27', 'Gas Plant (CCGT) CCUS'), 'cap-up'] = 9999

    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#meeting expansion plans for REPowerEU
def scenario_9(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#high tolerance for RES expansion
def scenario_10(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not data or not instalable_capacity_dict:
        print("One or more dictionaries are empty. Returning original data.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

    if 'process' in data:
        pro = data['process']
        for stf in data['global_prop'].index.levels[0].tolist():
            if stf <= 2030.0:
                pro.loc[(stf, 'EU27', 'Wind (onshore)'), 'cap-up'] = 379885#Value for cap up
                pro.loc[(stf, 'EU27', 'Wind (offshore)'), 'cap-up'] = 240293#Value for cap up
                pro.loc[(stf, 'EU27', 'Hydro (run-of-river)'), 'cap-up'] =50000 #Value for cap up
                pro.loc[(stf, 'EU27', 'Hydro (reservoir)'), 'cap-up'] = 80000#Value for cap up
            elif stf <= 2040.0:
                pro.loc[(stf, 'EU27', 'Wind (onshore)'), 'cap-up'] = 620169#Value for cap up
                pro.loc[(stf, 'EU27', 'Wind (offshore)'), 'cap-up'] = 458034#Value for cap up
                pro.loc[(stf, 'EU27', 'Hydro (run-of-river)'), 'cap-up'] =80000 #Value for cap up
                pro.loc[(stf, 'EU27', 'Hydro (reservoir)'), 'cap-up'] =110000 #Value for cap up
            else:
                pro.loc[(stf, 'EU27', 'Wind (onshore)'), 'cap-up'] =799440 #Value for cap up
                pro.loc[(stf, 'EU27', 'Wind (offshore)'), 'cap-up'] = 675796#Value for cap up
                pro.loc[(stf, 'EU27', 'Hydro (run-of-river)'), 'cap-up'] =110000 #Value for cap up
                pro.loc[(stf, 'EU27', 'Hydro (reservoir)'), 'cap-up'] =140000 #Value for cap up

    if 'Instalable Capacity' in instalable_capacity_dict:
        for year, cap in instalable_capacity_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2024:
                    new_cap = float(cap) * 1.1  # Factor by how much
                    instalable_capacity_dict[year] = new_cap
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated eu_primary_cost_dict:", instalable_capacity_dict)

    # Return the updated dictionaries/data
    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#low tolerance for RES expansion
def scenario_11(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not data or not instalable_capacity_dict:
        print("One or more dictionaries are empty. Returning original data.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

    if 'process' in data:
        pro = data['process']
        for stf in data['global_prop'].index.levels[0].tolist():
            if stf <= 2030.0:
                pro.loc[(stf, 'EU27', 'Wind (onshore)'), 'cap-up'] = 299697 # Value for cap up
                pro.loc[(stf, 'EU27', 'Wind (offshore)'), 'cap-up'] = 100989 # Value for cap up
                pro.loc[(stf, 'EU27', 'Hydro (run-of-river)'), 'cap-up'] =46710  # Value for cap up
                pro.loc[(stf, 'EU27', 'Hydro (reservoir)'), 'cap-up'] =  59840# Value for cap up
            elif stf <= 2040.0:
                pro.loc[(stf, 'EU27', 'Wind (onshore)'), 'cap-up'] = 377767 # Value for cap up
                pro.loc[(stf, 'EU27', 'Wind (offshore)'), 'cap-up'] =  269420# Value for cap up
                pro.loc[(stf, 'EU27', 'Hydro (run-of-river)'), 'cap-up'] = 46710 # Value for cap up
                pro.loc[(stf, 'EU27', 'Hydro (reservoir)'), 'cap-up'] =  59840# Value for cap up
            else:
                pro.loc[(stf, 'EU27', 'Wind (onshore)'), 'cap-up'] =  414687# Value for cap up
                pro.loc[(stf, 'EU27', 'Wind (offshore)'), 'cap-up'] =  377545# Value for cap up
                pro.loc[(stf, 'EU27', 'Hydro (run-of-river)'), 'cap-up'] = 46710 # Value for cap up
                pro.loc[(stf, 'EU27', 'Hydro (reservoir)'), 'cap-up'] =  59840# Value for cap up

    if 'Instalable Capacity' in instalable_capacity_dict:
        for year, cap in instalable_capacity_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2024:
                    new_cap = float(cap) * 0.8  # Factor by how much
                    instalable_capacity_dict[year] = new_cap
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated eu_primary_cost_dict:", instalable_capacity_dict)

        # Return the updated dictionaries/data
    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#high importcost due to importtolls on solar modules

def scenario_12(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not importcost_dict or not param_dict:
        print("Warning: importcost_dict is empty.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    for year, cost in importcost_dict.items():
        try:
            year_int = int(year)
            if year_int >= 2035: #year where importcost suddenly rises
                new_cost = float(cost) * 3  # Factor by how much
                importcost_dict[year] = new_cost
        except ValueError:
            print(f"Warning: Non-numeric year '{year}' found. Skipping.")

    if 'anti dumping Index' in param_dict:
        current_value = float(param_dict['anti dumping Index'])
        new_value = current_value + 0.05 #add 5%
        param_dict['anti dumping Index'] = new_value
        print("anti dumping Index updated.")
    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#subsidees on eu manufacturing in order to achieve independence from China

def scenario_13(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not eu_primary_cost_dict or not param_dict:
        print("Warning: importcost_dict is empty.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    for year, cost in eu_primary_cost_dict.items():
        try:
            year_int = int(year)
            if year_int >= 2024: #year where manufacturing gets cheaper
                new_cost = float(cost) * 0.9  # Factor by how much
                importcost_dict[year] = new_cost
        except ValueError:
            print(f"Warning: Non-numeric year '{year}' found. Skipping.")

    if 'anti dumping Index' in param_dict:
        current_value = float(param_dict['anti dumping Index'])
        new_value = current_value + 0.05 #add 5%
        param_dict['anti dumping Index'] = new_value
        print("anti dumping Index updated.")
    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#complete importstop on solar modules from China due to sanctions

def scenario_14(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not importcost_dict:
        print("Warning: importcost_dict is empty.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    for year, cost in importcost_dict.items():
        try:
            year_int = int(year)
            if year_int >= 2035: #sudden import stop
                new_cost = float(cost) * 9999999999999  # Factor by how much
                importcost_dict[year] = new_cost
        except ValueError:
            print(f"Warning: Non-numeric year '{year}' found. Skipping.")
    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#high investements and development  for domestic production and recycling

def scenario_15(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):

    if not param_dict or not eu_primary_cost_dict or not eu_secondary_cost_dict:
        print("One or more dictionaries are empty. Returning original data.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

    # Check if 'commodity' exists in the data and modify it
    if 'IR EU Primary' in param_dict:
        current_value = float(param_dict['IR EU Primary'])
        new_value = current_value + 0.05 #add 5%
        param_dict['IR EU Primary'] = new_value
        print("IR EU updated.")

    # Check if param_dict exists and modify it if needed
    if 'IR EU Secondary' in param_dict:
        current_value = float(param_dict['IR EU Secondary'])
        new_value = current_value + 0.05 #add 5%
        param_dict['IR EU Secondary'] = new_value
        print("IR secondary updated.")

    if 'anti dumping Index' in param_dict:
        current_value = float(param_dict['anti dumping Index'])
        new_value = current_value + 0.05 #add 5%
        param_dict['anti dumping Index'] = new_value
        print("anti dumping Index updated.")

    # Modify the eu_primary_cost_dict if applicable
    if eu_primary_cost_dict:
        for year, cost in eu_primary_cost_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2024:  # year where manufacturing gets cheaper
                    new_cost = float(cost) * 0.6  # Factor by how much
                    eu_primary_cost_dict[year] = new_cost
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated eu_primary_cost_dict:", eu_primary_cost_dict)
    #modify eu secondary cost
    if eu_secondary_cost_dict:
        for year, cost in eu_secondary_cost_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2024:  # year where manufacturing gets cheaper
                    new_cost = float(cost) * 0.8  # Factor by how much
                    eu_secondary_cost_dict[year] = new_cost
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated eu_secondary_cost_dict:", eu_secondary_cost_dict)
    # Return the updated dictionaries/data
    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#high volatility for domestic production and recycling
def scenario_16(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):

    if not param_dict:
        print("One or more dictionaries are empty. Returning original data.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

    # Check if 'commodity' exists in the data and modify it
    if 'DR Primary' in param_dict:
        current_value = float(param_dict['DR Primary'])
        new_value = 0.5 #new DR value
        param_dict['DR Primary'] = new_value
        print("DR updated.")

    # Check if param_dict exists and modify it if needed
    if 'DR Secondary' in param_dict:
        current_value = float(param_dict['DR Secondary'])
        new_value = 0.5  # new DR value
        param_dict['DR Secondary'] = new_value
        print("DR updated.")

    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#low volatility for domestic production and recycling
def scenario_17(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):

    if not param_dict:
        print("One or more dictionaries are empty. Returning original data.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

    # Check if 'commodity' exists in the data and modify it
    if 'DR Primary' in param_dict:
        current_value = float(param_dict['DR Primary'])
        new_value = 0.9 #new DR value
        param_dict['DR Primary'] = new_value
        print("DR updated.")

    # Check if param_dict exists and modify it if needed
    if 'DR Secondary' in param_dict:
        current_value = float(param_dict['DR Secondary'])
        new_value = 0.9  # new DR value
        param_dict['DR Secondary'] = new_value
        print("DR updated.")

    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#diversify import countries
def scenario_18(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not importcost_dict:
        print("Warning: importcost_dict is empty.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    for year, cost in importcost_dict.items():
        try:
            year_int = int(year)
            if year_int >= 2024:
                new_cost = float(cost) + 50000  # Value by how much importcost increase for diversified
                importcost_dict[year] = new_cost
        except ValueError:
            print(f"Warning: Non-numeric year '{year}' found. Skipping.")
    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#slow and steady reduction of CO2 emissions
def scenario_19(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not data:
        print("Warning: data is empty.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

    # Predefined CO2 limit values for years 2024–2050
    co2_limit_slow_steady = [
        482000000, 465000000, 448000000, 431000000, 414000000,
        397000000, 380000000, 363000000, 346000000, 329000000,
        312000000, 295000000, 278000000, 261000000, 244000000,
        227000000, 210000000, 193000000, 176000000, 159000000,
        142000000, 125000000, 108000000, 91000000, 74000000,
        57000000, 40000000
    ]

    if 'global_prop' in data:
        global_prop = data['global_prop']

        # Apply CO2 limits for each year in the range 2024–2050
        for idx, year in enumerate(range(2024, 2051)):
            if year in global_prop.index.levels[0].tolist():
                global_prop.loc[(year, 'CO2 limit'), 'value'] = co2_limit_slow_steady[idx]
            else:
                print(f"Year {year} is not found in global_prop index levels.")
    else:
        print("Warning: 'global_prop' not found in data.")
    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#late and rapid reduction of CO2 emissions
def scenario_20(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not data:
        print("Warning: data is empty.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

    # Predefined CO2 limit values for years 2024–2050
    co2_limit_late_rapid = [
        505000000, 505000000, 505000000, 505000000, 500000000,
        490000000, 475000000, 460000000, 440000000, 415000000,
        390000000, 350000000, 290000000, 220000000, 150000000,
        100000000, 75000000, 60000000, 50000000, 40000000,
        30000000, 25000000, 20000000, 15000000, 10000000,
        5000000, 3000000
    ]

    if 'global_prop' in data:
        global_prop = data['global_prop']

        # Apply CO2 limits for each year in the range 2024–2050
        for idx, year in enumerate(range(2024, 2051)):
            if year in global_prop.index.levels[0].tolist():
                global_prop.loc[(year, 'CO2 limit'), 'value'] = co2_limit_late_rapid[idx]
            else:
                print(f"Year {year} is not found in global_prop index levels.")
    else:
        print("Warning: 'global_prop' not found in data.")
    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#100% decarbonization of energy sector
def scenario_21(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not data:
        print("Warning: data is empty.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    if 'global_prop' in data:
        global_prop = data['global_prop']
        for stf in global_prop.index.levels[0].tolist():
            if stf >=2050:
                global_prop.loc[(stf, 'CO2 limit'), 'value'] = 0
            else:
                print(f"Skipping year {stf} as it's not 2024.")

    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#staying below 1.5 degrees
def scenario_22(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#above 2 degrees
def scenario_23(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#abort all climate change measures since USA left Paris Climate Agreement
def scenario_24(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):

    if not data:
        print("Warning: data is empty.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    if 'commodity' in data:
        co = data['commodity']
        for stf in data['global_prop'].index.levels[0].tolist():
            co.loc[(stf, 'EU27', 'CO2', 'Env'), 'price'] = 0 #set co2 price to 0
    if 'global_prop' in data:
        global_prop = data['global_prop']
        for stf in global_prop.index.levels[0].tolist():
            global_prop.loc[(stf, 'CO2 limit'), 'value'] = 999999999999999999999999999999
            global_prop.loc[(stf, 'CO2 budget'), 'value'] = 999999999999999999999999999999
    if 'process' in data:
        pro = data['process']
        for stf in data['global_prop'].index.levels[0].tolist():
            pro.loc[(stf, 'EU27', 'Coal Plant'), 'cap-up'] = 9999999#Value for cap up
            pro.loc[(stf, 'EU27', 'Coal Lignite'), 'cap-up'] = 9999999#Value for cap up
            pro.loc[(stf, 'EU27', 'Gas Plant (CCGT)'), 'cap-up'] =9999999 #Value for cap up

    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#high electricity demand due to increasing electrification
def scenario_25(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not data:
        print("Warning: param_dict is empty.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    elif 'demand' in data:
        de = data['demand']
        print(de.index)
        print(de.columns)
        for stf in de.index.levels[0].tolist():  # Iterate over support_timeframe
            for t in de.index.levels[1].tolist():  # Iterate over 't'
                # Try to print the value before modifying it
                print(f"Before modification - Year {stf}, t={t}: {de.loc[(stf, t), ('EU27', 'Elec')]}")
                # Increase the demand by 10% for the specific year and t
                de.loc[(stf, t), ('EU27', 'Elec')] *= 1.1
                # Print the updated value
                print(f"After modification - Year {stf}, t={t}: {de.loc[(stf, t), ('EU27', 'Elec')]}")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    else:
        print("Warning: 'demand' not found in data.")

########################################################################################################################

#technofriendly
def scenario_26(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not data or not importcost_dict or not eu_primary_cost_dict or not eu_secondary_cost_dict:
        print("Warning: importcost_dict is empty.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    if importcost_dict:
        for year, cost in importcost_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2024:
                    new_cost = float(cost) * 0.9  # Factor by how much
                    importcost_dict[year] = new_cost
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated importcost_dict:", importcost_dict)
        # Modify the eu_primary_cost_dict if applicable
    if eu_primary_cost_dict:
        for year, cost in eu_primary_cost_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2024:
                    new_cost = float(cost) * 0.9
                    eu_primary_cost_dict[year] = new_cost
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated eu_primary_cost_dict:", eu_primary_cost_dict)
        # modify eu secondary cost
    if eu_secondary_cost_dict:
        for year, cost in eu_secondary_cost_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2024:
                    new_cost = float(cost) * 0.9
                    eu_secondary_cost_dict[year] = new_cost
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated eu_secondary_cost_dict:", eu_secondary_cost_dict)
    if 'processes' in data:
        pro = data['processes']
        processes = ['Wind (onschore)', 'Wind (offshore)','Hydro (run-of-river)','hydro (reservoir)','Coal Plant','Coal Lignite','Gas Plant (CCGT)','Nuclear Plant','Biomass Plant']
        for stf in data['global_prop'].index.levels[0].tolist():
            for carrier in processes:
                co.loc[(stf, 'EU27', carrier, 'Env'), 'inv-cost'] *= 0.9
                co.loc[(stf, 'EU27', carrier, 'Env'), 'fix-cost'] *= 0.9
                co.loc[(stf, 'EU27', carrier, 'Env'), 'var-cost'] *= 0.9

    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict

########################################################################################################################

#global economical crisis
def scenario_27(data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict):
    if not data or not importcost_dict or not eu_primary_cost_dict or not eu_secondary_cost_dict:
        print("Warning: importcost_dict is empty.")
        return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict
    if importcost_dict:
        for year, cost in importcost_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2024:
                    new_cost = float(cost) * 1.5  # Factor by how much
                    importcost_dict[year] = new_cost
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated importcost_dict:", importcost_dict)
        # Modify the eu_primary_cost_dict if applicable
    if eu_primary_cost_dict:
        for year, cost in eu_primary_cost_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2024:
                    new_cost = float(cost) * 1.5
                    eu_primary_cost_dict[year] = new_cost
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated eu_primary_cost_dict:", eu_primary_cost_dict)
        # modify eu secondary cost
    if eu_secondary_cost_dict:
        for year, cost in eu_secondary_cost_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2024:
                    new_cost = float(cost) * 1.5
                    eu_secondary_cost_dict[year] = new_cost
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated eu_secondary_cost_dict:", eu_secondary_cost_dict)
    if 'processes' in data:
        pro = data['processes']
        processes = ['Wind (onschore)', 'Wind (offshore)','Hydro (run-of-river)','hydro (reservoir)','Coal Plant','Coal Lignite','Gas Plant (CCGT)','Nuclear Plant','Biomass Plant']
        for stf in data['global_prop'].index.levels[0].tolist():
            for carrier in processes:
                pro.loc[(stf, 'EU27', carrier, 'Env'), 'inv-cost'] *= 1.5
                pro.loc[(stf, 'EU27', carrier, 'Env'), 'fix-cost'] *= 1.5
                pro.loc[(stf, 'EU27', carrier, 'Env'), 'var-cost'] *= 1.5

    return data,param_dict,importcost_dict, instalable_capacity_dict, eu_primary_cost_dict, eu_secondary_cost_dict,dcr_dict








