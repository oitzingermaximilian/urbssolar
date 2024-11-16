import math
import pyomo.core as pyomo
from datetime import datetime
from .features import *
from .input import *


def create_model(data, param_dict, importcost_dict, instalable_capacity_dict,
                 eu_primary_cost_dict, eu_secondary_cost_dict, dt=8760,
                 timesteps=None, objective='cost',dual = None):
    """Create a pyomo ConcreteModel urbs object from given input data.

    Args:
        - data: a dict of up to 12
        - dt: timestep duration in hours (default: 1)
        - timesteps: optional list of timesteps, default: demand timeseries
        - objective: Either "cost" or "CO2" for choice of objective function,
          default: "cost"
        - dual: set True to add dual variables to model output
          (marginally slower), default: True

    Returns:
        a pyomo ConcreteModel object
    """

    # Optional
    if not timesteps:
        timesteps = data['demand'].index.tolist()

    m = pyomo_model_prep(data, timesteps)  # preparing pyomo model
    m.name = 'urbs'
    m.created = datetime.now().strftime('%Y%m%dT%H%M')
    m._data = data





    # Parameters

    # weight = length of year (hours) / length of simulation (hours)
    # weight scales costs and emissions from length of simulation to a full
    # year, making comparisons among cost types (invest is annualized, fixed
    # costs are annual by default, variable costs are scaled by weight) and
    # among different simulation durations meaningful.
    m.weight = pyomo.Param(
        within=pyomo.Reals,
        initialize=float(8760) / ((len(m.timesteps) - 1) * dt),
        doc='Pre-factor for variable costs and emissions for an annual result')

    # dt = spacing between timesteps. Required for storage equation that
    # converts between energy (storage content, e_sto_con) and power (all other
    # quantities that start with "e_")
    m.dt = pyomo.Param(
        within=pyomo.Reals,
        initialize=dt,
        doc='Time step duration (in hours), default: 1')


    # import objective function information
    m.obj = pyomo.Param(
        within=pyomo.Any,
        initialize=objective,
        doc='Specification of minimized quantity, default: "cost"')


    # Sets
    # ====
    # Syntax: m.{name} = Set({domain}, initialize={values})
    # where name: set name
    #       domain: set domain for tuple sets, a cartesian set product
    #       values: set values, a list or array of element tuples

    # generate ordered time step sets
    m.t = pyomo.Set(
       within=pyomo.Reals,
       initialize=m.timesteps,
        ordered=True,
        doc='Set of timesteps')
    #m.t = pyomo.Set(initialize=range(0, 2), ordered=True, doc='Set of timesteps')
    # modelled (i.e. excluding init time step for storage) time steps
    m.tm = pyomo.Set(
        within=m.t,
        initialize=m.timesteps[1:],
        ordered=True,
        doc='Set of modelled timesteps')


    # Support timeframes (e.g. 2020, 2030...)
    indexlist = []
    for key in m.commodity_dict["price"]:
        # Convert the first element of the key to an integer
        year = int(key[0])
        if year not in indexlist:
            indexlist.append(year)

    # Create the Pyomo set
    m.stf = pyomo.Set(
        within=pyomo.Integers,  # Changed to Integers
        initialize=indexlist,
        ordered=True,
        doc='Set of modeled support timeframes (e.g. years)'
    )

    # site (e.g. north, middle, south...)
    indexlist = list()
    for key in m.commodity_dict["price"]:
        if key[1] not in indexlist:
            indexlist.append(key[1])
    m.sit = pyomo.Set(
        initialize=indexlist,
        doc='Set of sites')

    # commodity (e.g. solar, wind, coal...)
    indexlist = list()
    for key in m.commodity_dict["price"]:
        if key[2] not in indexlist:
            indexlist.append(key[2])
    m.com = pyomo.Set(
        initialize=indexlist,
        doc='Set of commodities')

    # commodity type (i.e. SupIm, Demand, Stock, Env)
    indexlist = list()
    for key in m.commodity_dict["price"]:
        if key[3] not in indexlist:
            indexlist.append(key[3])
    m.com_type = pyomo.Set(
        initialize=indexlist,
        doc='Set of commodity types')

    # process (e.g. Wind turbine, Gas plant, Photovoltaics...)
    indexlist = list()
    for key in m.process_dict["inv-cost"]:
        if key[2] not in indexlist:
            indexlist.append(key[2])
    m.pro = pyomo.Set(
        initialize=indexlist,
        doc='Set of conversion processes')

    # cost_type
    m.cost_type = pyomo.Set(
        initialize=m.cost_type_list,
        doc='Set of cost types (hard-coded)')


    ########################################
    # New Sets & Params used for urbs-solar#
    ########################################

    m.cost_type_solar = pyomo.Set(
        initialize=m.cost_solar_list,
        doc='Set of cost types (hard-coded)')
    # Input Params urbs-solar
    # basic params
    m.y0 = pyomo.Param(initialize=int(param_dict['Start Year y0']))  # Initial year
    m.y_end = pyomo.Param(initialize=int(param_dict['End Year yn']))  # End year
    m.n = pyomo.Param(initialize=int(param_dict['n turnover stockpile']))
    m.l = pyomo.Param(initialize=int(param_dict['l']))

    # Capacities ( capacity(t=0), stock(t=0), instalable (max/a) )
    m.Installed_Capacity_Q_s = pyomo.Param(initialize=int(param_dict['InitialCapacity']))  # Initial installed capacity MW
    m.Existing_Stock_Q_stock = pyomo.Param(initialize=int(param_dict['Existing Stock in y0']))  # Initial stock in y0
    m.Q_Solar_new = pyomo.Param(m.stf, initialize=instalable_capacity_dict)
    print("Initialized values for Q_Solar_new:")
    for stf in m.stf:
        print(f"Year: {stf}, Q_Solar_new: {m.Q_Solar_new[stf]}")

    # cost params in €/MW
    m.IMPORTCOST = pyomo.Param(m.stf, initialize=importcost_dict)
    m.STORAGECOST = pyomo.Param(initialize=float(param_dict['Storagecost / MW']))
    m.EU_primary_costs = pyomo.Param(m.stf, initialize=eu_primary_cost_dict)
    m.EU_secondary_costs = pyomo.Param(m.stf, initialize=eu_secondary_cost_dict)
    m.logisticcost = pyomo.Param(initialize=float(15)) #to avoid instant storage takeout

    m.FT = pyomo.Param(initialize=float(param_dict['FT']))  # Factor
    m.anti_dumping_index = pyomo.Param(initialize=float(param_dict['anti duping Index']))  # Anti-dumping index
    m.deltaQ_EUprimary = pyomo.Param(initialize=float(param_dict['dQ EU Primary']))  # ΔQ EU Primary
    m.deltaQ_EUsecondary = pyomo.Param(initialize=float(param_dict['dQ EU Secondary']))  # ΔQ EU Secondary
    m.IR_EU_primary = pyomo.Param(initialize=float(param_dict['IR EU Primary']))  # IR EU Primary
    m.IR_EU_secondary = pyomo.Param(initialize=float(param_dict['IR EU Secondary']))  # IR EU Secondary
    m.DCR_solar = pyomo.Param(initialize=float(param_dict['DCR Solar']))  # DCR Solar
    m.DR_primary = pyomo.Param(initialize=float(param_dict['DR Primary']))  # DR Primary
    m.DR_secondary = pyomo.Param(initialize=float(param_dict['DR Secondary']))  # DR Secondary


    # Capacity to Balance with loadfactor and h/a
    m.lf_solar = pyomo.Param(initialize=float(param_dict['lf Solar']))  # lf Solar
    m.hours_year = pyomo.Param(initialize=int(param_dict['hours per year']))  # Hours per year

#######################################End of urbs-solar Params#########################################################

    # tuple sets
    m.sit_tuples = pyomo.Set(
        within=m.stf * m.sit,
        initialize=tuple(m.site_dict["area"].keys()),
        doc='Combinations of support timeframes and sites')
    m.com_tuples = pyomo.Set(
        within=m.stf * m.sit * m.com * m.com_type,
        initialize=tuple(m.commodity_dict["price"].keys()),
        doc='Combinations of defined commodities, e.g. (2018,Mid,Elec,Demand)')
    m.pro_tuples = pyomo.Set(
        within=m.stf * m.sit * m.pro,
        initialize=tuple(m.process_dict["inv-cost"].keys()),
        doc='Combinations of possible processes, e.g. (2018,North,Coal plant)')
    m.com_stock = pyomo.Set(
        within=m.com,
        initialize=commodity_subset(m.com_tuples, 'Stock'),
        doc='Commodities that can be purchased at some site(s)')
    if m.mode['int']:
        # tuples for operational status of technologies
        m.operational_pro_tuples = pyomo.Set(
            within=m.sit * m.pro * m.stf * m.stf,
            initialize=[(sit, pro, stf, stf_later)
                        for (sit, pro, stf, stf_later)
                        in op_pro_tuples(m.pro_tuples, m)],
            doc='Processes that are still operational through stf_later'
                '(and the relevant years following), if built in stf'
                'in stf.')

        # tuples for rest lifetime of installed capacities of technologies
        m.inst_pro_tuples = pyomo.Set(
            within=m.sit * m.pro * m.stf,
            initialize=[(sit, pro, stf)
                        for (sit, pro, stf)
                        in inst_pro_tuples(m)],
            doc='Installed processes that are still operational through stf')

    # commodity type subsets
    m.com_supim = pyomo.Set(
        within=m.com,
        initialize=commodity_subset(m.com_tuples, 'SupIm'),
        doc='Commodities that have intermittent (timeseries) input')
    m.com_demand = pyomo.Set(
        within=m.com,
        initialize=commodity_subset(m.com_tuples, 'Demand'),
        doc='Commodities that have a demand (implies timeseries)')
    m.com_env = pyomo.Set(
        within=m.com,
        initialize=commodity_subset(m.com_tuples, 'Env'),
        doc='Commodities that (might) have a maximum creation limit')

    # process tuples for area rule
    m.pro_area_tuples = pyomo.Set(
        within=m.stf * m.sit * m.pro,
        initialize=tuple(m.proc_area_dict.keys()),
        doc='Processes and Sites with area Restriction')

    # process input/output
    m.pro_input_tuples = pyomo.Set(
        within=m.stf * m.sit * m.pro * m.com,
        initialize=[(stf, site, process, commodity)
                    for (stf, site, process) in m.pro_tuples
                    for (s, pro, commodity) in tuple(m.r_in_dict.keys())
                    if process == pro and s == stf],
        doc='Commodities consumed by process by site,'
            'e.g. (2020,Mid,PV,Solar)')
    m.pro_output_tuples = pyomo.Set(
        within=m.stf * m.sit * m.pro * m.com,
        initialize=[(stf, site, process, commodity)
                    for (stf, site, process) in m.pro_tuples
                    for (s, pro, commodity) in tuple(m.r_out_dict.keys())
                    if process == pro and s == stf],
        doc='Commodities produced by process by site, e.g. (2020,Mid,PV,Elec)')

    # process tuples for maximum gradient feature
    m.pro_maxgrad_tuples = pyomo.Set(
        within=m.stf * m.sit * m.pro,
        initialize=[(stf, sit, pro)
                    for (stf, sit, pro) in m.pro_tuples
                    if m.process_dict['max-grad'][stf, sit, pro] < 1.0 / dt],
        doc='Processes with maximum gradient smaller than timestep length')

    # process tuples for partial feature
    m.pro_partial_tuples = pyomo.Set(
        within=m.stf * m.sit * m.pro,
        initialize=[(stf, site, process)
                    for (stf, site, process) in m.pro_tuples
                    for (s, pro, _) in tuple(m.r_in_min_fraction_dict.keys())
                    if process == pro and s == stf],
        doc='Processes with partial input')

    m.pro_partial_input_tuples = pyomo.Set(
        within=m.stf * m.sit * m.pro * m.com,
        initialize=[(stf, site, process, commodity)
                    for (stf, site, process) in m.pro_partial_tuples
                    for (s, pro, commodity) in tuple(m.r_in_min_fraction_dict
                                                     .keys())
                    if process == pro and s == stf],
        doc='Commodities with partial input ratio,'
            'e.g. (2020,Mid,Coal PP,Coal)')

    m.pro_partial_output_tuples = pyomo.Set(
        within=m.stf * m.sit * m.pro * m.com,
        initialize=[(stf, site, process, commodity)
                    for (stf, site, process) in m.pro_partial_tuples
                    for (s, pro, commodity) in tuple(m.r_out_min_fraction_dict
                                                     .keys())
                    if process == pro and s == stf],
        doc='Commodities with partial input ratio, e.g. (Mid,Coal PP,CO2)')

    # Variables

    # costs
    m.costs = pyomo.Var(
        m.cost_type,
        within=pyomo.Reals,
        doc='Costs by type (EUR/a)')

    m.process_costs = pyomo.Var(
        m.pro_tuples,
        m.cost_type,
        within=pyomo.Reals,
        doc='Costs by type and site (EUR/a)')
    # commodity
    m.e_co_stock = pyomo.Var(
        m.tm, m.com_tuples,
        within=pyomo.NonNegativeReals,
        doc='Use of stock commodity source (MW) per timestep')

    # process
    m.cap_pro_new = pyomo.Var(
        m.pro_tuples,
        within=pyomo.NonNegativeReals,
        doc='New process capacity (MW)')

    # process capacity as expression object
    # (variable if expansion is possible, else static)
    m.cap_pro = pyomo.Expression(
        m.pro_tuples,
        rule=def_process_capacity_rule,
        doc='Total process capacity (MW)')

    m.tau_pro = pyomo.Var(
        m.t, m.pro_tuples,
        within=pyomo.NonNegativeReals,
        doc='Power flow (MW) through process')
    m.e_pro_in = pyomo.Var(
        m.tm, m.pro_input_tuples,
        within=pyomo.NonNegativeReals,
        doc='Power flow of commodity into process (MW) per timestep')
    m.e_pro_out = pyomo.Var(
        m.tm, m.pro_output_tuples,
        within=pyomo.NonNegativeReals,
        doc='Power flow out of process (MW) per timestep')


    ################################
    # Variables used for urbs_solar#
    ################################

    # capacity variables (MW)
    m.capacity_solar = pyomo.Var(m.stf, domain=pyomo.NonNegativeReals)
    m.capacity_solar_new = pyomo.Var(m.stf, domain=pyomo.NonNegativeReals)
    m.capacity_solar_imported = pyomo.Var(m.stf, domain=pyomo.NonNegativeReals)
    m.capacity_solar_stockout = pyomo.Var(m.stf, domain=pyomo.NonNegativeReals)
    m.capacity_solar_euprimary = pyomo.Var(m.stf, domain=pyomo.NonNegativeReals)
    m.capacity_solar_eusecondary = pyomo.Var(m.stf, domain=pyomo.NonNegativeReals)
    m.capacity_solar_stock = pyomo.Var(m.stf, domain=pyomo.NonNegativeReals)
    m.capacity_solar_stock_imported = pyomo.Var(m.stf, domain=pyomo.NonNegativeReals)


    m.sum_outofstock = pyomo.Var(m.stf, domain=pyomo.NonNegativeReals)
    m.sum_stock = pyomo.Var(m.stf, domain=pyomo.NonNegativeReals)
    m.anti_dumping_measures = pyomo.Var(m.stf, domain=pyomo.NonNegativeReals)

    # balance Variables (MWh) : only used for results & res_vertex_rule
    m.balance_solar = pyomo.Var(m.stf, within=pyomo.NonNegativeReals) # --> res_vertex_rule
    m.balance_import = pyomo.Var(m.stf, within=pyomo.NonNegativeReals)
    m.balance_outofstock = pyomo.Var(m.stf, within=pyomo.NonNegativeReals)
    m.balance_EU_primary = pyomo.Var(m.stf, within=pyomo.NonNegativeReals)
    m.balance_EU_secondary = pyomo.Var(m.stf, within=pyomo.NonNegativeReals)

    # cost Variables (€/MW): main objective Function --> minimize cost
    m.costs_solar = pyomo.Var(m.cost_type_solar, domain=pyomo.NonNegativeReals)
    m.costs_solar_import = pyomo.Var(m.stf, within=pyomo.NonNegativeReals)
    m.costs_solar_storage =pyomo.Var(m.stf, within=pyomo.NonNegativeReals)
    m.costs_EU_primary =pyomo.Var(m.stf, within=pyomo.NonNegativeReals)
    m.costs_EU_secondary =pyomo.Var(m.stf, within=pyomo.NonNegativeReals)


    if m.mode['tra']:
        if m.mode['dpf']:
            m = add_transmission_dc(m)
        else:
            m = add_transmission(m)
    if m.mode['sto']:
        m = add_storage(m)
    if m.mode['dsm']:
        m = add_dsm(m)
    if m.mode['bsp']:
        m = add_buy_sell_price(m)
    if m.mode['tve']:
        m = add_time_variable_efficiency(m)
    else:
        m.pro_timevar_output_tuples = pyomo.Set(
            within=m.stf * m.sit * m.pro * m.com,
            doc='empty set needed for (partial) process output')

    # Equation declarations
    # equation bodies are defined in separate functions, referred to here by
    # their name in the "rule" keyword.


    ##################################
    # Constraints used for urbs_solar#
    ##################################



    m.capacity_solar_growth_constraint = pyomo.Constraint(m.stf, rule=capacity_solar_growth_rule)
    m.initial_capacity_constraint = pyomo.Constraint(m.stf, rule=initial_capacity_rule)
    m.capacity_solar_new_constraint = pyomo.Constraint(m.stf, rule=capacity_solar_new_rule)
    m.capacity_solar_stock_constraint = pyomo.Constraint(m.stf, rule=capacity_solar_stock_rule)
    m.capacity_solar_stock_initial_constraint = pyomo.Constraint(m.stf, rule=capacity_solar_stock_initial_rule)
    m.stock_turnover_constraint = pyomo.Constraint(m.stf, rule=stock_turnover_rule)
    m.anti_dumping_measures_constraint = pyomo.Constraint(m.stf, rule=anti_dumping_measures_rule)
    m.capacity_solar_new_limit_constraint = pyomo.Constraint(m.stf, rule=capacity_solar_new_limit_rule)
    m.timedelay_EU_primary_production_constraint = pyomo.Constraint(m.stf, rule=timedelay_EU_primary_production_rule)
    m.timedelay_EU_secondary_production_constraint = pyomo.Constraint(m.stf, rule=timedelay_EU_secondary_production_rule)
    m.constraint_EU_secondary1_to_total_constraint = pyomo.Constraint(m.stf,rule=constraint1_EU_secondary_to_total_rule)
    m.constraint_EU_secondary2_to_total_constraint = pyomo.Constraint(m.stf,rule=constraint2_EU_secondary_to_total_rule)
    m.constraint_EU_primary_to_total_constraint = pyomo.Constraint(m.stf, rule=constraint_EU_primary_to_total_rule)
    m.constraint_EU_secondary_to_secondary_constraint = pyomo.Constraint(m.stf,rule=constraint_EU_secondary_to_secondary_rule)
    m.cost_constraint_solar = pyomo.Constraint(m.cost_type_solar, rule=def_costs_solar)
    m.balance_import_constraint = pyomo.Constraint(m.stf, rule=convert_capacity_1_rule)
    m.balance_balance_outofstock_constraint = pyomo.Constraint(m.stf, rule=convert_capacity_2_rule)
    m.balance_EU_primary_constraint = pyomo.Constraint(m.stf, rule=convert_capacity_3_rule)
    m.balance_EU_secondary_constraint = pyomo.Constraint(m.stf, rule=convert_capacity_4_rule)
    m.yearly_storagecost_constraint = pyomo.Constraint(m.stf, rule=calculate_yearly_storagecost)
    m.yearly_importcost_constraint = pyomo.Constraint(m.stf, rule=calculate_yearly_importcost)
    m.EUprimary_cost_yearly_constraint =pyomo.Constraint(m.stf, rule=calculate_yearly_EU_primary)
    m.EUsecondary_cost_yearly_constraint = pyomo.Constraint(m.stf, rule=calculate_yearly_EU_secondary)
    m.balance_solar_constraint = pyomo.Constraint(m.stf, rule=convert_totalcapacity_to_balance)

    # commodity constraints default
    m.res_vertex = pyomo.Constraint(
        m.tm, m.com_tuples,
        rule=res_vertex_rule,
        doc='storage + transmission + process + source + buy - sell == demand')
    m.res_stock_step = pyomo.Constraint(
        m.tm, m.com_tuples,
        rule=res_stock_step_rule,
        doc='stock commodity input per step <= commodity.maxperstep')
    m.res_stock_total = pyomo.Constraint(
        m.com_tuples,
        rule=res_stock_total_rule,
        doc='total stock commodity input <= commodity.max')
    m.res_env_step = pyomo.Constraint(
        m.tm, m.com_tuples,
        rule=res_env_step_rule,
        doc='environmental output per step <= commodity.maxperstep')
    m.res_env_total = pyomo.Constraint(
        m.com_tuples,
        rule=res_env_total_rule,
        doc='total environmental commodity output <= commodity.max')

    # process
    m.def_process_input = pyomo.Constraint(
        m.tm, m.pro_input_tuples - m.pro_partial_input_tuples,
        rule=def_process_input_rule,
        doc='process input = process throughput * input ratio')
    m.def_process_output = pyomo.Constraint(
        m.tm, (m.pro_output_tuples - m.pro_partial_output_tuples -
               m.pro_timevar_output_tuples),
        rule=def_process_output_rule,
        doc='process output = process throughput * output ratio')
    m.def_intermittent_supply = pyomo.Constraint(
        m.tm, m.pro_input_tuples,
        rule=def_intermittent_supply_rule,
        doc='process output = process capacity * supim timeseries')
    m.res_process_throughput_by_capacity = pyomo.Constraint(
        m.tm, m.pro_tuples,
        rule=res_process_throughput_by_capacity_rule,
        doc='process throughput <= total process capacity')
    m.res_process_maxgrad_lower = pyomo.Constraint(
        m.tm, m.pro_maxgrad_tuples,
        rule=res_process_maxgrad_lower_rule,
        doc='throughput may not decrease faster than maximal gradient')
    m.res_process_maxgrad_upper = pyomo.Constraint(
        m.tm, m.pro_maxgrad_tuples,
        rule=res_process_maxgrad_upper_rule,
        doc='throughput may not increase faster than maximal gradient')
    m.res_process_capacity = pyomo.Constraint(
        m.pro_tuples,
        rule=res_process_capacity_rule,
        doc='process.cap-lo <= total process capacity <= process.cap-up')

    m.res_area = pyomo.Constraint(
        m.sit_tuples,
        rule=res_area_rule,
        doc='used process area <= total process area')

    m.res_throughput_by_capacity_min = pyomo.Constraint(
        m.tm, m.pro_partial_tuples,
        rule=res_throughput_by_capacity_min_rule,
        doc='cap_pro * min-fraction <= tau_pro')
    m.def_partial_process_input = pyomo.Constraint(
        m.tm, m.pro_partial_input_tuples,
        rule=def_partial_process_input_rule,
        doc='e_pro_in = '
            ' cap_pro * min_fraction * (r - R) / (1 - min_fraction)'
            ' + tau_pro * (R - min_fraction * r) / (1 - min_fraction)')
    m.def_partial_process_output = pyomo.Constraint(
        m.tm,
        (m.pro_partial_output_tuples -
         (m.pro_partial_output_tuples & m.pro_timevar_output_tuples)),
        rule=def_partial_process_output_rule,
        doc='e_pro_out = '
            ' cap_pro * min_fraction * (r - R) / (1 - min_fraction)'
            ' + tau_pro * (R - min_fraction * r) / (1 - min_fraction)')

    # if m.mode['int']:
    #    m.res_global_co2_limit = pyomo.Constraint(
    #        m.stf
    #        ,
    #        rule=res_global_co2_limit_rule,
    #        doc='total co2 commodity output <= global.prop CO2 limit')

    # costs
    m.def_costs = pyomo.Constraint(
        m.cost_type,
        rule=def_costs_rule,
        doc='main cost function by cost type')

    # specific cost calculation allows to identify individual contributors to the cost function.
    m.def_specific_process_costs = pyomo.Constraint(
        m.pro_tuples,
        m.cost_type,
        rule=def_specific_process_costs_rule,
        doc='main cost function of processes by cost type by process and stf')

    # objective and global constraints
    if m.obj.value == 'cost':
        m.res_global_co2_limit = pyomo.Constraint(
            m.stf,
            rule=res_global_co2_limit_rule,
            doc='total co2 commodity output <= Global CO2 limit')

        if m.mode['int']:
            m.res_global_co2_budget = pyomo.Constraint(
                rule=res_global_co2_budget_rule,
                doc='total co2 commodity output <= global.prop CO2 budget')

            m.res_global_cost_limit = pyomo.Constraint(
                m.stf,
                rule=res_global_cost_limit_rule,
                doc='total costs <= Global cost limit')

        m.objective_function = pyomo.Objective(
            rule=cost_rule,
            sense=pyomo.minimize,
            doc='minimize(cost = sum of all cost types)')

    elif m.obj.value == 'CO2':

        m.res_global_cost_limit = pyomo.Constraint(
            m.stf,
            rule=res_global_cost_limit_rule,
            doc='total costs <= Global cost limit')

        if m.mode['int']:
            m.res_global_cost_budget = pyomo.Constraint(
                rule=res_global_cost_budget_rule,
                doc='total costs <= global.prop Cost budget')
            m.res_global_co2_limit = pyomo.Constraint(
                m.stf,
                rule=res_global_co2_limit_rule,
                doc='total co2 commodity output <= Global CO2 limit')

        m.objective_function = pyomo.Objective(
            rule=co2_rule,
            sense=pyomo.minimize,
            doc='minimize total CO2 emissions')

    else:
        raise NotImplementedError("Non-implemented objective quantity. Set "
                                  "either 'cost' or 'CO2' as the objective in "
                                  "runme.py!")

    if dual:
        m.dual = pyomo.Suffix(direction=pyomo.Suffix.IMPORT)

    return m


# commodity

# vertex equation: calculate balance for given commodity and site;
# contains implicit constraints for process activity, import/export and
# storage activity (calculated by function commodity_balance);
# contains implicit constraint for stock commodity source term
def res_vertex_rule(m,tm, stf, sit, com, com_type):
    # environmental or supim commodities don't have this constraint (yet)
    if com in m.com_env:
        return pyomo.Constraint.Skip
    if com in m.com_supim:
        return pyomo.Constraint.Skip

    # helper function commodity_balance calculates balance from input to
    # and output from processes, storage and transmission.
    # if power_surplus > 0: production/storage/imports create net positive
    #                       amount of commodity com
    # if power_surplus < 0: production/storage/exports consume a net
    #                       amount of the commodity com
    power_surplus = - commodity_balance(m,tm, stf, sit, com)


    # Add solar capacity contribution to power surplus
    if com == "Elec":
        power_surplus += m.balance_solar[stf]  # Adding total solar capacity in MWh

        print(power_surplus)
    # if com is a stock commodity, the commodity source term e_co_stock
    # can supply a possibly negative power_surplus
    if com in m.com_stock:
        power_surplus += m.e_co_stock[tm, stf, sit, com, com_type]

    # if Buy and sell prices are enabled
    if m.mode['bsp']:
        power_surplus += bsp_surplus(m, tm, stf, sit, com, com_type)

    # if com is a demand commodity, the power_surplus is reduced by the
    # demand value; no scaling by m.dt or m.weight is needed here, as this
    # constraint is about power (MW), not energy (MWh)
    if com in m.com_demand:
        try:
            # Get the demand value
            demand_value = m.demand_dict[(sit, com)][(stf, tm)]

            # Subtract demand from power surplus
            power_surplus -= demand_value
            print(power_surplus)
        except KeyError:
            pass

    if m.mode['dsm']:
        power_surplus += dsm_surplus(m, tm, stf, sit, com)

    return power_surplus == 0


# stock commodity purchase == commodity consumption, according to
# commodity_balance of current (time step, site, commodity);
# limit stock commodity use per time step


def res_stock_step_rule(m, tm, stf, sit, com, com_type):
    if com not in m.com_stock:
        return pyomo.Constraint.Skip
    else:
        return (m.e_co_stock[tm, stf, sit, com, com_type] <=
                m.dt * m.commodity_dict['maxperhour']
                [(stf, sit, com, com_type)])


# limit stock commodity use in total (scaled to annual consumption, thanks
# to m.weight)
def res_stock_total_rule(m, stf, sit, com, com_type):
    if com not in m.com_stock:
        return pyomo.Constraint.Skip
    else:
        # calculate total consumption of commodity com
        total_consumption = 0
        for tm in m.tm:
            total_consumption += (
                m.e_co_stock[tm, stf, sit, com, com_type])
        total_consumption *= m.weight
        return (total_consumption <=
                m.commodity_dict['max'][(stf, sit, com, com_type)])


# environmental commodity creation == - commodity_balance of that commodity
# used for modelling emissions (e.g. CO2) or other end-of-pipe results of
# any process activity;
# limit environmental commodity output per time step
def res_env_step_rule(m, tm, stf, sit, com, com_type):
    if com not in m.com_env:
        return pyomo.Constraint.Skip
    else:
        environmental_output = - commodity_balance(m, tm, stf, sit, com)
        return (environmental_output <=
                m.dt * m.commodity_dict['maxperhour']
                [(stf, sit, com, com_type)])


# limit environmental commodity output in total (scaled to annual
# emissions, thanks to m.weight)
def res_env_total_rule(m, stf, sit, com, com_type):
    if com not in m.com_env:
        return pyomo.Constraint.Skip
    else:
        # calculate total creation of environmental commodity com
        env_output_sum = 0
        for tm in m.tm:
            env_output_sum += (- commodity_balance(m, tm, stf, sit, com))
        env_output_sum *= m.weight
        return (env_output_sum <=
                m.commodity_dict['max'][(stf, sit, com, com_type)])


# process

# process capacity (for m.cap_pro Expression)
def def_process_capacity_rule(m, stf, sit, pro):
    if m.mode['int']:
        if (sit, pro, stf) in m.inst_pro_tuples:
            if (sit, pro, min(m.stf)) in m.pro_const_cap_dict:
                cap_pro = m.process_dict['inst-cap'][(stf, sit, pro)]
            else:
                cap_pro = \
                    (sum(m.cap_pro_new[stf_built, sit, pro]
                         for stf_built in m.stf
                         if (sit, pro, stf_built, stf)
                         in m.operational_pro_tuples) +
                     m.process_dict['inst-cap'][(min(m.stf), sit, pro)])
        else:
            cap_pro = sum(
                m.cap_pro_new[stf_built, sit, pro]
                for stf_built in m.stf
                if (sit, pro, stf_built, stf) in m.operational_pro_tuples)
    else:
        if (sit, pro, stf) in m.pro_const_cap_dict:
            cap_pro = m.process_dict['inst-cap'][(stf, sit, pro)]
        else:
            cap_pro = (m.cap_pro_new[stf, sit, pro] +
                       m.process_dict['inst-cap'][(stf, sit, pro)])
    return cap_pro


# process input power == process throughput * input ratio


def def_process_input_rule(m, tm, stf, sit, pro, com):
    return (m.e_pro_in[tm, stf, sit, pro, com] ==
            m.tau_pro[tm, stf, sit, pro] * m.r_in_dict[(stf, pro, com)])


# process output power = process throughput * output ratio
def def_process_output_rule(m, tm, stf, sit, pro, com):
    ergebnis = m.tau_pro[tm, stf, sit, pro] * m.r_out_dict[(stf, pro, com)]
    print(ergebnis)
    return m.e_pro_out[tm, stf, sit, pro, com] == ergebnis



# process input (for supim commodity) = process capacity * timeseries
def def_intermittent_supply_rule(m, tm, stf, sit, pro, coin):
    if coin in m.com_supim:
        return (m.e_pro_in[tm, stf, sit, pro, coin] ==
                m.cap_pro[stf, sit, pro] * m.supim_dict[(sit, coin)]
                [(stf, tm)] * m.dt)
    else:
        return pyomo.Constraint.Skip


# process throughput <= process capacity
def res_process_throughput_by_capacity_rule(m, tm, stf, sit, pro):
    result = m.dt * m.cap_pro[stf, sit, pro]
    print(result)
    return (m.tau_pro[tm, stf, sit, pro] <= result)


def res_process_maxgrad_lower_rule(m, t, stf, sit, pro):
    return (m.tau_pro[t - 1, stf, sit, pro] -
            m.cap_pro[stf, sit, pro] *
            m.process_dict['max-grad'][(stf, sit, pro)] * m.dt <=
            m.tau_pro[t, stf, sit, pro])


def res_process_maxgrad_upper_rule(m, t, stf, sit, pro):
    return (m.tau_pro[t - 1, stf, sit, pro] +
            m.cap_pro[stf, sit, pro] *
            m.process_dict['max-grad'][(stf, sit, pro)] * m.dt >=
            m.tau_pro[t, stf, sit, pro])


def res_throughput_by_capacity_min_rule(m, tm, stf, sit, pro):
    return (m.tau_pro[tm, stf, sit, pro] >=
            m.cap_pro[stf, sit, pro] *
            m.process_dict['min-fraction'][(stf, sit, pro)] * m.dt)


def def_partial_process_input_rule(m, tm, stf, sit, pro, coin):
    # input ratio at maximum operation point
    R = m.r_in_dict[(stf, pro, coin)]
    # input ratio at lowest operation point
    r = m.r_in_min_fraction_dict[stf, pro, coin]
    min_fraction = m.process_dict['min-fraction'][(stf, sit, pro)]

    online_factor = min_fraction * (r - R) / (1 - min_fraction)
    throughput_factor = (R - min_fraction * r) / (1 - min_fraction)

    return (m.e_pro_in[tm, stf, sit, pro, coin] ==
            m.dt * m.cap_pro[stf, sit, pro] * online_factor +
            m.tau_pro[tm, stf, sit, pro] * throughput_factor)


def def_partial_process_output_rule(m, tm, stf, sit, pro, coo):
    # input ratio at maximum operation point
    R = m.r_out_dict[stf, pro, coo]
    # input ratio at lowest operation point
    r = m.r_out_min_fraction_dict[stf, pro, coo]
    min_fraction = m.process_dict['min-fraction'][(stf, sit, pro)]

    online_factor = min_fraction * (r - R) / (1 - min_fraction)
    throughput_factor = (R - min_fraction * r) / (1 - min_fraction)

    return (m.e_pro_out[tm, stf, sit, pro, coo] ==
            m.dt * m.cap_pro[stf, sit, pro] * online_factor +
            m.tau_pro[tm, stf, sit, pro] * throughput_factor)


# lower bound <= process capacity <= upper bound
def res_process_capacity_rule(m, stf, sit, pro):
    return (m.process_dict['cap-lo'][stf, sit, pro],
            m.cap_pro[stf, sit, pro],
            m.process_dict['cap-up'][stf, sit, pro])


# used process area <= maximal process area
def res_area_rule(m, stf, sit):
    if m.site_dict['area'][stf, sit] >= 0 and sum(
            m.process_dict['area-per-cap'][st, s, p]
            for (st, s, p) in m.pro_area_tuples
            if s == sit and st == stf) > 0:
        total_area = sum(m.cap_pro[st, s, p] *
                         m.process_dict['area-per-cap'][st, s, p]
                         for (st, s, p) in m.pro_area_tuples
                         if s == sit and st == stf)
        return total_area <= m.site_dict['area'][stf, sit]
    else:
        # Skip constraint, if area is not numeric
        return pyomo.Constraint.Skip


# total CO2 output <= Global CO2 limit
def res_global_co2_limit_rule(m, stf):
    if math.isinf(m.global_prop_dict['value'][stf, 'CO2 limit']):
        return pyomo.Constraint.Skip
    elif m.global_prop_dict['value'][stf, 'CO2 limit'] >= 0:
        co2_output_sum = 0
        for tm in m.tm:
            for sit in m.sit:
                # minus because negative commodity_balance represents creation
                # of that commodity.
                co2_output_sum += (- commodity_balance(m, tm,
                                                       stf, sit, 'CO2'))

        # scaling to annual output (cf. definition of m.weight)
        co2_output_sum *= m.weight
        return (co2_output_sum <= m.global_prop_dict['value']
        [stf, 'CO2 limit'])
    else:
        return pyomo.Constraint.Skip


# CO2 output in entire period <= Global CO2 budget
def res_global_co2_budget_rule(m):
    if math.isinf(m.global_prop_dict['value'][min(m.stf_list), 'CO2 budget']):
        return pyomo.Constraint.Skip
    elif (m.global_prop_dict['value'][min(m.stf_list), 'CO2 budget']) >= 0:
        co2_output_sum = 0
        for stf in m.stf:
            for tm in m.tm:
                for sit in m.sit:
                    # minus because negative commodity_balance represents
                    # creation of that commodity.
                    co2_output_sum += (- commodity_balance
                    (m, tm, stf, sit, 'CO2') *
                                       m.weight *
                                       stf_dist(stf, m))

        return (co2_output_sum <=
                m.global_prop_dict['value'][min(m.stf), 'CO2 budget'])
    else:
        return pyomo.Constraint.Skip


# total cost of one year <= Global cost limit
def res_global_cost_limit_rule(m, stf):
    if math.isinf(m.global_prop_dict["value"][stf, "Cost limit"]):
        return pyomo.Constraint.Skip
    elif m.global_prop_dict["value"][stf, "Cost limit"] >= 0:
        return (pyomo.summation(m.costs) <= m.global_prop_dict["value"]
        [stf, "Cost limit"])
    else:
        return pyomo.Constraint.Skip


# total cost in entire period <= Global cost budget
def res_global_cost_budget_rule(m):
    if math.isinf(m.global_prop_dict["value"][min(m.stf), "Cost budget"]):
        return pyomo.Constraint.Skip
    elif m.global_prop_dict["value"][min(m.stf), "Cost budget"] >= 0:
        return (pyomo.summation(m.costs) <= m.global_prop_dict["value"]
        [min(m.stf), "Cost budget"])
    else:
        return pyomo.Constraint.Skip


# Costs and emissions
def def_costs_rule(m, cost_type):
    # Calculate total costs by cost type.
    # Sums up process activity and capacity expansions
    # and sums them in the cost types that are specified in the set
    # m.cost_type. To change or add cost types, add/change entries
    # there and modify the if/elif cases in this function accordingly.
    # Cost types are
    #  - Investment costs for process power, storage power and
    #    storage capacity. They are multiplied by the investment
    #    factors. Rest values of units are subtracted.
    #  - Fixed costs for process power, storage power and storage
    #    capacity.
    #  - Variables costs for usage of processes, storage and transmission.
    #  - Fuel costs for stock commodity purchase.

    if cost_type == 'Invest':
        cost = \
            sum(m.cap_pro_new[p] *
                m.process_dict['inv-cost'][p] *
                m.process_dict['invcost-factor'][p]
                for p in m.pro_tuples)
        if m.mode['int']:
            cost -= \
                sum(m.cap_pro_new[p] *
                    m.process_dict['inv-cost'][p] *
                    m.process_dict['overpay-factor'][p]
                    for p in m.pro_tuples)
            #print('Invest Cost',cost)
        if m.mode['tra']:
            # transmission_cost is defined in transmission.py
            cost += transmission_cost(m, cost_type)
        if m.mode['sto']:
            # storage_cost is defined in storage.py
            cost += storage_cost(m, cost_type)
        return m.costs[cost_type] == cost

    elif cost_type == 'Fixed':
        cost = \
            sum(m.cap_pro[p] * m.process_dict['fix-cost'][p] *
                m.process_dict['cost_factor'][p]
                for p in m.pro_tuples)
        if m.mode['tra']:
            cost += transmission_cost(m, cost_type)
        if m.mode['sto']:
            cost += storage_cost(m, cost_type)
        return m.costs[cost_type] == cost

    elif cost_type == 'Variable':
        cost = \
            sum(m.tau_pro[(tm,) + p] * m.weight *
                m.process_dict['var-cost'][p] *
                m.process_dict['cost_factor'][p]
                for tm in m.tm
                for p in m.pro_tuples)
        if m.mode['tra']:
            cost += transmission_cost(m, cost_type)
        if m.mode['sto']:
            cost += storage_cost(m, cost_type)
        return m.costs[cost_type] == cost

    elif cost_type == 'Fuel':
        return m.costs[cost_type] == sum(
            m.e_co_stock[(tm,) + c] * m.weight *
            m.commodity_dict['price'][c] *
            m.commodity_dict['cost_factor'][c]
            for tm in m.tm for c in m.com_tuples
            if c[2] in m.com_stock)

    elif cost_type == 'Environmental':
        return m.costs[cost_type] == sum(
            - commodity_balance(m, tm, stf, sit, com) * m.weight *
            m.commodity_dict['price'][(stf, sit, com, com_type)] *
            m.commodity_dict['cost_factor'][(stf, sit, com, com_type)]
            for tm in m.tm
            for stf, sit, com, com_type in m.com_tuples
            if com in m.com_env)

    # Revenue and Purchase costs defined in BuySellPrice.py
    elif cost_type == 'Revenue':
        return m.costs[cost_type] == revenue_costs(m)

    elif cost_type == 'Purchase':
        return m.costs[cost_type] == purchase_costs(m)

    else:
        raise NotImplementedError("Unknown cost type.")


def def_specific_process_costs_rule(m, stf, sit, pro, cost_type):
    # Calculate total costs by cost type per process and stf. This allows to easily identify the biggest contributors to the cost functions.
    if cost_type == 'Invest':
        cost_spec = \
            (m.cap_pro_new[stf, sit, pro] *
             m.process_dict['inv-cost'][stf, sit, pro] *
             m.process_dict['invcost-factor'][stf, sit, pro])

        if m.mode['int']:
            # import pdb;pdb.set_trace()
            cost_spec -= \
                (m.cap_pro_new[stf, sit, pro] *
                 m.process_dict['inv-cost'][stf, sit, pro] *
                 m.process_dict['overpay-factor'][stf, sit, pro])

        return m.process_costs[stf, sit, pro, cost_type] == cost_spec

    elif cost_type == 'Fixed':
        cost_spec = \
            (m.cap_pro[stf, sit, pro] * m.process_dict['fix-cost'][stf, sit, pro] *
             m.process_dict['cost_factor'][stf, sit, pro]
             )

        return m.process_costs[stf, sit, pro, cost_type] == cost_spec

    elif cost_type == 'Variable':
        cost_spec = \
            sum(m.tau_pro[tm, stf, sit, pro] * m.weight *
                m.process_dict['var-cost'][stf, sit, pro] *
                m.process_dict['cost_factor'][stf, sit, pro]
                for tm in m.tm)

        return m.process_costs[stf, sit, pro, cost_type] == cost_spec

    elif cost_type == 'Fuel':
        return m.process_costs[stf, sit, pro, cost_type] == \
            sum(
                m.e_pro_in[(tm, st, si, pro, co)] * m.weight *
                m.commodity_dict['price'][st, si, co, co_type] *
                m.commodity_dict['cost_factor'][st, si, co, co_type]
                for tm in m.tm for (st, si, co, co_type) in m.com_tuples
                if st == stf
                if si == sit
                if ((stf, sit, pro, co) in m.pro_input_tuples) and co_type == "Stock")

    elif cost_type == 'Environmental':
        return m.process_costs[stf, sit, pro, cost_type] == \
            sum(
                m.e_pro_out[(tm, st, si, pro, co)] * m.weight *
                m.commodity_dict['price'][st, si, co, co_type] *
                m.commodity_dict['cost_factor'][st, si, co, co_type]
                for tm in m.tm for (st, si, co, co_type) in m.com_tuples
                if st == stf
                if si == sit
                if ((stf, sit, pro, co) in m.pro_output_tuples) and co_type == "Env")


    # Revenue and Purchase costs defined in BuySellPrice.py
    elif cost_type == 'Revenue':
        return m.process_costs[stf, sit, pro, cost_type] == revenue_costs(m)

    elif cost_type == 'Purchase':
        return m.process_costs[stf, sit, pro, cost_type] == purchase_costs(m)
    else:
        raise NotImplementedError("Unknown cost type.")

def cost_rule(m): #urbs_solar Extention

    # Calculate total base costs from m.costs
    total_base_costs = pyomo.summation(m.costs)
    total_solar_costs = pyomo.summation(m.costs_solar)
    #print("Total Base Costs:", total_base_costs)  # Print base costs for debugging
    #print("Total Urbs Solar Costs:", total_solar_costs)  # Print solar costs
    # Calculate the total combined costs
    total_costs = total_base_costs + total_solar_costs
    #print("Total Combined Costs (Base + Solar):", total_costs)  # Print total costs

    return total_costs




# CO2 output in entire period <= Global CO2 budget
def co2_rule(m):
    co2_output_sum = 0
    for stf in m.stf:
        for tm in m.tm:
            for sit in m.sit:
                # minus because negative commodity_balance represents
                # creation of that commodity.
                if m.mode['int']:
                    co2_output_sum += (- commodity_balance(m, tm, stf, sit, 'CO2') *
                                       m.weight * stf_dist(stf, m))
                else:
                    co2_output_sum += (- commodity_balance(m, tm, stf, sit, 'CO2') *
                                       m.weight)

    return (co2_output_sum)






##########################################################################################
#                                                                                        #
#  urbs_solar Additional functions and rules used to implement into existing urbs model  #
#                              25. September 2024                                        #
#                                                                                        #
##########################################################################################

#calculate total urbs costs
def def_costs_solar(m, cost_type_solar):
    if cost_type_solar == 'Importcost':
        total_import_cost = sum(m.IMPORTCOST[stf] * (m.capacity_solar_imported[stf] + m.capacity_solar_stock_imported[stf]*m.logisticcost) for stf in m.stf)
        print("Calculating Import Cost Total:")
        print(f"Total Import Cost = {total_import_cost}")
        return m.costs_solar[cost_type_solar] == total_import_cost

    elif cost_type_solar == 'Storagecost':
        total_storage_cost = sum(m.STORAGECOST * (m.capacity_solar_stock[stf]) for stf in m.stf)
        print("Calculating Storage Cost Total:")
        print(f"Total Storage Cost = {total_storage_cost}")
        return m.costs_solar[cost_type_solar] == total_storage_cost

    elif cost_type_solar == 'Eu Cost Primary':
        total_eu_cost_primary = sum(m.EU_primary_costs[stf] * (m.capacity_solar_euprimary[stf]) for stf in m.stf)
        print("Calculating EU Primary Cost Total:")
        print(f"Total EU Primary Cost = {total_eu_cost_primary}")
        return m.costs_solar[cost_type_solar] == total_eu_cost_primary

    elif cost_type_solar == 'Eu Cost Secondary':
        total_eu_cost_secondary = sum(m.EU_secondary_costs[stf] * (m.capacity_solar_eusecondary[stf]) for stf in m.stf)
        print("Calculating EU Secondary Cost Total:")
        print(f"Total EU Secondary Cost = {total_eu_cost_secondary}")
        return m.costs_solar[cost_type_solar] == total_eu_cost_secondary

    else:
        raise NotImplementedError("Unknown cost type.")

#Convert capacity solar MW to Balance MWh
def convert_totalcapacity_to_balance(m,stf):
    return m.balance_solar[stf] == m.capacity_solar[stf] * m.lf_solar * m.hours_year

def convert_capacity_1_rule(m, stf):
    return m.balance_import[stf] == m.capacity_solar_imported[stf] * m.lf_solar * m.hours_year
def convert_capacity_2_rule(m, stf):
    return m.balance_outofstock[stf] == m.capacity_solar_stockout[stf] * m.lf_solar * m.hours_year
def convert_capacity_3_rule(m, stf):
    return m.balance_EU_primary[stf] == m.capacity_solar_euprimary[stf] * m.lf_solar * m.hours_year
def convert_capacity_4_rule(m, stf):
    return m.balance_EU_secondary[stf] == m.capacity_solar_eusecondary[stf] * m.lf_solar * m.hours_year

#Calculate yearly Solar Costs
def calculate_yearly_importcost(m,stf):
        return m.costs_solar_import[stf] == m.IMPORTCOST[stf] * (m.capacity_solar_imported[stf] + m.capacity_solar_stock_imported[stf]*m.logisticcost)
def calculate_yearly_storagecost(m,stf):
    return m.costs_solar_storage[stf] == m.STORAGECOST * m.capacity_solar_stock[stf]
def calculate_yearly_EU_primary(m,stf):
    return m.costs_EU_primary[stf] == m.EU_primary_costs[stf] * m.capacity_solar_euprimary[stf]
def calculate_yearly_EU_secondary(m,stf):
    return m.costs_EU_secondary[stf] == m.EU_secondary_costs[stf] * m.capacity_solar_eusecondary[stf]



# Constraint 1: capacity_solar_y = capacity_solar_y-1 + capacity_solar_new_y for all y > y0
def capacity_solar_growth_rule(m, stf):
    if stf == m.y0:
        return pyomo.Constraint.Skip
    else:
        return m.capacity_solar[stf] == m.capacity_solar[stf-1] + m.capacity_solar_new[stf-1]

# Constraint 2: capacity_solar_y = Installed_Capacity_Q_s + capacity_solar_new_y for y = y0
def initial_capacity_rule(m, stf):
    if stf == m.y0:
        return m.capacity_solar[stf] == m.Installed_Capacity_Q_s + m.capacity_solar_new[stf]
    else:
        return pyomo.Constraint.Skip

#Constraint 3: capacity_solar_new_y = sum of capacities for all y
def capacity_solar_new_rule(m, stf):
    return m.capacity_solar_new[stf] == m.capacity_solar_imported[stf] + m.capacity_solar_stockout[stf] + m.capacity_solar_euprimary[stf] + m.capacity_solar_eusecondary[stf]

#Constraint 4:
def capacity_solar_stock_rule(m, stf):
    if stf == m.y0:
        return pyomo.Constraint.Skip
    else:
        return m.capacity_solar_stock[stf] == m.capacity_solar_stock[stf-1] + m.capacity_solar_stock_imported[stf] - m.capacity_solar_stockout[stf]

#Constraint 5:
def capacity_solar_stock_initial_rule(m, stf):
    if stf == m.y0:
        return m.capacity_solar_stock[stf] == m.Existing_Stock_Q_stock + m.capacity_solar_stock_imported[stf] - m.capacity_solar_stockout[stf]
    else:
        return pyomo.Constraint.Skip

#Constraint 6:
def importcost_solar_rule(m, stf):
    return m.importcost[stf] == m.IMPORTCOST[stf] * (m.capacity_solar_imported[stf]+ m.capacity_solar_stock_imported[stf]*m.logisticcost)

#Constraint 7:
def storagecost_solar_rule(m, stf):
    return m.storagecost[stf] == m.STORAGECOST * m.capacity_solar_stock[stf]

#Constraint 8:
def manufacturingcost_primary_solar_rule(m, stf):
    return  m.costs_eu_primary[stf] == m.EU_primary_costs[stf] * m.capacity_solar_euprimary[stf]

#Constraint 9:
def manufacturingcost_secondary_solar_rule(m, stf):
    return  m.costs_eu_secondary[stf] == m.EU_secondary_costs[stf] * m.capacity_solar_eusecondary[stf]

#def logisticscost_for_waytostock_rule(m,stf):
#    return m.logisticscost_Stock[stf] == m.logisticcost * m.capacity_solar_stock_imported[stf]

#Constraint 10&11: stock turnover
def stock_turnover_rule(m, stf):
    valid_years = [2025, 2030, 2035, 2040, 2045, 2050]
    if stf in valid_years and stf <= max(m.stf) - m.n:
        lhs = sum(m.capacity_solar_stockout[j] for j in range(stf + 5, stf + 5 + m.n) if j in m.capacity_solar_stockout)
        rhs = m.FT * (1 / m.n) * sum(
            m.capacity_solar_stock[j] for j in range(stf, stf + m.n) if j in m.capacity_solar_stock)

        return lhs >= rhs
    else:
        return pyomo.Constraint.Skip

#def compute_sum_outofstock_rule(m, stf):
#    if stf <= max(m.stf) - m.n:
#        return sum(m.capacity_solar_stockout[j] for j in range(stf, stf + m.n)) - m.sum_outofstock[stf] == 0
#    else:
#        return pyomo.Constraint.Skip

#def stock_turnover_rule(m, stf):
#    if stf <= max(m.stf) - m.n:
#        return m.sum_outofstock[stf] >= m.FT * (1 / m.n) * sum(m.capacity_solar_stock[j] for j in range(stf, stf + m.n))
#    else:
#        return pyomo.Constraint.Skip

#Constraint 12:
def anti_dumping_measures_rule(m, stf):
    return m.anti_dumping_measures[stf] == m.anti_dumping_index * (m.capacity_solar_imported[stf]+ m.capacity_solar_stock_imported[stf])

#Constraint 13:
def capacity_solar_new_limit_rule(m, stf):
    # Retrieve the values for debugging
    capacity_value = m.capacity_solar_new[stf]
    solar_new_value = m.Q_Solar_new[stf]

    # Print values for debugging
    print(f"Debug: STF = {stf}, Capacity Solar New = {capacity_value}, max instalable Capacity = {solar_new_value}")

    # Return the constraint
    return capacity_value <= solar_new_value


#Constraint 14: time delay constraint for Eu primary
def timedelay_EU_primary_production_rule(m, stf):
    if stf == m.y0:
        return pyomo.Constraint.Skip
    else:
        return m.capacity_solar_euprimary[stf] - m.capacity_solar_euprimary[stf-1] <= \
            m.deltaQ_EUprimary + m.IR_EU_primary * m.capacity_solar_euprimary[stf-1]

#Constraint 15: time delay constraint for EU secondary
def timedelay_EU_secondary_production_rule(m, stf):
    if stf == m.y0:
        return pyomo.Constraint.Skip
    else:
        return m.capacity_solar_eusecondary[stf] - m.capacity_solar_eusecondary[stf-1] <= \
            m.deltaQ_EUsecondary + m.IR_EU_secondary * m.capacity_solar_eusecondary[stf-1]

#Constraint 16:
def constraint1_EU_secondary_to_total_rule(m, stf):
    if m.y0 <= stf-m.l:
        return m.capacity_solar_eusecondary[stf] <= m.capacity_solar_new[stf-m.l]
    else:
        return pyomo.Constraint.Skip

#Constraint 17:
def constraint2_EU_secondary_to_total_rule(m, stf):
    if m.y0 >= stf-m.l:
        return m.capacity_solar_eusecondary[stf] <= m.DCR_solar * m.capacity_solar[stf]
    else:
        return pyomo.Constraint.Skip

#Constraint 18:
def constraint_EU_primary_to_total_rule(m, stf):
    if stf == m.y0:
        return pyomo.Constraint.Skip
    else:
        return m.capacity_solar_euprimary[stf] >= m.DR_primary * m.capacity_solar_euprimary[stf-1]

#Constraint 19:
def constraint_EU_secondary_to_secondary_rule(m, stf):
    if stf == m.y0:
        return pyomo.Constraint.Skip
    else:
        return m.capacity_solar_eusecondary[stf] >= m.DR_secondary * m.capacity_solar_eusecondary[stf-1]

#TBD



