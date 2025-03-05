import os
import pyomo.environ
from pyomo.opt.base import SolverFactory
from datetime import datetime, date
from .model import create_model
from .report import *
from .plot import *
from .input import *
from .validation import *
from .saveload import *


def prepare_result_directory(result_name):
    """ create a time stamped directory within the result folder.

    Args:
        result_name: user specified result name

    Returns:
        a subfolder in the result folder 
    
    """
    # timestamp for result directory
    now = datetime.now().strftime('%Y%m%dT%H%M')

    # create result directory if not existent
    result_dir = os.path.join('result', '{}-{}'.format(result_name, now))
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    return result_dir


def setup_solver(optim, logfile='solver.log'):
    """ """
    if optim.name == 'gurobi':
        # reference with list of option names
        # http://www.gurobi.com/documentation/5.6/reference-manual/parameters
        optim.set_options("logfile={}".format(logfile))
        # optim.set_options("timelimit=7200")  # seconds
        # optim.set_options("mipgap=5e-4")  # default = 1e-4
    elif optim.name == 'glpk':
        # reference with list of options
        # execute 'glpsol --help'
        optim.set_options("log={}".format(logfile))
        # optim.set_options("tmlim=7200")  # seconds
        # optim.set_options("mipgap=.0005")
    elif optim.name == 'cplex':
        optim.set_options("log={}".format(logfile))
    else:
        print("Warning from setup_solver: no options set for solver "
              "'{}'!".format(optim.name))
    return optim


def run_scenario(input_files, Solver, timesteps, scenario, result_dir, dt,
                 objective, plot_tuples=None,  plot_sites_name=None,
                 plot_periods=None, report_tuples=None,
                 report_sites_name=None):
    """ run an urbs model for given input, time steps and scenario

    Args:
        - input_files: filenames of input Excel spreadsheets
        - Solver: the user specified solver
        - timesteps: a list of timesteps, e.g. range(0,8761)
        - scenario: a scenario function that modifies the input data dict
        - result_dir: directory name for result spreadsheet and plots
        - dt: length of each time step (unit: hours)
        - objective: objective function chosen (either "cost" or "CO2")
        - plot_tuples: (optional) list of plot tuples (c.f. urbs.result_figures)
        - plot_sites_name: (optional) dict of names for sites in plot_tuples
        - plot_periods: (optional) dict of plot periods
          (c.f. urbs.result_figures)
        - report_tuples: (optional) list of (sit, com) tuples
          (c.f. urbs.report)
        - report_sites_name: (optional) dict of names for sites in
          report_tuples

    Returns:
        the urbs model instance
    """

    # sets a modeled year for non-intertemporal problems
    # (necessary for consitency)
    year = date.today().year

    # scenario name, read and modify data for scenario
    sce = scenario.__name__
    data = read_input(input_files, year)


    ### --------start of urbs-solar input data addition-------- ###


    location = 'Params.xlsx'
    def clean_and_convert(df):
        """Clean and convert the Value column to float."""
        df['Value'] = df['Value'].apply(lambda x: str(x).replace(" ", "").replace(",", ".")).astype(float)
        return df

    dataframe_params = pd.read_excel(location, sheet_name='Params')
    dataframe_params['Param'] = dataframe_params['Param'].str.strip()
    param_dict = dict(zip(dataframe_params['Param'], dataframe_params['Value']))


    data_sheets = {
        'importcost': 'importcost_dict',
        'instalable_capacity': 'instalable_capacity_dict',
        'eu_primary_cost': 'eu_primary_cost_dict',
        'eu_secondary_cost': 'eu_secondary_cost_dict',
        'dcr': 'dcr_dict',
        'stocklvl': 'stocklvl_dict'

    }


    data_dicts = {}
    for sheet, var_name in data_sheets.items():
        df = clean_and_convert(pd.read_excel(location, sheet_name=sheet))
        data_dicts[var_name] = dict(zip(df['Stf'], df['Value'])) if 'Stf' in df else dict(zip(df['Param'], df['Value']))
    importcost_dict = data_dicts['importcost_dict']
    instalable_capacity_dict = data_dicts['instalable_capacity_dict']
    eu_primary_cost_dict = data_dicts['eu_primary_cost_dict']
    eu_secondary_cost_dict = data_dicts['eu_secondary_cost_dict']
    dcr_dict = data_dicts['dcr_dict']
    stocklvl_dict = data_dicts['stocklvl_dict']



    ### --------end of urbs-solar input data addition-------- ###

    ### --------start of urbs-extensionv1.0 input data addition-------- ###

    def process_cost_sheet(cost_sheet):
        """Processes cost data into structured dictionaries indexed by (year, location, process)."""
        importcost_dict = {}  # Dictionary to store import costs
        manufacturingcost_dict = {}  # Dictionary to store manufacturing costs
        remanufacturingcost_dict = {}  # Dictionary to store remanufacturing costs

        # Extract the 'Stf' column (year)
        years = cost_sheet["Stf"].unique()  # Extract the unique years from the 'stf' column

        # Iterate through the columns of the cost sheet (skip the 'stf' column)
        for col in cost_sheet.columns:
            # Skip the 'stf' column since it's already handled
            if col == "Stf":
                continue

            # Split the column name into costtype, location, and process
            parts = col.split("_")
            if len(parts) < 3:
                continue  # Skip columns that don't follow the "costtype_location_process" format

            costtype = parts[0]  # Extract the cost type (e.g., "import")
            location = parts[1]  # Extract the location (e.g., "EU27")
            process = "_".join(parts[2:])  # Extract the process (e.g., "solarPV")

            # Iterate over the rows (years) for each column and map them to (year, location, process)
            for year, value in zip(cost_sheet["Stf"], cost_sheet[col]):
                if year not in years:
                    continue  # Skip invalid years if any

                # Construct a key as (year, location, process)
                key = (year, location, process)

                # Distribute values to respective dictionaries based on cost type
                if costtype == "import":
                    importcost_dict[key] = value
                elif costtype == "manufacturing":
                    manufacturingcost_dict[key] = value
                elif costtype == "remanufacturing":
                    remanufacturingcost_dict[key] = value

        return importcost_dict, manufacturingcost_dict, remanufacturingcost_dict

    def load_data_from_excel(file_path):
        """Loads data from Excel and processes all relevant sheets."""
        # Read all sheets
        base_data = pd.read_excel(file_path, sheet_name="Base")
        cost_sheet = pd.read_excel(file_path, sheet_name="cost_sheet")
        #locations_data = pd.read_excel(file_path, sheet_name="locations")
        #loadfactors_data = pd.read_excel(file_path, sheet_name="loadfactors")
        #technologies_data = pd.read_excel(file_path, sheet_name="Technologies")
        #dcr_data = pd.read_excel(file_path, sheet_name="dcr")
        #stocklvl_data = pd.read_excel(file_path, sheet_name="stocklvl")

        # Extract base parameters from the Base sheet
        base_params = {
            "y0": int(base_data.loc[base_data["Param"] == "Start Year y0", "Value"].values[0]),
            "y_end": int(base_data.loc[base_data["Param"] == "End Year yn", "Value"].values[0]),
            "hours": int(base_data.loc[base_data["Param"] == "hours per year", "Value"].values[0])
        }

        # Process the cost sheet into import, manufacturing, and remanufacturing cost dicts
        importcost_dict, manufacturingcost_dict, remanufacturingcost_dict = process_cost_sheet(cost_sheet)

        # Now we create the 'data_urbsextensionv1' dictionary to return all data
        data_urbsextensionv1 = {
            "base_params": base_params,
            "importcost_dict": importcost_dict,
            "manufacturingcost_dict": manufacturingcost_dict,
            "remanufacturingcost_dict": remanufacturingcost_dict
            #"locations": locations_data,
            #"loadfactors": loadfactors_data,
            #"technologies": technologies_data,
            #"dcr": dcr_data,
            #"stocklvl": stocklvl_data
        }

        return data_urbsextensionv1

    # Load the data from the Excel file
    data_urbsextensionv1 = load_data_from_excel("Input_urbsextensionv1.xlsx")  # Replace with your actual file path

    ### --------end of urbs-extensionv1.0 input data addition-------- ###

    data,data_urbsextensionv1,param_dict, instalable_capacity_dict,dcr_dict,stocklvl_dict = scenario(data,data_urbsextensionv1.copy(),param_dict.copy(),
        instalable_capacity_dict.copy(),
        dcr_dict.copy(),
        stocklvl_dict.copy())
    validate_input(data)
    validate_dc_objective(data, objective)

    # create model
    prob = create_model(data,data_urbsextensionv1, param_dict,  instalable_capacity_dict,dcr_dict,stocklvl_dict, dt, timesteps, objective)

    # prob_filename = os.path.join(result_dir, 'model.lp')
    # prob.write(prob_filename, io_options={'symbolic_solver_labels':True})

    # refresh time stamp string and create filename for logfile
    log_filename = os.path.join(result_dir, '{}.log').format(sce)

    # solve model and read results
    optim = SolverFactory(Solver)  # cplex, glpk, gurobi, ...
    optim = setup_solver(optim, logfile=log_filename)
    result = optim.solve(prob, tee=True)
    assert str(result.solver.termination_condition) == 'optimal'

    # save problem solution (and input data) to HDF5 file
    save(prob, os.path.join(result_dir, '{}.h5'.format(sce)))

    # write report to spreadsheet
    report(
        prob,
        os.path.join(result_dir, '{}.xlsx').format(sce),
        report_tuples=report_tuples,
        report_sites_name=report_sites_name)

    # result plots
    result_figures(
        prob,
        os.path.join(result_dir, '{}'.format(sce)),
        timesteps,
        plot_title_prefix=sce.replace('_', ' '),
        plot_tuples=plot_tuples,
        plot_sites_name=plot_sites_name,
        periods=plot_periods,
        figure_size=(24, 9))

    return prob
