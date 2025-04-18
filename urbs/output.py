import pandas as pd
from .input import get_input
from .pyomoio import get_entity, get_entities
from .util import is_string


def get_constants(instance):
    """Return summary DataFrames for important variables

    Usage:
        costs, cpro, ctra, csto = get_constants(instance)

    Args:
        instance: an urbs model instance

    Returns:
        (costs, cpro, ctra, csto) tuple

    Example:
        >>> import pyomo.environ
        >>> from pyomo.opt.base import SolverFactory
        >>> data = read_excel('mimo-example.xlsx')
        >>> prob = create_model(data, range(1,25))
        >>> optim = SolverFactory('glpk')
        >>> result = optim.solve(prob)
        >>> cap_pro = get_constants(prob)[1]['Total']
        >>> cap_pro.xs('Wind park', level='Process').apply(int)
        Site
        Mid      13000
        North    23258
        South        0
        Name: Total, dtype: int64
    """


    costs = get_entity(instance, 'costs')
    cpro = get_entities(instance, ['cap_pro', 'cap_pro_new'])
    ctra = get_entities(instance, ['cap_tra', 'cap_tra_new'])
    csto = get_entities(instance, ['cap_sto_c', 'cap_sto_c_new',
                                   'cap_sto_p', 'cap_sto_p_new'])

    ##########################################################################
    #                                                                        #
    # Handling of extra report df for better Display of Results and Plotting #
    #                                                                        #
    ##########################################################################
####gather BD df to see if it works 13. january 2025
    decisionvalues_pri = get_entity(instance, 'BD_pri')
    #print(decisionvalues_pri)
    decisionvalues_sec = get_entity(instance, 'BD_sec')
    #print(decisionvalues_sec)
    price_reduction = get_entity(instance, 'pricereduction_pri')
    #print(price_reduction)
    capacityprimary = get_entity(instance, 'capacity_solar_euprimary')
    #print(capacityprimary)
    # Print the values of BD
    #print("Decision variable values for BD:")
    #for stf in m.stf:
    #    for n in m.nsteps:
    #        print(f"BD[{stf}, {n}] = {m.BD[stf, n].value}")


####Gather all relevant urbs-solar df's

    process_cost = get_entity(instance, 'process_costs')

    solar_costs = get_entity(instance,'costs_solar')

    csolar = get_entities(instance, ['capacity_solar_imported', 'capacity_solar_stockout',
                                     'capacity_solar_euprimary', 'capacity_solar_eusecondary',
                                     'capacity_solar_stock','capacity_solar_stock_imported'])

    bsolar = get_entity(instance, 'balance_solar')

    yearly_cost_solar = get_entities(instance, ['costs_solar_import', 'costs_solar_storage',
                                     'costs_EU_primary', 'costs_EU_secondary'])
    capacity_solar_total = get_entity(instance, 'capacity_solar')

    e_pro_out_df = get_entity(instance, 'e_pro_out')
    #print(e_pro_out_df)

#####Process df's to be used in report sheets

####us_co2
    e_pro_out_co2 = {key: value for key, value in e_pro_out_df.items() if key[-1] == 'CO2'}
    df_co2 = pd.DataFrame(list(e_pro_out_co2.items()), columns=['Index', 'Value'])

####us_balance
    e_pro_out_elec = {key: value for key, value in e_pro_out_df.items() if key[-1] == 'Elec'}
    #print(e_pro_out_elec)
    df_Elec = pd.DataFrame(list(e_pro_out_elec.items()), columns=['Index', 'Value'])
    df_Elec['Stf'] = df_Elec['Index'].apply(lambda x: int(x[1]))
    df_bsolar = pd.DataFrame(bsolar, columns=['balance_solar'])
    df_bsolar['Index'] = range(2024, 2051)
    solar_process = pd.DataFrame({
        'Index': [(1,float(year),'EU27', 'Solar', 'Elec') for year in df_bsolar['Index']],
        'Value': df_bsolar['balance_solar'],
        'Stf': df_bsolar['Index']
    })
    combined_balance = pd.concat([df_Elec, solar_process], ignore_index=True)
    combined_balance = combined_balance.sort_values(by='Stf').reset_index(drop=True)
    combined_balance[['tm', 'Year', 'Site', 'Process', 'Type']] = pd.DataFrame(combined_balance['Index'].tolist(),
                                                                                 index=combined_balance.index)
    combined_balance = combined_balance[['Stf','Process', 'Value']]


####us_cost
    df_process = pd.DataFrame(process_cost)
    df_process_reset = df_process.reset_index()
    cost_types_to_sum = ['Invest','Fixed', 'Variable', 'Fuel', 'Environmental']
    df_process_summed = df_process_reset[df_process_reset['cost_type'].isin(cost_types_to_sum)].groupby(
        ['stf', 'pro'])['process_costs'].sum().reset_index()
    df_process_summed.rename(columns={'process_costs': 'Total_Cost'}, inplace=True)
    df_solar_melted = yearly_cost_solar.reset_index().melt(id_vars='stf',
                                                  var_name='pro',
                                                  value_name='Total_Cost')
    cost_df_combined = pd.concat([df_process_summed, df_solar_melted], ignore_index=True)
    cost_df_combined = round(cost_df_combined.groupby(['stf', 'pro'])['Total_Cost'].sum().reset_index(),2)

####us_capacity
    # Resetting the index for processing
    csolar.reset_index(inplace=True)

    # Melting the DataFrame
    long_csolar = csolar.melt(id_vars='stf', var_name='pro', value_name='New')

    # Grouping by year and process type
    capacity_sum = long_csolar.groupby(['stf', 'pro'])['New'].sum().reset_index()

    # Initialize Total
    capacity_sum['Total'] = 0

    # Loop through each row to compute Total
    for i, row in capacity_sum.iterrows():
        current_year = row['stf']
        process_type = row['pro']

        # Calculate total capacity for the process type
        total_capacity = capacity_sum[
            (capacity_sum['pro'] == process_type) &
            (capacity_sum['stf'] <= current_year)
            ]['New'].sum()

        # Update Total
        capacity_sum.at[i, 'Total'] = total_capacity

    # Calculate Solar Stock
    # Assuming you have these columns in csolar DataFrame
    # Initialize the Solar Stock calculation with the given value for year 0
    initial_capacity = 40000  # Initial stock for year 0

    # Create a DataFrame for Solar Stock
    solar_stock_data = []

    for year in csolar['stf'].unique():
        if year == 2024:
            solar_stock = initial_capacity+csolar[csolar['stf'] == year]['capacity_solar_stock_imported'].sum() - csolar[csolar['stf'] == year]['capacity_solar_stockout'].sum()
        else:
            solar_stock = csolar[csolar['stf'] == year]['capacity_solar_stock_imported'].sum() - \
                          csolar[csolar['stf'] == year]['capacity_solar_stockout'].sum()

        solar_stock_data.append({'stf': year, 'pro': 'Solar Stock', 'New': solar_stock})

    # Convert to DataFrame
    solar_stock_df = pd.DataFrame(solar_stock_data)

    # Calculate the Total for Solar Stock
    solar_stock_df['Total'] = solar_stock_df['New'].cumsum()  # Cumulative sum to get Total for Solar Stock

    # Combine Solar Stock Data with Capacity Sum
    capacity_sum = pd.concat([capacity_sum, solar_stock_df], ignore_index=True)

    # Filter out unwanted processes
    processes_to_remove = ['capacity_solar_stock_imported', 'capacity_solar_stock']
    capacity_sum = capacity_sum[~capacity_sum['pro'].isin(processes_to_remove)]

    # Create a final index and DataFrame
    final_index = pd.MultiIndex.from_tuples(
        [(row['stf'], 'EU27', row['pro']) for _, row in capacity_sum.iterrows()],
        names=['Stf', 'Site', 'Process']
    )

    # Creating the final DataFrame
    final_solar_df = pd.DataFrame({
        'Total': capacity_sum['Total'].values,
        'New': capacity_sum['New'].values
    }, index=final_index)

    # Setting float levels for index
    final_solar_df.index = final_solar_df.index.set_levels([float(i) for i in final_solar_df.index.levels[0]], level=0)

    # Final output excludes 'capacity_solar_stock_imported' and 'capacity_solar_stock'

    # Final output includes the new 'Solar Stock' process

    # better labels and index names and return sorted
    if not cpro.empty:
        cpro.index.names = ['Stf', 'Site', 'Process']
        cpro.columns = ['Total', 'New']
        cpro.sort_index(inplace=True)
    final_cpro = pd.concat([cpro.reset_index(), final_solar_df.reset_index().drop(columns='Site')], ignore_index=True)
    final_cpro.set_index(['Stf', 'Site', 'Process'], inplace=True)
########################################################################################################################


    if not ctra.empty:
        ctra.index.names = (['Stf', 'Site In', 'Site Out',
                             'Transmission', 'Commodity'])
        ctra.columns = ['Total', 'New']
        ctra.sort_index(inplace=True)
    if not csto.empty:
        csto.index.names = ['Stf', 'Site', 'Storage', 'Commodity']
        csto.columns = ['C Total', 'C New', 'P Total', 'P New']
        csto.sort_index(inplace=True)

#### Process df's to be used in report sheets

    combined_cpro_csolar = pd.concat([final_cpro, final_solar_df])
    combined_cpro_csolar = round(combined_cpro_csolar.groupby(level=['Stf', 'Site', 'Process']).sum(),2)


    solar_costs = solar_costs.rename('costs')
    combined_costs_df = pd.concat([costs, solar_costs], ignore_index=False)


    return costs, cpro, ctra, csto, csolar,combined_cpro_csolar,cost_df_combined,capacity_solar_total,df_co2,combined_balance,decisionvalues_pri,decisionvalues_sec


def get_timeseries(instance, stf, com, sites, timesteps=None):
    """Return DataFrames of all timeseries referring to given commodity

    Usage:
        created, consumed, stored, imported, exported,
        dsm = get_timeseries(instance, commodity, sites, timesteps)

    Args:
        - instance: a urbs model instance
        - com: a commodity name
        - sites: a site name or list of site names
        - timesteps: optional list of timesteps, default: all modelled
          timesteps

    Returns:
        a tuple of (created, consumed, storage, imported, exported, dsm) with
        DataFrames timeseries. These are:

        - created: timeseries of commodity creation, including stock source
        - consumed: timeseries of commodity consumption, including demand
        - storage: timeseries of commodity storage (level, stored, retrieved)
        - imported: timeseries of commodity import
        - exported: timeseries of commodity export
        - dsm: timeseries of demand-side management
    """
    if timesteps is None:
        # default to all simulated timesteps
        timesteps = sorted(get_entity(instance, 'tm').index)
    else:
        timesteps = sorted(timesteps)  # implicit: convert range to list

    if is_string(sites):
        # wrap single site name into list
        sites = [sites]

    # DEMAND
    # default to zeros if commodity has no demand, get timeseries
    try:
        # select relevant timesteps (=rows)
        # select commodity (xs), then the sites from remaining simple columns
        # and sum all together to form a Series
        demand = (
            pd.DataFrame.from_dict(
                get_input(
                    instance,
                    'demand_dict')).loc[stf] .loc[timesteps].xs(
                com,
                axis=1,
                level=1)[sites].sum(
                    axis=1))
    except KeyError:
        demand = pd.Series(0, index=timesteps)
    demand.name = 'Demand'

    # STOCK
    eco = get_entity(instance, 'e_co_stock')
    try:
        eco = eco.xs((stf, com, 'Stock'), level=['stf', 'com', 'com_type'])
        stock = eco.unstack()[sites].sum(axis=1)
    except KeyError:
        stock = pd.Series(0, index=timesteps)
    stock.name = 'Stock'

    # PROCESS
    created = get_entity(instance, 'e_pro_out')

    try:
        created = created.xs((stf, com), level=['stf', 'com']).loc[timesteps]
        created = created.unstack(level='sit')[sites].fillna(0).sum(axis=1)
        created = created.unstack(level='pro')
        created = drop_all_zero_columns(created)

    except KeyError:

        created = pd.DataFrame(index=timesteps[1:])





    consumed = get_entity(instance, 'e_pro_in')
    try:
        consumed = consumed.xs((stf, com), level=['stf', 'com']).loc[timesteps]
        consumed = consumed.unstack(level='sit')[sites].fillna(0).sum(axis=1)
        consumed = consumed.unstack(level='pro')
        consumed = drop_all_zero_columns(consumed)
    except KeyError:
        consumed = pd.DataFrame(index=timesteps[1:])

    # TRANSMISSION
    other_sites = (get_input(instance, 'site')
                   .xs(stf, level='support_timeframe').index.difference(sites))

    # if commodity is transportable
    try:
        df_transmission = get_input(instance, 'transmission')
        if com in set(df_transmission.index.get_level_values('Commodity')):
            imported = get_entity(instance, 'e_tra_out')
            # avoid negative value import for DCPF transmissions
            if instance.mode['dpf']:
                # -0.01 to avoid numerical errors such as -0
                minus_imported = imported[(imported < -0.01)]
                minus_imported = -1 * minus_imported.swaplevel('sit', 'sit_')
                imported = imported[imported >= 0]
                imported = pd.concat([imported, minus_imported])
            imported = imported.loc[timesteps].xs(
                (stf, com), level=['stf', 'com'])
            imported = imported.unstack(level='tra').sum(axis=1)
            imported = imported.unstack(
                level='sit_')[sites].fillna(0).sum(
                axis=1)
            imported = imported.unstack(level='sit')

            internal_import = imported[sites].sum(axis=1)  # ...from sites
            if instance.mode['dpf']:
                imported = imported[[x for x in other_sites if x in imported.keys()]]  # ...to existing other_sites
            else:
                imported = imported[other_sites]  # ...from other_sites
            imported = drop_all_zero_columns(imported.fillna(0))

            exported = get_entity(instance, 'e_tra_in')
            # avoid negative value export for DCPF transmissions
            if instance.mode['dpf']:
                # -0.01 to avoid numerical errors such as -0
                minus_exported = exported[(exported < -0.01)]
                minus_exported = -1 * minus_exported.swaplevel('sit', 'sit_')
                exported = exported[exported >= 0]
                exported = pd.concat([exported, minus_exported])
            exported = exported.loc[timesteps].xs(
                (stf, com), level=['stf', 'com'])
            exported = exported.unstack(level='tra').sum(axis=1)
            exported = exported.unstack(
                level='sit')[sites].fillna(0).sum(
                axis=1)
            exported = exported.unstack(level='sit_')

            internal_export = exported[sites].sum(
                axis=1)  # ...to sites (internal)
            if instance.mode['dpf']:
                exported = exported[[x for x in other_sites if x in exported.keys()]]  # ...to existing other_sites
            else:
                exported = exported[other_sites]  # ...to other_sites
            exported = drop_all_zero_columns(exported.fillna(0))
        else:
            imported = pd.DataFrame(index=timesteps)
            exported = pd.DataFrame(index=timesteps)
            internal_export = pd.Series(0, index=timesteps)
            internal_import = pd.Series(0, index=timesteps)

        # to be discussed: increase demand by internal transmission losses
        internal_transmission_losses = internal_export - internal_import
        demand = demand + internal_transmission_losses
    except KeyError:
        # imported and exported are empty
        imported = exported = pd.DataFrame(index=timesteps)

    # STORAGE
    # group storage energies by commodity
    # select all entries with desired commodity co
    stored = get_entities(instance, ['e_sto_con', 'e_sto_in', 'e_sto_out'])
    try:
        stored = stored.loc[timesteps].xs((stf, com), level=['stf', 'com'])
        stored = stored.groupby(level=['t', 'sit']).sum()
        stored = stored.loc[(slice(None), sites), :].groupby('t').sum()
        stored.columns = ['Level', 'Stored', 'Retrieved']
    except (KeyError, ValueError):
        stored = pd.DataFrame(0, index=timesteps,
                              columns=['Level', 'Stored', 'Retrieved'])

    # DEMAND SIDE MANAGEMENT (load shifting)
    dsmup = get_entity(instance, 'dsm_up')
    dsmdo = get_entity(instance, 'dsm_down')

    if dsmup.empty:
        # if no DSM happened, the demand is not modified (delta = 0)
        delta = pd.Series(0, index=timesteps)

    else:
        # DSM happened (dsmup implies that dsmdo must be non-zero, too)
        # so the demand will be modified by the difference of DSM up and
        # DSM down uses
        # for sit in m.dsm_site_tuples:
        try:
            # select commodity
            dsmup = dsmup.xs((stf, com), level=['stf', 'com'])
            dsmdo = dsmdo.xs((stf, com), level=['stf', 'com'])

            # select sites
            dsmup = dsmup.unstack()[sites].sum(axis=1)
            dsmdo = dsmdo.unstack()[sites].sum(axis=1)

            # convert dsmdo to Series by summing over the first time level
            dsmdo = dsmdo.unstack().sum(axis=0)
            dsmdo.index.names = ['t']

            # derive secondary timeseries
            delta = dsmup - dsmdo
        except KeyError:
            delta = pd.Series(0, index=timesteps)

    shifted = demand + delta

    shifted.name = 'Shifted'
    demand.name = 'Unshifted'
    delta.name = 'Delta'

    dsm = pd.concat((shifted, demand, delta), axis=1)

    # JOINS
    created = created.join(stock)  # show stock as created
    consumed = consumed.join(shifted.rename('Demand'))

    # VOLTAGE ANGLE of sites

    try:
        voltage_angle = get_entity(instance, 'voltage_angle')
        voltage_angle = voltage_angle.xs(stf, level=['stf']).loc[timesteps]
        voltage_angle = voltage_angle.unstack(level='sit')[sites]
    except (KeyError, AttributeError, TypeError):
        voltage_angle = pd.DataFrame(index=timesteps)
    voltage_angle.name = 'Voltage Angle'

    return created, consumed, stored, imported, exported, dsm, voltage_angle


def drop_all_zero_columns(df):
    """ Drop columns from DataFrame if they contain only zeros.

    Args:
        df: a DataFrame

    Returns:
        the DataFrame without columns that only contain zeros
    """
    return df.loc[:, (df != 0).any(axis=0)]
