import os

import pandas as pd
import numpy as np
import itertools

# # Grab data from databases for plotting new and existing capacity
# def _load_capacity_capex(scen_labels_, path):

#     # Load project capacity table and process them from database
#     def __load_new_and_existing_csv(capacity_, projects_, zones_, scenario):

#         capacity_['capacity_mw'] = capacity_['capacity_mw'].astype(float)
#         capacity_['Status']      = 'new'

#         for project in projects_['project'].unique():
#             if capacity_.loc[(capacity_['project'] == project) & (capacity_['period'] == 2020), 'capacity_mw'].to_numpy()[0] != 0.:
#                 capacity_.loc[capacity_['project'] == project, 'Status'] = 'existing'

#         periods_ = capacity_['period'].unique()
#         techs_   = capacity_['technology'].unique()
#         status_  = capacity_['Status'].unique()

#         capacity_all_ = []

#         for tech, i_tech in zip(techs_, range(len(techs_))):
#             for period, i_period in zip(periods_, range(len(periods_))):
#                 for zone, i_zone in zip(zones_, range(len(zones_))):
#                     for status, i_status in zip(status_, range(len(status_))):

#                         # Find specific row from database
#                         if zone == 'India':
#                             idx_ = (capacity_['period'] == period) & (capacity_['technology'] == tech) & (capacity_['Status'] == status)
#                         else:
#                             idx_ = (capacity_['period'] == period) & (capacity_['technology'] == tech) & (capacity_['Status'] == status)

#                         capacity_all_ += [[scenario,
#                                            period,
#                                            tech,
#                                            zone,
#                                            status,
#                                            np.sum(capacity_.loc[idx_, 'capacity_mw']),
#                                            np.sum(capacity_.loc[idx_, 'energy_capacity_mwh'])]]

#         return pd.DataFrame(np.array(capacity_all_), columns = ['Scenario', 'Period', 'Technology', 'Zone', 'Status', 'Power', 'Energy']).sort_values(by = ['Scenario', 'Period', 'Technology', 'Zone']).reset_index(drop = True)

#     scenarios_ = scen_labels_['scenario'].unique()
#     zones_     = scen_labels_['zone'].unique()
#     dfs_       = []

#     # Open connection: open database and grab meta-data
#     for scenario in scenarios_:
#         print(scenario)
#         dir_name        = r'{}/{}'.format(path, scenario)
#         capacity_table_ = pd.read_csv(dir_name + r'/results/project_period.csv', low_memory = False)
#         spec_table_     = pd.read_csv(dir_name + r'/inputs/spec_capacity_period_params.tab', sep = '\t', engine = 'python')
#         project_table_  = pd.read_csv(dir_name + r'/inputs/projects.tab', sep = '\t', engine = 'python')
#         project_table_  = project_table_[project_table_['project'].isin(pd.unique(spec_table_['project']))]

#         # Load specified capacity from csv files
#         dfs_.append(__load_new_and_existing_csv(capacity_table_, project_table_, zones_, scenario))

#     dfs_           = pd.concat(dfs_, axis = 0).reset_index(drop = True)
#     dfs_['Power']  = dfs_['Power'].astype(float)
#     dfs_['Energy'] = dfs_['Energy'].astype(float)
#     dfs_['Period'] = dfs_['Period'].astype(int)
#     return dfs_

def _group_capacity_technologies(capacity_all_, tech_labels_):

    def __agg(df_, row_, x_):
        idx_  = df_['Technology'].isin(x_)
        row_ += [df_.loc[idx_, 'Power'].sum(), df_.loc[idx_, 'Energy'].sum()]
        df_   = df_.drop(df_.index.values[idx_])
        df_   = df_.reset_index(drop = True)
        df_.loc[len(df_.index)] = row_
        return df_

    groups_ = tech_labels_['group'].unique()

    dfs_ = []
    for scenario in capacity_all_['Scenario'].unique():
        for period in capacity_all_['Period'].unique():
            for zone in capacity_all_['Zone'].unique():
                for status in capacity_all_['Status'].unique():
                    idx_ = (capacity_all_['Scenario'] == scenario) & (capacity_all_['Period'] == period) & (capacity_all_['Zone'] == zone) & (capacity_all_['Status'] == status)
                    df_  = capacity_all_.loc[idx_]
                    for group in groups_:
                        techs_ = tech_labels_.loc[tech_labels_['group'] == group, 'technology'].to_list()
                        df_    = __agg(df_, [scenario, period, group, zone, status], techs_)
                    dfs_.append(df_)
    return pd.concat(dfs_).sort_values(by = ['Scenario', 'Period', 'Technology', 'Zone']).reset_index(drop = True)

# Grab data from databases for plotting new and existing capacity
def _load_new_and_existing_capacity_by_zone(scenarios_, path):

    # Load project capacity table and process them from database
    def __load_new_and_existing_csv(table_, projects_, scenario):

        table_['capacity_mw'] = table_['capacity_mw'].astype(float)
        table_['Status']      = 'new'
        
        for project in projects_['project'].unique():      
            
            if table_.loc[(table_['project'] == project) & (table_['period'] == 2020), 'capacity_mw'].to_numpy()[0] != 0.: 
                table_.loc[table_['project'] == project, 'Status'] = 'existing'
        
        periods_ = table_['period'].unique()
        techs_   = table_['technology'].unique()
        status_  = table_['Status'].unique()
        zones_   = table_['load_zone'].unique()

        capacity_all_ = []
        for zone, i_zone in zip(zones_, range(len(zones_))):
            for tech, i_tech in zip(techs_, range(len(techs_))):
                for period, i_period in zip(periods_, range(len(periods_))):
                    for status, i_status in zip(status_, range(len(status_))):
                        # Find specific row from database 
                        if zone == 'all_nodes': 
                            idx_ = (table_['period'] == period) & (table_['technology'] == tech) & (table_['Status'] == status)
                        else:               
                            idx_ = (table_['period'] == period) & (table_['technology'] == tech) & (table_['Status'] == status) & (table_['load_zone'] == zone)
                            
                        capacity_all_ += [[scenario, 
                                           period, 
                                           tech, 
                                           zone, 
                                           status, 
                                           np.sum(table_.loc[idx_, 'capacity_mw'])]]

        return pd.DataFrame(np.array(capacity_all_), columns = ['Scenario', 'Period', 'Technology', 'Zone', 'Status', 'Power'])

    # Load energy dispatch table and process data from database
    def __load_peak_demand_from_csv(demand_table_, scenario):
        zones_   = demand_table_['LOAD_ZONES'].unique()
        periods_ = demand_table_['period'].unique()
        demand_  = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                # Find specific row from database 
                idx_ = (demand_table_['LOAD_ZONES'] == zone) & (demand_table_['period'] == period)
                
                demand_ += [[scenario, 
                             period, 
                             'Load', 
                             zone, 
                             'new', 
                             demand_table_.loc[idx_, 'load_mw'].max()]]

        return pd.DataFrame(np.array(demand_), columns = ['Scenario', 'Period', 'Technology', 'Zone', 'Status', 'Power'])
    
    dfs_ = []

    # Open connection: open database and grab meta-data
    for scenario in scenarios_:
        print(scenario)
        dir_name        = r'{}/{}'.format(path, scenario)
        capacity_table_ = pd.read_csv(dir_name + r'/results/capacity_all.csv')
        spec_table_     = pd.read_csv(dir_name + r'/inputs/spec_capacity_period_params.tab', sep = '\t', engine = 'python')
        project_table_  = pd.read_csv(dir_name + r'/inputs/projects.tab', sep = '\t', engine = 'python')
        project_table_  = project_table_[project_table_['project'].isin(pd.unique(spec_table_['project']))]
        demand_table_   = pd.read_csv(dir_name + r'/inputs/load_mw.tab', sep = '\t', engine = 'python')

        # Load specified capacity from csv files
        cap_ = __load_new_and_existing_csv(capacity_table_, project_table_, scenario)

        # Load peak demand from csv files
        demand_table_['period'] = demand_table_['timepoint'].apply(lambda x: int(str(x)[:4]))
        demand_table_['period'] = demand_table_['period'].apply(lambda x: x - (x % 5))
        demand_                 = __load_peak_demand_from_csv(demand_table_, scenario)

        dfs_.append(pd.concat([cap_, demand_], axis = 0).reset_index(drop = True))

    dfs_           = pd.concat(dfs_, axis = 0).reset_index(drop = True)
    dfs_['Power']  = dfs_['Power'].astype(float)
    dfs_['Period'] = dfs_['Period'].astype(int)
    return dfs_

# # Grab data from databases for plotting LCOE emissions
# def _load_energy_dispatch_by_zone(scen_labels_, path):

#     # Load energy dispatch table and process data from database
#     def __load_demand_from_csv(demand_table_, timepoints_table_, zones_, scenario):
#         periods_ = timepoints_table_['period'].unique()
#         demand_  = []
#         for period, i_period in zip(periods_, range(len(periods_))):
#             for zone, i_zone in zip(zones_, range(len(zones_))):
#                 # Find specific row from database 
#                 idx_ = timepoints_table_['period'] == period

#                 if zone == 'all_nodes':
#                     state_demand_              = demand_table_.groupby('timepoint').agg({'load_mw': 'sum'})
#                     state_demand_['timepoint'] = state_demand_.index
#                     state_demand_              = state_demand_.reset_index(drop = True)              
#                 else:
#                     state_demand_ = demand_table_.loc[demand_table_['LOAD_ZONES'] == zone].reset_index(drop = True)  

#                 demand_ += [[scenario, 
#                              period, 
#                              'Load', 
#                              zone, 
#                              np.sum(state_demand_.loc[idx_, 'load_mw']*timepoints_table_.loc[idx_, 'timepoint_weight'])]]

#         return pd.DataFrame(np.array(demand_), columns = ['Scenario', 'Period', 'Technology', 'Zone', 'Energy'])

    # Load energy dispatch table and process data from database
    def __load_ed_from_csv(table_, zones_, scenario):
        
        periods_ = ed_table_['period'].unique()
        techs_   = ed_table_['technology'].unique()

        dispatch_ = []
        for tech, i_tech in zip(techs_, range(len(techs_))):
            for period, i_period in zip(periods_, range(len(periods_))):
                for zone, i_zone in zip(zones_, range(len(zones_))):
                    # Find specific row from database 
                    if zone == 'all_nodes':
                        idx_ = (table_['period'] == period) & (table_['technology'] == tech)
                    else:
                        idx_ = (table_['period'] == period) & (table_['technology'] == tech) & (table_['load_zone'] == zone)
                                                
                    dispatch_ += [[scenario, 
                                   period, 
                                   tech, 
                                   zone, 
                                   np.sum(table_.loc[idx_, 'timepoint_weight']*table_.loc[idx_, 'power_mw'])]]

        return pd.DataFrame(np.array(dispatch_), columns = ['Scenario', 'Period', 'Technology', 'Zone', 'Energy'])
    
    scenarios_ = scen_labels_['scenario'].unique()
    zones_     = scen_labels_['zone'].unique()
    dfs_       = []
    # Open connection: open database and grab meta-data
    for scenario in scenarios_:
        print(scenario)
        dir_name          = r'{}/{}'.format(path, scenario)
        demand_table_     = pd.read_csv(dir_name + r'/inputs/load_mw.tab', sep = '\t', engine = 'python')
        timepoints_table_ = pd.read_csv(dir_name + r'/inputs/timepoints.tab', sep = '\t', engine = 'python')
        ed_table_         = pd.read_csv(dir_name + r'/results/dispatch_all.csv')
        zones_            = ed_table_['load_zone'].unique()

        # Load energy demand from csv files
        ed_     = __load_ed_from_csv(ed_table_, zones_, scenario)
        demand_ = __load_demand_from_csv(demand_table_, timepoints_table_, zones_, scenario)
        dfs_   += [pd.concat([ed_, demand_], axis = 0).reset_index(drop = True)]
        
    dfs_           = pd.concat(dfs_, axis = 0).reset_index(drop = True)
    dfs_['Energy'] = dfs_['Energy'].astype(float)

    return dfs_


def _group_capacity_technologies_by_zone(capacity_all_, tech_groups_):
    def __agg(df_, row_, x_):
        idx_  = df_['Technology'].isin(x_)
        row_ += [df_.loc[idx_, 'Power'].sum()]  
        df_   = df_.drop(df_.index.values[idx_])
        df_   = df_.reset_index(drop = True)
        df_.loc[len(df_.index)] = row_
        return df_

    dfs_ = []
    for scenario in capacity_all_['Scenario'].unique():
        for period in capacity_all_['Period'].unique():
            for zone in capacity_all_['Zone'].unique():
                for status in capacity_all_['Status'].unique():
                    idx_ = (capacity_all_['Scenario'] == scenario) & (capacity_all_['Period'] == period) & (capacity_all_['Zone'] == zone) & (capacity_all_['Status'] == status)
                    df_ = capacity_all_.loc[idx_]
                    for tech_group_ in tech_groups_:
                        df_ = __agg(df_, [scenario, period, tech_group_[0], zone, status], tech_group_[1])

                    dfs_.append(df_)        
    return pd.concat(dfs_).reset_index(drop = True)


def _group_dispatch_technologies_by_zone(ed_, tech_groups_):

    def __agg(df_, row_, x_):
        idx_                    = df_['Technology'].isin(x_)
        row_                   += [df_.loc[idx_, 'Energy'].sum()]  
        df_                     = df_.drop(df_.index.values[idx_])
        df_                     = df_.reset_index(drop = True)
        df_.loc[len(df_.index)] = row_
        return df_
    
    dfs_ = []
    for scenario in ed_['Scenario'].unique():
        for period in ed_['Period'].unique():
            for zone in ed_['Zone'].unique():
                idx_ = (ed_['Scenario'] == scenario) & (ed_['Period'] == period) & (ed_['Zone'] == zone)
                df_ = ed_.loc[idx_]

                for tech_group_ in tech_groups_:
                    df_ = __agg(df_, [scenario, period, tech_group_[0], zone], tech_group_[1])
                dfs_.append(df_) 
                
    return pd.concat(dfs_).reset_index(drop = True)


# # Grab data from databases for plotting energy dispatch and clean energy targets
# def _load_energy_dispatch(scen_labels_, path):

#     # Load energy dispatch table and process data from database
#     def __load_ed_from_csv(ed_, zones_, scenario):
        
#         periods_  = ed_['period'].unique()
#         techs_    = ed_['technology'].unique()
#         dispatch_ = []
#         for tech, i_tech in zip(techs_, range(len(techs_))):
#             for period, i_period in zip(periods_, range(len(periods_))):
#                 for zone, i_zone in zip(zones_, range(len(zones_))):
#                     # Find specific row from database 
#                     if zone == 'all_nodes':
#                         idx_ = (ed_['period'] == period) & (ed_['technology'] == tech)
#                     else:
#                         idx_ = (ed_['period'] == period) & (ed_['technology'] == tech) & (ed_['load_zone'] == zone)
                                                
#                     dispatch_ += [[scenario, 
#                                    period, 
#                                    tech, 
#                                    zone, 
#                                    np.sum(ed_.loc[idx_, 'number_of_hours_in_timepoint']*ed_.loc[idx_, 'timepoint_weight']*ed_.loc[idx_, 'power_mw'])]]

#         return pd.DataFrame(np.array(dispatch_), columns = ['Scenario', 'Period', 'Technology', 'Zone', 'Energy'])

#     # Load energy dispatch table and process data from database
#     def __load_demand_from_csv(table_, zones_, scenario):
        
#         periods_ = table_['period'].unique()
#         demand_  = []
#         for period, i_period in zip(periods_, range(len(periods_))):
#             for zone, i_zone in zip(zones_, range(len(zones_))):
#                 # Find specific row from database 
#                 if zone == 'all_nodes':
#                     idx_ = (table_['period'] == period)
#                 else:
#                     idx_ = (table_['period'] == period) & (table_['load_zone'] == zone)

#                 demand_ += [[scenario, 
#                              period, 
#                              'Shedding', 
#                              zone, 
#                              np.sum(table_.loc[idx_, 'number_of_hours_in_timepoint']*table_.loc[idx_, 'timepoint_weight']*table_.loc[idx_, 'unserved_energy_mw'])]]

#                 demand_ += [[scenario, 
#                              period, 
#                              'Curtailment', 
#                              zone, 
#                              np.sum(table_.loc[idx_, 'number_of_hours_in_timepoint']*table_.loc[idx_, 'timepoint_weight']*table_.loc[idx_, 'overgeneration_mw'])]]

#         return pd.DataFrame(np.array(demand_), columns = ['Scenario', 'Period', 'Technology', 'Zone', 'Energy'])

#     scenarios_ = scen_labels_['scenario'].unique()
#     zones_     = scen_labels_['zone'].unique()
#     dfs_       = []
#     # Open connection: open database and grab meta-data
#     for scenario in scenarios_:
#         print(scenario)
#         dir_name = r'{}/{}'.format(path, scenario)
#         ed_      = pd.read_csv(dir_name + r'/results/project_timepoint.csv', low_memory = False)
#         demand_  = pd.read_csv(dir_name + r'/results/system_load_zone_timepoint.csv', low_memory = False)
#         # Load energy dispatch from csv files
#         dfs_ += [__load_ed_from_csv(ed_, zones_, scenario)]
#         dfs_ += [__load_demand_from_csv(demand_, zones_, scenario)]

#     dfs_           = pd.concat(dfs_, axis = 0).reset_index(drop = True)
#     dfs_['Energy'] = dfs_['Energy'].astype(float)

#     return dfs_

# Grab data from databases for plotting energy exchange
def _load_energy_transmission(scen_labels_, path):

    def __load_tx_exchange_from_csv(table_, zones, scenario):

        periods_ = table_['period'].unique()

        exchange_ = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                # Find specific row from database 
                if zone == 'all_nodes':
                    imports = 0.
                    exports = 0.
                else:
                    state_exchange_ = table_.loc[table_['load_zone_to'] == zone].reset_index(drop = True)                    
                    idx_            = table_['period'] == period           
                    
                    aux_ = state_exchange_.loc[idx_, 'transmission_flow_mw']*state_exchange_.loc[idx_, 'timepoint_weight']*state_exchange_.loc[idx_, 'number_of_hours_in_timepoint']
                    imports = np.sum(aux_.loc[aux_ > 0.]) 
                    exports = np.sum(aux_.loc[aux_ < 0.]) 
                exchange_ += [[scenario, period, zone, imports, exports]]

        return pd.DataFrame(np.array(exchange_), columns = ['Scenario', 'Period', 'Zone', 'Import', 'Export'])

    # Load energy dispatch table and process data from database
    def __load_tx_loss_from_csv(table_, zones_, scenario):

        periods_ = table_['period'].unique()

        losses_ = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                # Find specific row from database 
                if zone == 'all_nodes': 
                    idx_ = (table_['period'] == period)
                else:                   
                    idx_ = (table_['period'] == period) & (table_['load_zone_to'] == zone)
                
                losses_ += [[scenario, 
                             period, 
                             zone,  
                             np.sum(table_.loc[idx_, 'number_of_hours_in_timepoint']*table_.loc[idx_, 'timepoint_weight']*table_.loc[idx_, 'transmission_losses_lz_from']), 
                             np.sum(table_.loc[idx_, 'number_of_hours_in_timepoint']*table_.loc[idx_, 'timepoint_weight']*table_.loc[idx_, 'transmission_losses_lz_to'])]]

        return pd.DataFrame(np.array(losses_), columns = ['Scenario', 'Period', 'Zone', 'Tx_Losses_fr', 'Tx_Losses_to'])

    # Load energy dispatch table and process data from database
    def __load_demand_from_csv(demand_table_, timepoints_table_, zones_, scenario):

        periods_ = timepoints_table_['period'].unique()
        
        demand_ = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                # Find specific row from database 
                idx_ = timepoints_table_['period'] == period
                if zone == 'all_nodes':
                    state_demand_              = demand_table_.groupby('timepoint').agg({'load_mw': 'sum'})
                    state_demand_['timepoint'] = state_demand_.index
                    state_demand_              = state_demand_.reset_index(drop = True)              
                else:
                    state_demand_ = demand_table_.loc[demand_table_['LOAD_ZONES'] == zone].reset_index(drop = True) 
                    
                demand_ += [[scenario, 
                             period, 
                             zone, 
                             np.sum(state_demand_.loc[idx_, 'load_mw']*timepoints_table_.loc[idx_, 'timepoint_weight'])]]

        return pd.DataFrame(np.array(demand_), columns = ['Scenario', 'Period', 'Zone', 'Load'])
    
    scenarios_ = scen_labels_['scenario'].unique()
    zones_     = scen_labels_['zone'].unique()
    dfs_       = []

    # Open connection: open database and grab meta-data
    for scenario in scenarios_:
        print(scenario)
        dir_name          = r'{}/{}'.format(path, scenario)
        exchange_table_   = pd.read_csv(dir_name + r'/results/transmission_timepoint.csv')
        demand_table_     = pd.read_csv(dir_name + r'/inputs/load_mw.tab', sep = '\t', engine = 'python')
        timepoints_table_ = pd.read_csv(dir_name + r'/inputs/timepoints.tab', sep = '\t', engine = 'python')
   
        # Imports and exports exchanges from csv files
        exchange_ = __load_tx_exchange_from_csv(exchange_table_, zones_, scenario)    
        # Load transmission losses from csv files
        tx_loss_ = __load_tx_loss_from_csv(exchange_table_, zones_, scenario) 
        # Load enregy curtailmenet from csv files
        demand_ = __load_demand_from_csv(demand_table_, timepoints_table_, zones_, scenario)
        df_   = pd.merge(exchange_, tx_loss_, on = ['Scenario', 'Period', 'Zone']).reset_index(drop = True)
        dfs_ += [pd.merge(df_, demand_, on = ['Scenario', 'Period', 'Zone']).reset_index(drop = True)]

    dfs_                 = pd.concat(dfs_, axis = 0).reset_index(drop = True)
    dfs_['Export']       = dfs_['Export'].astype(float)
    dfs_['Import']       = dfs_['Import'].astype(float)
    dfs_['Tx_Losses_to'] = dfs_['Tx_Losses_to'].astype(float)
    dfs_['Tx_Losses_fr'] = dfs_['Tx_Losses_fr'].astype(float)
    dfs_['Load']         = dfs_['Load'].astype(float)

    return dfs_

def _merge_ed_and_tx(ed_, Tx_):

    #ed_ = ed_.loc[(ed_['Technology'] != 'Battery') & (ed_['Technology'] != 'Hydrogen') & (ed_['Technology'] != 'Hydro_Pumped')]
    df_  = ed_.groupby(['Scenario', 'Period', 'Zone'], as_index = False).agg({'Energy': 'sum'})
    
    idx_ = df_['Period'] == '2050'
    df_  = pd.merge(df_, Tx_, on = ['Scenario', 'Period', 'Zone']).reset_index(drop = True)
    
    idx_ = Tx_['Period'] == '2050'
    # Caculate state-level curtailment and loses
    df_.loc[df_['Zone'] != 'India', 'Curtailment'] = df_['Load'] - df_['Energy'] - df_['Import'] + df_['Export'] 
    df_.loc[df_['Zone'] != 'India', 'Tx_Losses']   = - df_['Tx_Losses_fr']
    df_.loc[df_['Zone'] != 'India', 'Export']      = - df_['Export']

    # Caculate national-level curtailment and losses
    df_.loc[df_['Zone'] == 'India', 'Curtailment'] = df_['Load'] + (df_['Tx_Losses_to'] + df_['Tx_Losses_fr']) - df_['Energy']
    df_.loc[df_['Zone'] == 'India', 'Tx_Losses']   = - df_['Tx_Losses_to'] - df_['Tx_Losses_fr']
    df_.loc[df_['Zone'] == 'India', 'Export']      = 0.
    df_.loc[df_['Zone'] == 'India', 'Import']      = 0.

    # Caculate Load Shedding
    df_.loc[df_['Curtailment'] > 0., 'Shedding'] = df_.loc[df_['Curtailment'] > 0., 'Curtailment']
    df_.loc[df_['Curtailment'] > 0., 'Curtailment'] = 0.
    df_ = df_.fillna(0.)
    df_ = df_.drop(columns = ['Energy', 'Tx_Losses_to', 'Tx_Losses_fr', 'Energy', 'Load'])

    # Merge both dataframes
    dfs_     = []
    columns_ = ['Curtailment', 'Shedding', 'Import', 'Tx_Losses', 'Export']
    for column in columns_:
        df_p_               = df_.drop(columns = [i for i in columns_ if i != column])
        df_p_['Technology'] = column
        dfs_               += [df_p_.rename(columns = {column: 'Energy'})]

    return pd.concat([ed_, pd.concat(dfs_, axis = 0)], axis = 0).sort_values(by = ['Period']).reset_index(drop = True)


def _group_dispatch_technologies(dispatch_, tech_labels_):

    def __agg(df_, row_, x_):
        idx_                    = df_['Technology'].isin(x_)
        row_                   += [df_.loc[idx_, 'Energy'].sum()]
        df_                     = df_.drop(df_.index.values[idx_])
        df_                     = df_.reset_index(drop = True)
        df_.loc[len(df_.index)] = row_
        return df_

    groups_ = tech_labels_['group'].unique()
    dfs_    = []
    for scen in dispatch_['Scenario'].unique():
        for period in dispatch_['Period'].unique():
            for zone in dispatch_['Zone'].unique():
                df_ = dispatch_.loc[ (dispatch_['Scenario'] == scen) & (dispatch_['Period'] == period) & (dispatch_['Zone'] == zone)]
                for group in groups_:
                    techs_ = tech_labels_.loc[tech_labels_['group'] == group, 'technology'].to_list()
                    df_    = __agg(df_, [scen, period, group, zone], techs_)
                dfs_.append(df_) 
                
    dfs_           = pd.concat(dfs_).reset_index(drop = True)
    dfs_['Energy'] = dfs_['Energy'].astype(float)
    return dfs_


def _load_RPS(data_, clean_techs_):

    scenarios_ = data_['Scenario'].unique()
    periods_   = data_['Period'].unique()
    zones_     = data_['Zone'].unique()
    RPS_ = []
    for scenario in scenarios_:
        for zone in zones_:
            for period in periods_:
                idx_1_ = (data_['Period'] == period) & (data_['Scenario'] == scenario) & (data_['Zone'] == zone)
                idx_2_ = data_['Technology'].isin(clean_techs_)
                demand = data_.loc[idx_1_, 'Energy'].sum()

                clean = data_.loc[idx_1_ & idx_2_, 'Energy'].sum()
                rps = 100*clean/demand
                # if rps > 100.:
                #     rps = 100
                RPS_.append([scenario, 
                             period, 
                             zone, 
                             clean, 
                             demand, 
                             rps])
            
    return pd.DataFrame(np.stack(RPS_), columns = ['Scenario', 'Period', 'Zone', 'Clean_Energy', 'Energy', 'RPS']).sort_values(by = ['Scenario', 'Period', 'Technology', 'Zone']).reset_index(drop = True)


# Grab data from databases for plotting GHG emissions
def _GHG_emissions(scenarios_, zones_, path):
    
    # Load GHG emissions table and process them from database
    def __load_GHG_from_csv(table_, zones_, scenario):
        
        periods_   = table_['period'].unique()
        techs_     = table_['technology'].unique()
        emissions_ = []
        for tech, i_tech in zip(techs_, range(len(techs_))):
            for period, i_period in zip(periods_, range(len(periods_))):
                for zone, i_zone in zip(zones_, range(len(zones_))):
                    # Find specific row from database 
                    if zone == 'India': idx_ = (table_['period'] == period) & (table_['technology'] == tech)
                    else:               idx_ = (table_['period'] == period) & (table_['technology'] == tech) & (table_['load_zone'] == zone)
                    
                    emissions_ += [[scenario, 
                                    period, 
                                    tech, 
                                    zone, 
                                    np.sum(table_.loc[idx_, 'timepoint_weight']*table_.loc[idx_, 'carbon_emissions_tons'])]]

        return pd.DataFrame(np.array(emissions_), columns = ['Scenario', 'Period', 'Technology', 'Zone', 'GHG'])

    # Load energy dispatch table and process data from database
    def __load_demand_from_csv(demand_table_, timepoints_table_, zones_, scenario):
        periods_ = timepoints_table_['period'].unique()
        demand_  = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                # Find specific row from database 
                idx_ = timepoints_table_['period'] == period

                if zone == 'India': 
                    state_demand_              = demand_table_.groupby('timepoint').agg({'load_mw': 'sum'})
                    state_demand_['timepoint'] = state_demand_.index
                    state_demand_              = state_demand_.reset_index(drop = True)              
                else:
                    state_demand_ = demand_table_.loc[demand_table_['LOAD_ZONES'] == zone].reset_index(drop = True)  

                demand_ += [[scenario, 
                             period, 
                             zone, 
                             np.sum(state_demand_.loc[idx_, 'load_mw']*timepoints_table_.loc[idx_, 'timepoint_weight'])]]

        return pd.DataFrame(np.array(demand_), columns = ['Scenario', 'Period', 'Zone', 'Load'])

    # Open connection: open database and grab meta-data
    dfs_ = []
    demands_ = []
    for scenario in scenarios_:
        print(scenario)
        dir_name = r'{}/{}'.format(path, scenario)
        tables_  = pd.read_csv(dir_name + r'/results/carbon_emissions_by_project.csv')
        
        demand_table_     = pd.read_csv(dir_name + r'/inputs/load_mw.tab', sep = '\t', engine = 'python')
        timepoints_table_ = pd.read_csv(dir_name + r'/inputs/timepoints.tab', sep = '\t', engine = 'python')
        # Load energy demand from csv files
        demand_ = __load_demand_from_csv(demand_table_, timepoints_table_, zones_, scenario)
        # Load GHG emissions from cvs files        
        emissions_        = __load_GHG_from_csv(tables_, zones_, scenario)
        emissions_['GHG'] = emissions_['GHG'].astype(float)
        dfs_.append(emissions_)
        demands_.append(demand_)

    return pd.concat(dfs_, axis = 0).reset_index(drop = True), pd.concat(demands_, axis = 0).reset_index(drop = True)

# Grab data from databases for plotting LCOE emissions
def _load_system_cost(scen_labels_, path, gp_model):
    # Load fuel, and operation and maintanace cost table and process data from database
    def __load_vr_cost_from_csv(table_, zones_, scenario):
        periods_ = table_['period'].unique()
        vr_cost_ = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                # Find specific row from database
                if zone == 'all_nodes': idx_ = table_['period'] == period
                else:               idx_ = (table_['period'] == period) & (table_['load_zone'] == zone)

                vr_cost_ += [[scenario,
                              period,
                              zone,
                              np.sum(table_.loc[idx_, 'number_of_hours_in_timepoint']*table_.loc[idx_, 'timepoint_weight']*table_.loc[idx_, 'variable_om_cost'])]]

        return pd.DataFrame(np.array(vr_cost_), columns = ['Scenario', 'Period', 'Zone', 'Variable_Costs']).sort_values(by = ['Scenario', 'Period', 'Zone']).reset_index(drop = True)

    # Load fix capacity cost table and process data from database
    def __load_fx_cost_from_csv(table_, zones_, scenario):
        periods_ = table_['period'].unique()
        fx_cost_ = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                # Find specific row from database
                if zone == 'all_nodes': 
                    idx_ = table_['period'] == period
                else:                   
                    idx_ = (table_['period'] == period) & (table_['load_zone'] == zone)

                fx_cost_ += [[scenario,
                              period,
                              zone,
                              np.sum(table_.loc[idx_, 'capacity_cost']) + np.sum(table_.loc[idx_, 'fixed_cost'])]]

        return pd.DataFrame(np.array(fx_cost_), columns = ['Scenario', 'Period', 'Zone', 'Fix_Costs'])

    # Load transmission capacity cost table and process data from database
    def __load_tx_cost_from_csv(table_, zones_, scenario):
        periods_ = table_['period'].unique()
        tx_cost_ = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                # Find specific row from database
                if zone == 'all_nodes': 
                    idx_ = table_['period'] == period
                else:                   
                    idx_ = (table_['period'] == period) & (table_['load_zone_to'] == zone)

                tx_cost_ += [[scenario,
                              period,
                              zone,
                              np.sum(table_.loc[idx_, 'capacity_cost']) + np.sum(table_.loc[idx_, 'fixed_cost'])]]

        return pd.DataFrame(np.array(tx_cost_), columns = ['Scenario', 'Period', 'Zone', 'Tx_Costs'])

    # Load energy dispatch table and process data from database
    def __load_demand_from_csv(demand_table_, timepoints_table_, zones_, scenario):
        periods_ = timepoints_table_['period'].unique()
        demand_  = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                # Find specific row from database
                idx_ = timepoints_table_['period'] == period
                if zone == 'all_nodes':
                    state_demand_              = demand_table_.groupby('timepoint').agg({'load_mw': 'sum'})
                    state_demand_['timepoint'] = state_demand_.index
                    state_demand_              = state_demand_.reset_index(drop = True)
                else:
                    state_demand_ = demand_table_.loc[demand_table_['LOAD_ZONES'] == zone].reset_index(drop = True)

                demand_ += [[scenario,
                             period,
                             zone,
                             np.sum(timepoints_table_.loc[idx_, 'number_of_hours_in_timepoint']*state_demand_.loc[idx_, 'load_mw']*timepoints_table_.loc[idx_, 'timepoint_weight'])]]

        return pd.DataFrame(np.array(demand_), columns = ['Scenario', 'Period', 'Zone', 'Load'])

    scenarios_ = scen_labels_['scenario'].to_list()
    zones_     = scen_labels_['zone'].to_list()

    dfs_ = []
    # Open connection: open database and grab meta-data
    for scen, i_scen in zip(scenarios_, range(len(scenarios_))):
        print(scen)
        dir_name = r'{}/{}'.format(path, scen)
        if gp_model == 'production':
            fx_table_   = []
            vr_table_   = []
            tx_table_   = []
            demand_     = []
            timepoints_ = []
            for folder in next(os.walk(dir_name))[1]:
                fx_table_.append(pd.read_csv(dir_name + f'/{folder}/results/project_period.csv', low_memory = False))
                vr_table_.append(pd.read_csv(dir_name + f'/{folder}/results/project_timepoint.csv', low_memory = False))
                demand_.append(pd.read_csv(dir_name + f'/{folder}/inputs/load_mw.tab', sep = '\t', engine = 'python'))
                timepoints_.append(pd.read_csv(dir_name + f'/{folder}/inputs/timepoints.tab', sep = '\t', engine = 'python'))

                try:
                    tx_table_.append(pd.read_csv(dir_name + f'/{folder}/results/transmission_period.csv', low_memory = False))  
                except:
                    pass
                    
            fx_table_   = pd.concat(fx_table_, axis = 0).reset_index(drop = True)
            vr_table_   = pd.concat(vr_table_, axis = 0).reset_index(drop = True)
            demand_     = pd.concat(demand_, axis = 0).reset_index(drop = True)
            timepoints_ = pd.concat(timepoints_, axis = 0).reset_index(drop = True)

            try:
                tx_table_ = pd.concat(tx_table_, axis = 0).reset_index(drop = True)
            except:
                pass

        elif gp_model == 'capex':
            fx_table_   = pd.read_csv(dir_name + f'/results/project_period.csv', low_memory = False)
            vr_table_   = pd.read_csv(dir_name + f'/results/project_timepoint.csv', low_memory = False)
            demand_     = pd.read_csv(dir_name + f'/inputs/load_mw.tab', sep = '\t', engine = 'python')
            timepoints_ = pd.read_csv(dir_name + f'/inputs/timepoints.tab', sep = '\t', engine = 'python')
            
            try:
                tx_table_   = pd.read_csv(dir_name + f'/results/transmission_period.csv', low_memory = False)     
            except:
                pass
        
        zone = [zones_[i_scen]]

        # Load energy demand from csv files
        demand_ = __load_demand_from_csv(demand_, timepoints_, zone, scen)
        # Load fix costs from csv files
        fx_cost_ = __load_fx_cost_from_csv(fx_table_, zone, scen)
        # Load variables costs from csv files
        vr_cost_ = __load_vr_cost_from_csv(vr_table_, zone, scen)

        df_ = pd.merge(vr_cost_, fx_cost_, on = ['Scenario', 'Period', 'Zone'])
        df_ = pd.merge(df_, demand_, on = ['Scenario', 'Period', 'Zone'])

        try:
            tx_cost_    = __load_tx_cost_from_csv(tx_table_, zone, scen)
            df_         = pd.merge(df_, tx_cost_, on = ['Scenario', 'Period', 'Zone'])
            df_['Cost'] = df_['Fix_Costs'].astype(float) + df_['Variable_Costs'].astype(float) + df_['Tx_Costs'].astype(float)
        except:
            df_['Cost'] = df_['Fix_Costs'].astype(float) + df_['Variable_Costs'].astype(float)

        df_['Load'] = df_['Load'].astype(float)
        df_['LCOE'] = df_['Cost'].astype(float)/df_['Load'].astype(float)
        dfs_.append(df_)

    return pd.concat(dfs_, axis = 0).reset_index(drop = True)


# Grab data from databases for plotting LCOE emissions
def _load_technology_costs(scenarios_, zones_, path):
    # Load fuel, and operation and maintanace cost table and process data from database
    def __load_vr_cost_from_csv(table_, zones_, scenario):
        periods_ = table_['period'].unique()
        techs_ = table_['technology'].unique()

        vr_cost_ = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                for tech, i_tech in zip(techs_, range(len(techs_))):

                    # Find specific row from database 
                    if zone == 'India': idx_ = (table_['period'] == period) & (table_['technology'] == tech)
                    else:               idx_ = (table_['period'] == period) & (table_['load_zone'] == zone) & (table_['technology'] == tech)
                    
                    vr_cost_ += [[scenario, 
                                  period, 
                                  zone, 
                                  tech, 
                                  np.sum(table_.loc[idx_, 'timepoint_weight']*table_.loc[idx_, 'variable_om_cost'])]]

        return pd.DataFrame(np.array(vr_cost_), columns = ['Scenario', 'Period', 'Zone', 'Technology', 'Variable_Costs'])

    # Load fix capacity cost table and process data from database
    def __load_fx_cost_from_csv(table_, zones_, scenario):
        periods_ = table_['period'].unique()
        techs_   = table_['technology'].unique()
        fx_cost_ = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                for tech, i_tech in zip(techs_, range(len(techs_))):

                    # Find specific row from database 
                    if zone == 'India': idx_ = (table_['period'] == period) & (table_['technology'] == tech)
                    else:               idx_ = (table_['period'] == period) & (table_['load_zone'] == zone) & (table_['technology'] == tech)
                    
                    fx_cost_ += [[scenario, 
                                  period, 
                                  zone, 
                                  tech, 
                                  np.sum(table_.loc[idx_, 'capacity_cost'])]]

        return pd.DataFrame(np.array(fx_cost_), columns = ['Scenario', 'Period', 'Zone', 'Technology', 'Fix_Costs'])

    # Load transmission capacity cost table and process data from database
    def __load_tx_cost_from_csv(table_, zones_, scenario):
        periods_ = table_['period'].unique()
        tx_cost_ = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                # Find specific row from database 
                if zone == 'India': idx_ = table_['period'] == period
                else:               idx_ = (table_['period'] == period) & (table_['load_zone_to'] == zone)
                
                tx_cost_ += [[scenario, 
                              period, 
                              zone, 
                              'Tx', 
                              np.sum(table_.loc[idx_, 'capacity_cost']), 
                              0.]]

        return pd.DataFrame(np.array(tx_cost_), columns = ['Scenario', 'Period', 'Zone', 'Technology', 'Fix_Costs', 'Variable_Costs'])

    # Load energy dispatch table and process data from database
    def __load_demand_from_csv(demand_table_, timepoints_table_, zones_, scenario):
        periods_ = timepoints_table_['period'].unique()
        demand_  = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                # Find specific row from database 
                idx_ = timepoints_table_['period'] == period

                if zone == 'India': 
                    state_demand_              = demand_table_.groupby('timepoint').agg({'load_mw': 'sum'})
                    state_demand_['timepoint'] = state_demand_.index
                    state_demand_              = state_demand_.reset_index(drop = True)              
                else:
                    state_demand_ = demand_table_.loc[demand_table_['LOAD_ZONES'] == zone].reset_index(drop = True)  

                demand_ += [[scenario, 
                             period, 
                             zone, 
                             np.sum(state_demand_.loc[idx_, 'load_mw']*timepoints_table_.loc[idx_, 'timepoint_weight'])]]

        return pd.DataFrame(np.array(demand_), columns = ['Scenario', 'Period', 'Zone', 'Load'])
    
    dfs_ = []
    # Open connection: open database and grab meta-data
    for scenario in scenarios_:
        print(scenario)
        dir_name          = r'{}/{}'.format(path, scenario)
        demand_table_     = pd.read_csv(dir_name + r'/inputs/load_mw.tab', sep = '\t', engine = 'python')
        timepoints_table_ = pd.read_csv(dir_name + r'/inputs/timepoints.tab', sep = '\t', engine = 'python')
        fx_table_         = pd.read_csv(dir_name + r'/results/costs_capacity_all_projects.csv')
        vr_table_         = pd.read_csv(dir_name + r'/results/costs_operations.csv')
        tx_table_         = pd.read_csv(dir_name + r'/results/costs_transmission_capacity.csv')

        # Load energy demand from csv files
        demand_ = __load_demand_from_csv(demand_table_, timepoints_table_, zones_, scenario)
        #print(demand_)
        # Load fix costs from csv files
        fx_cost_ = __load_fx_cost_from_csv(fx_table_, zones_, scenario)
        #print(fx_cost_)
        # Load variables costs from csv files
        vr_cost_ = __load_vr_cost_from_csv(vr_table_, zones_, scenario)
        #print(vr_cost_)
        # Load transmission costs from csv files
        tx_cost_ = __load_tx_cost_from_csv(tx_table_, zones_, scenario)
        #print(tx_cost_)

        df_ = pd.merge(vr_cost_, fx_cost_,  on = ['Scenario', 'Period', 'Zone', 'Technology'])
        df_ = pd.concat([df_, tx_cost_], axis = 0)
        for period in demand_['Period'].unique():
            df_.loc[df_['Period'] == period, 'Load'] = demand_.loc[demand_['Period'] == period, 'Load'].to_numpy()[0]
            
        df_['Fix_Costs']      = df_['Fix_Costs'].astype(float)
        df_['Variable_Costs'] = df_['Variable_Costs'].astype(float)
        df_['Load']           = df_['Load'].astype(float)

        dfs_.append(df_)
    return pd.concat(dfs_, axis = 0).reset_index(drop = True)

def _group_technology_costs(technology_costs_, tech_groups_):
    def __agg(df_, row_, x_):
        idx_  = df_['Technology'].isin(x_)
        row_ += [df_.loc[idx_, 'Variable_Costs'].sum(), df_.loc[idx_, 'Fix_Costs'].sum(), df_.loc[idx_, 'Load'].mean()]  
        df_   = df_.drop(df_.index.values[idx_])
        df_   = df_.reset_index(drop = True)
        df_.loc[len(df_.index)] = row_
        return df_

    dfs_ = []
    for scenario in technology_costs_['Scenario'].unique():
        for period in technology_costs_['Period'].unique():
            for zone in technology_costs_['Zone'].unique():
                idx_ = (technology_costs_['Scenario'] == scenario) 
                idx_ = idx_& (technology_costs_['Period'] == period) & (technology_costs_['Zone'] == zone) 
                df_  = technology_costs_.loc[idx_]
                
                for tech_group_ in tech_groups_:
                    print(tech_group_)
                    df_ = __agg(df_, [scenario, period, zone, tech_group_[0][0]], tech_group_[1])
                    
                dfs_.append(df_)        
                
    return pd.concat(dfs_).reset_index(drop = True)


# Grab data from databases for plotting GHG emissions
def _load_GHG_emissions(scen_labels_, path, gp_model):

    # Load GHG emissions table and process them from database
    def __load_GHG_from_csv(ed_, zones_, scenario):

        periods_   = ed_['period'].unique()
        techs_     = ed_['technology'].unique()
        emissions_ = []
        for tech, i_tech in zip(techs_, range(len(techs_))):
            for period, i_period in zip(periods_, range(len(periods_))):
                for zone, i_zone in zip(zones_, range(len(zones_))):
                    # Find specific row from database
                    if zone == 'all_nodes': idx_ = (ed_['period'] == period) & (ed_['technology'] == tech)
                    else:                   idx_ = (ed_['period'] == period) & (ed_['technology'] == tech) & (ed_['load_zone'] == zone)

                    emissions_ += [[scenario,
                                    period,
                                    tech,
                                    zone,
                                    np.sum(ed_.loc[idx_, 'number_of_hours_in_timepoint']*ed_.loc[idx_, 'timepoint_weight']*ed_.loc[idx_, 'carbon_emissions_tons'])]]

        return pd.DataFrame(np.array(emissions_), columns = ['Scenario', 'Period', 'Technology', 'Zone', 'GHG']).sort_values(by = ['Scenario', 'Period', 'Technology', 'Zone']).reset_index(drop = True)

    # Load energy dispatch table and process data from database
    def __load_demand_from_csv(demand_table_, timepoints_table_, zones_, scenario):
        periods_ = timepoints_table_['period'].unique()
        demand_  = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                # Find specific row from database
                idx_ = timepoints_table_['period'] == period

                if zone == 'all_nodes':
                    state_demand_              = demand_table_.groupby('timepoint').agg({'load_mw': 'sum'})
                    state_demand_['timepoint'] = state_demand_.index
                    state_demand_              = state_demand_.reset_index(drop = True)
                else:
                    state_demand_ = demand_table_.loc[demand_table_['LOAD_ZONES'] == zone].reset_index(drop = True)

                demand_ += [[scenario,
                             period,
                             zone,
                             np.sum(timepoints_table_.loc[idx_, 'number_of_hours_in_timepoint']*state_demand_.loc[idx_, 'load_mw']*timepoints_table_.loc[idx_, 'timepoint_weight'])]]

        return pd.DataFrame(np.array(demand_), columns = ['Scenario', 'Period', 'Zone', 'Load'])

    # Open connection: open database and grab meta-data
    dfs_     = []
    demands_ = []
    scenarios_ = scen_labels_['scenario'].to_list()
    zones_     = scen_labels_['zone'].to_list()

    for scen, i_scen in zip(scenarios_, range(len(scenarios_))):
        print(scen)
        dir_name = r'{}/{}'.format(path, scen)

        if gp_model == 'production':
            ed_         = []
            demand_     = []
            timepoints_ = []
            for folder in next(os.walk(dir_name))[1]:
                ed_.append(pd.read_csv(dir_name + f'/{folder}/results/project_timepoint.csv', low_memory=False))
                demand_.append(pd.read_csv(dir_name + f'/{folder}/inputs/load_mw.tab', sep = '\t', engine = 'python'))
                timepoints_.append(pd.read_csv(dir_name + f'/{folder}/inputs/timepoints.tab', sep = '\t', engine = 'python'))
            ed_         = pd.concat(ed_, axis = 0).reset_index(drop = True)
            demand_     = pd.concat(demand_, axis = 0).reset_index(drop = True)
            timepoints_ = pd.concat(timepoints_, axis = 0).reset_index(drop = True)

        if gp_model == 'capex':
            ed_         = pd.read_csv(dir_name + f'/results/project_timepoint.csv', low_memory=False)
            demand_     = pd.read_csv(dir_name + f'/inputs/load_mw.tab', sep = '\t', engine = 'python')
            timepoints_ = pd.read_csv(dir_name + f'/inputs/timepoints.tab', sep = '\t', engine = 'python')
            
        # Load GHG emissions from cvs files
        zone              = [zones_[i_scen]]
        emissions_        = __load_GHG_from_csv(ed_, zone, scen)
        emissions_['GHG'] = emissions_['GHG'].astype(float)

        # Load energy demand from csv files
        demand_         = __load_demand_from_csv(demand_, timepoints_, zone, scen)
        demand_['Load'] = demand_['Load'].astype(float)

        dfs_.append(emissions_)
        demands_.append(demand_)

    return pd.concat(dfs_, axis = 0).reset_index(drop = True), pd.concat(demands_, axis = 0).reset_index(drop = True)

def _GHG_emissions_intensity(emissions_, demands_):
    emissions_ = emissions_.drop(columns = ['Technology'])
    emissions_ = emissions_.groupby(['Scenario', 'Zone', 'Period'], as_index = False).sum()

    emissions_['Load'] = 0.
    for scen in emissions_['Scenario'].unique():
        print(scen)
        for zone in emissions_['Zone'].unique():
            for period in emissions_['Period'].unique():
                idx_1_ = (demands_['Scenario'] == scen) & (demands_['Zone'] == zone) & (demands_['Period'] == period)
                idx_2_ = (emissions_['Scenario'] == scen) & (emissions_['Zone'] == zone) & (emissions_['Period'] == period)

                emissions_.loc[idx_2_, 'Load'] = float(demands_.loc[idx_1_, 'Load'].to_numpy()[0])

        emissions_['Load'] = emissions_['Load'].astype(float)
    emissions_['Intensity'] = emissions_['GHG']/emissions_['Load']
    return emissions_.sort_values(by = ['Scenario', 'Period', 'Zone']).reset_index(drop = True), demands_

# # Grab data from databases for plotting state generation  
# def _load_energy_dispatch_by_scenario_and_period(scenario, period, path):
    
#     dir_name = r'{}/{}'.format(path, scenario)

#     ed_ = pd.read_csv(dir_name + r'/results/dispatch_all.csv')
#     # Grab data and meta-data for plotting LCOE graph
#     ed_               = ed_.loc[ed_['period'] == period].reset_index(drop = True)
#     ed_['energy_mwh'] = ed_['timepoint_weight'] * ed_['power_mw']
#     ed_               = ed_.drop(columns = ['horizon', 
#                                             'project', 
#                                             'period', 
#                                             'operational_type', 
#                                             'timepoint', 
#                                             'balancing_type', 
#                                             'power_mw', 
#                                             'timepoint_weight', 
#                                             'number_of_hours_in_timepoint'])
        
#     return ed_.groupby(['load_zone', 'technology'], as_index = False).agg('sum')

# Grab data from databases for plotting state generation  
def _load_energy_flow_by_scenario_and_period(cities_, scenario, period, path):

    def __processing_tx_operations(tx_, cities_):
        def __zone_to_cood(cities_, key):
            idx_ = cities_['state'] == key
            lat  = cities_.loc[idx_, 'pie_lat'].to_numpy()[0]
            lon  = cities_.loc[idx_, 'pie_lon'].to_numpy()[0]
            return lat, lon

        tx_['from_lat'] = 0.
        tx_['from_lon'] = 0.
        tx_['to_lat']   = 0.
        tx_['to_lon']   = 0.

        for i in range(tx_.shape[0]):
            tx_.loc[i, 'from_lat'], tx_.loc[i, 'from_lon'] = __zone_to_cood(cities_, tx_.loc[i, 'lz_from'])
            tx_.loc[i, 'to_lat'], tx_.loc[i, 'to_lon']     = __zone_to_cood(cities_, tx_.loc[i, 'lz_to'])

        return tx_.drop(columns = ['lz_from', 'lz_to'])
    
    dir_name = r'{}/{}'.format(path, scenario)

    flow_ = pd.read_csv(dir_name + r'/results/transmission_operations.csv')
    
    tx_lines_ = flow_['tx_line'].unique()
    periods_  = flow_['period'].unique()
    
    agg_flow_ = []

    for tx_line in tx_lines_:
        idx_    = (flow_['tx_line'] == tx_line) & (flow_['period'] == period)
        flow_p_ = (flow_.loc[idx_, 'timepoint_weight'] * flow_.loc[idx_, 'transmission_flow_mw']).to_numpy()
        imports = flow_p_[flow_p_ > 0.].sum()
        exports = flow_p_[flow_p_ < 0.].sum()
        lz_from = tx_line.split('-')[0].replace('_new', '')
        lz_to   = tx_line.split('-')[1].replace('_new', '')

        agg_flow_.append([lz_from, lz_to, imports, exports])
    
    index_ = ['lz_from', 'lz_to', 'imports', 'exports']
    agg_flow_ = pd.DataFrame(np.stack(agg_flow_).T, index = index_).T

    agg_flow_ = __processing_tx_operations(agg_flow_, cities_) 
                 
    agg_flow_['imports'] = agg_flow_['imports'].astype(float)
    agg_flow_['exports'] = agg_flow_['exports'].astype(float)

    agg_flow_['from_lat'] = agg_flow_['from_lat'].astype(float)
    agg_flow_['from_lon'] = agg_flow_['from_lon'].astype(float)
    agg_flow_['to_lat']   = agg_flow_['to_lat'].astype(float)
    agg_flow_['to_lon']   = agg_flow_['to_lon'].astype(float)

    for i in range(agg_flow_.shape[0]):

        if (agg_flow_.index == i).sum() == 1:
        
            row_ = agg_flow_.loc[i]
            idx_ = (agg_flow_['from_lat'] == row_['from_lat']) & (agg_flow_['from_lon'] == row_['from_lon']) 
            idx_ = idx_ & (agg_flow_['to_lat'] == row_['to_lat']) & (agg_flow_['to_lon'] == row_['to_lon'])

            if idx_.sum() > 1:
                agg_flow_.loc[agg_flow_.index[idx_][0], 'imports'] = agg_flow_.loc[agg_flow_.index[idx_], 'imports'].sum()
                agg_flow_.loc[agg_flow_.index[idx_][0], 'exports'] = agg_flow_.loc[agg_flow_.index[idx_], 'exports'].sum()

                agg_flow_ = agg_flow_.drop(agg_flow_.index[idx_][1:].tolist())

    agg_flow_ = agg_flow_.reset_index(drop = True)

    agg_flow_['total'] = agg_flow_['imports'] - agg_flow_['exports']
    agg_flow_['net']   = np.absolute(agg_flow_['imports'] + agg_flow_['exports'])
    
    return agg_flow_

# Grab data from databases for plotting state generation  
def _load_transmission_capacity_by_scenario_and_period(cities_, scenario, period, path):

    def __processing_tx_file(tx_, cities_):
        def __zone_to_cood(cities_, key):
            idx_ = cities_['state'] == key
            lat  = cities_.loc[idx_, 'pie_lat'].to_numpy()[0]
            lon  = cities_.loc[idx_, 'pie_lon'].to_numpy()[0]
            return lat, lon

        tx_['from_lat'] = 0.
        tx_['from_lon'] = 0.
        tx_['to_lat']   = 0.
        tx_['to_lon']   = 0.

        for i in range(tx_.shape[0]):
            tx_.loc[i, 'from_lat'], tx_.loc[i, 'from_lon'] = __zone_to_cood(cities_, tx_.loc[i, 'load_zone_from'])
            tx_.loc[i, 'to_lat'], tx_.loc[i, 'to_lon']     = __zone_to_cood(cities_, tx_.loc[i, 'load_zone_to'])

        return tx_.drop(columns = ['load_zone_from', 'load_zone_to'])
    
    dir_name = r'{}/{}'.format(path, scenario)
    
    tx_ = pd.read_csv(dir_name + r'/results/transmission_capacity.csv')
    tx_ = __processing_tx_file(tx_, cities_)
    tx_ = tx_.drop(columns = ['transmission_min_capacity_mw'])
    tx_ = tx_.rename(columns = {'transmission_max_capacity_mw': 'capacity_mw'})

    idx_       = (tx_['period'] == period) & (tx_['capacity_mw'] > 0.)
    idx_new_   = tx_['tx_line'].apply(lambda x: 'new' in x)
    tx_new_    = tx_.loc[idx_ & idx_new_].reset_index(drop = True)
    tx_        = tx_.loc[idx_ & ~idx_new_].reset_index(drop = True)
    lines_     = tx_[['from_lon', 'to_lon', 'from_lat', 'to_lat', 'capacity_mw']].to_numpy()
    lines_new_ = tx_new_[['from_lon', 'to_lon', 'from_lat', 'to_lat', 'capacity_mw']].to_numpy()

    return lines_, lines_new_

# # Grab data from databases for plotting state capacity  
# def _load_capacity_by_scenario_and_period(scenario, period, path):
    
#     dir_name = r'{}/{}'.format(path, scenario)

#     capacity_ = pd.read_csv(dir_name + r'/results/capacity_all.csv')
#     # Grab data and meta-data for plotting LCOE graph
#     capacity_ = capacity_.loc[capacity_['period'] == period].reset_index(drop = True)
#     capacity_ = capacity_.drop(columns = ['capacity_type', 
#                                           'hyb_gen_capacity_mw', 
#                                           'hyb_stor_capacity_mw', 
#                                           'fuel_prod_capacity_fuelunitperhour', 
#                                           'fuel_rel_capacity_fuelunitperhour', 
#                                           'fuel_stor_capacity_fuelunit'])    
#     return capacity_.groupby(['load_zone', 'technology'], as_index = False).agg('sum')

def _group_capacity(capacity_, techs_):
    return capacity_.loc[capacity_.technology.isin(techs_)].reset_index(drop = True)

# Grab data from databases for plotting energy trade
def _load_energy_exchange(scenarios_, path):

    dfs_ = []
    # Open connection: open database and grab meta-data
    for scenario in scenarios_:
        print(scenario)
        dir_name             = r'{}/{}'.format(path, scenario)
        import_export_table_ = pd.read_csv(dir_name + r'/results/imports_exports.csv')
        for load_zone in import_export_table_['load_zone'].unique():
            for period in import_export_table_['period'].unique():

                idx_                   = (import_export_table_['load_zone'] == load_zone) & (import_export_table_['period'] == period)
                import_export_table_p_ = import_export_table_.loc[idx_]
                
                imports_ = import_export_table_p_['timepoint_weight'] * import_export_table_p_['imports_mw']
                exports_ = import_export_table_p_['timepoint_weight'] * import_export_table_p_['exports_mw']
                
                imports = imports_[imports_ > 0.].sum() - exports_[exports_ < 0.].sum()
                exports = exports_[exports_ > 0.].sum() - imports_[imports_ < 0.].sum()
                total   = imports + exports
                net     = np.absolute(imports - exports)
                #imports = - imports
                
                dfs_.append([scenario, load_zone, period, imports, exports, total, net])
                
    dfs_ = pd.DataFrame(np.stack(dfs_).T, index = ['Scenario', 'Zone', 'Period', 'Imports', 'Exports', 'Total', 'Net']).T
    
    dfs_['Imports'] = dfs_['Imports'].astype(float)
    dfs_['Exports'] = dfs_['Exports'].astype(float)
    dfs_['Total']   = dfs_['Total'].astype(float)
    dfs_['Net']     = dfs_['Net'].astype(float)
    dfs_['Period']  = dfs_['Period'].astype(int)

    return dfs_

# Grab data from databases for plotting energy trade
def _load_energy_trading(scenarios_, path):

    dfs_ = []
    # Open connection: open database and grab meta-data
    for scenario in scenarios_:
        print(scenario)
        dir_name             = r'{}/{}'.format(path, scenario)
        import_export_table_ = pd.read_csv(dir_name + r'/results/imports_exports.csv')
        import_export_table_['exchange_mw']  = np.absolute(import_export_table_['timepoint_weight'] * import_export_table_['imports_mw'])
        import_export_table_['exchange_mw'] += np.absolute(import_export_table_['timepoint_weight'] * import_export_table_['exports_mw'])
        import_export_table_ = import_export_table_.drop(columns = ['load_zone', 
                                                                    'timepoint', 
                                                                    'timepoint_weight', 
                                                                    'net_imports_mw', 
                                                                    'number_of_hours_in_timepoint', 
                                                                    'imports_mw', 
                                                                    'exports_mw'])
        import_export_table_ = import_export_table_.groupby(['period']).sum()
        import_export_table_ = import_export_table_.reset_index()
        import_export_table_['scenario'] = scenario

        dfs_.append(import_export_table_)
    return pd.concat(dfs_).reset_index(drop = True)



# Grab data from databases for plotting energy dispatch and clean energy targets
def _load_dispatch(scen_labels_, path):

    def __merge_ed_and_tx(ed_, Tx_):

        df_  = ed_.groupby(['Scenario', 'Period', 'Zone'], as_index = False).agg({'Energy': 'sum'})
        df_  = pd.merge(df_, Tx_, on = ['Scenario', 'Period', 'Zone']).reset_index(drop = True)

        df_['Import'] += df_['Export']
        df_['Export']  = 0.
        # Caculate state-level curtailment and loses
        df_['Curtailment'] = df_['Load'] - df_['Energy'] - df_['Import']
        df_['Tx_Losses']   = - df_['Tx_Losses_fr'] - df_['Tx_Losses_to']
        # Caculate Load Shedding
        df_.loc[df_['Curtailment'] > 0., 'Shedding'] = df_.loc[df_['Curtailment'] > 0., 'Curtailment']
        df_.loc[df_['Curtailment'] > 0., 'Curtailment'] = 0.
        df_ = df_.fillna(0.)
        df_ = df_.drop(columns = ['Energy', 'Tx_Losses_to', 'Tx_Losses_fr', 'Energy', 'Load'])
        # Merge both dataframes
        dfs_     = []
        columns_ = ['Curtailment', 'Shedding', 'Import', 'Tx_Losses', 'Export']
        for column in columns_:
            df_p_               = df_.drop(columns = [i for i in columns_ if i != column])
            df_p_['Technology'] = column
            dfs_               += [df_p_.rename(columns = {column: 'Energy'})]

        return pd.concat([ed_, pd.concat(dfs_, axis = 0)], axis = 0).sort_values(by = ['Period']).reset_index(drop = True)

    # Load energy dispatch table and process data from database
    def __load_ed_from_csv(table_, zones_, scenario):

        periods_ = ed_table_['period'].unique()
        techs_   = ed_table_['technology'].unique()

        dispatch_ = []
        for tech, i_tech in zip(techs_, range(len(techs_))):
            for period, i_period in zip(periods_, range(len(periods_))):
                for zone, i_zone in zip(zones_, range(len(zones_))):
                    # Find specific row from database
                    if zone == 'India':
                        idx_ = (table_['period'] == period) & (table_['technology'] == tech)
                    else:
                        idx_ = (table_['period'] == period) & (table_['technology'] == tech) & (table_['load_zone'] == zone)

                    dispatch_ += [[scenario,
                                   period,
                                   tech,
                                   zone,
                                   np.sum(table_.loc[idx_, 'timepoint_weight']*table_.loc[idx_, 'power_mw'])]]

        return pd.DataFrame(np.array(dispatch_), columns = ['Scenario', 'Period', 'Technology', 'Zone', 'Energy'])

    # Load energy dispatch table and process data from database
    def __load_tx_loss_from_csv(table_, zones_, scenario):

        periods_ = table_['period'].unique()

        losses_ = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                # Find specific row from database
                if zone == 'India': idx_ = (table_['period'] == period)
                else:               idx_ = (table_['period'] == period) & (table_['lz_to'] == zone)

                losses_ += [[scenario,
                             period,
                             zone,
                             np.sum(table_.loc[idx_, 'timepoint_weight']*table_.loc[idx_, 'transmission_losses_lz_from']),
                             np.sum(table_.loc[idx_, 'timepoint_weight']*table_.loc[idx_, 'transmission_losses_lz_to'])]]

        return pd.DataFrame(np.array(losses_), columns = ['Scenario', 'Period', 'Zone', 'Tx_Losses_fr', 'Tx_Losses_to'])

    def __load_imports_and_exports_from_csv(table_, zones_, scenario):
        periods_ = table_['period'].unique()

        exchange_ = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                # Find specific row from database
                if zone == 'India':
                    imports = 0.
                    exports = 0.
                else:
                    state_exchange_ = table_.loc[table_['load_zone'] == zone].reset_index(drop = True)
                    idx_            = table_['period'] == period
                    aux_1_ = state_exchange_.loc[idx_, 'imports_mw']*state_exchange_.loc[idx_, 'timepoint_weight']
                    aux_2_ = state_exchange_.loc[idx_, 'exports_mw']*state_exchange_.loc[idx_, 'timepoint_weight']
                    imports = np.sum(aux_1_.loc[aux_1_ > 0.]) - np.sum(aux_2_.loc[aux_2_ < 0.])
                    exports = np.sum(aux_2_.loc[aux_2_ > 0.]) - np.sum(aux_1_.loc[aux_1_ < 0.])
                exchange_ += [[scenario, period, zone, imports, exports]]
        return pd.DataFrame(np.array(exchange_), columns = ['Scenario', 'Period', 'Zone', 'Import', 'Export'])

    # Load energy dispatch table and process data from database
    def __load_demand_from_csv(demand_table_, timepoints_table_, zones_, scenario):
        periods_ = timepoints_table_['period'].unique()
        demand_  = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                # Find specific row from database
                idx_ = timepoints_table_['period'] == period

                if zone == 'India':
                    state_demand_              = demand_table_.groupby('timepoint').agg({'load_mw': 'sum'})
                    state_demand_['timepoint'] = state_demand_.index
                    state_demand_              = state_demand_.reset_index(drop = True)
                else:
                    state_demand_ = demand_table_.loc[demand_table_['LOAD_ZONES'] == zone].reset_index(drop = True)

                demand_ += [[scenario,
                             period,
                             zone,
                             np.sum(state_demand_.loc[idx_, 'load_mw']*timepoints_table_.loc[idx_, 'timepoint_weight'])]]

        return pd.DataFrame(np.array(demand_), columns = ['Scenario', 'Period', 'Zone', 'Load'])

    scenarios_ = scen_labels_['scenario'].to_list()
    zones_     = scen_labels_['zone'].to_list()
    eds_       = []
    losses_    = []

    # Open connection: open database and grab meta-data
    for scen, i_scen in zip(scenarios_, range(len(scenarios_))):
        print(scen)
        dir_name             = r'{}/{}'.format(path, scen)
        ed_table_            = pd.read_csv(dir_name + r'/results/dispatch_all.csv')
        losses_table_        = pd.read_csv(dir_name + r'/results/transmission_operations.csv')
        import_export_table_ = pd.read_csv(dir_name + r'/results/imports_exports.csv')
        demand_table_        = pd.read_csv(dir_name + r'/inputs/load_mw.tab', sep = '\t', engine = 'python')
        timepoints_table_    = pd.read_csv(dir_name + r'/inputs/timepoints.tab', sep = '\t', engine = 'python')


        # Load energy dispatch from csv files
        zone = [zones_[i_scen]]

        # Load transmission losses from csv files
        tx_loss_ = __load_tx_loss_from_csv(losses_table_, zone, scen)

        # Imports and exports exchanges from csv files
        exchange_ = __load_imports_and_exports_from_csv(import_export_table_, zone, scen)

        # Load enregy curtailmenet from csv files
        demand_ = __load_demand_from_csv(demand_table_, timepoints_table_, zone, scen)
        df_     = pd.merge(exchange_, tx_loss_,  on = ['Scenario', 'Period', 'Zone']).reset_index(drop = True)

        losses_ += [pd.merge(df_, demand_,  on = ['Scenario', 'Period', 'Zone']).reset_index(drop = True)]
        eds_    += [__load_ed_from_csv(ed_table_, zone, scen)]

    eds_           = pd.concat(eds_, axis = 0).reset_index(drop = True)
    eds_['Energy'] = eds_['Energy'].astype(float)

    losses_                 = pd.concat(losses_, axis = 0).reset_index(drop = True)
    losses_['Export']       = losses_['Export'].astype(float)
    losses_['Import']       = losses_['Import'].astype(float)
    losses_['Tx_Losses_to'] = losses_['Tx_Losses_to'].astype(float)
    losses_['Tx_Losses_fr'] = losses_['Tx_Losses_fr'].astype(float)
    losses_['Load']         = losses_['Load'].astype(float)

    return __merge_ed_and_tx(eds_, losses_).sort_values(by = ['Scenario', 'Period', 'Technology', 'Zone']).reset_index(drop = True)



def _merge_dispatch_and_tx_losses(dispatch_, Tx_):
    
    tx_losses_p_ = Tx_.copy()
    periods_     = tx_losses_p_['Period'].unique()
    scenarios_   = tx_losses_p_['Scenario'].unique()

    dfs_ = []
    for period in periods_:
        for scenario in scenarios_:
            idx_ = (tx_losses_p_['Scenario'] == scenario) & (tx_losses_p_['Period'] == period)
    
            dfs_ += [[scenario, 
                      period, 
                      'Import', 
                      tx_losses_p_.loc[idx_, 'Zone'].to_numpy()[0],
                      tx_losses_p_.loc[idx_, 'Import'].to_numpy()[0]]]
    
            dfs_ += [[scenario, 
                      period, 
                      'Export', 
                      tx_losses_p_.loc[idx_, 'Zone'].to_numpy()[0],
                      tx_losses_p_.loc[idx_, 'Export'].to_numpy()[0]]]
    
            dfs_ += [[scenario, 
                      period, 
                      'Tx_Losses', 
                      tx_losses_p_.loc[idx_, 'Zone'].to_numpy()[0],
                      -tx_losses_p_.loc[idx_, 'Tx_Losses_to'].to_numpy()[0]]]
            
            dfs_ += [[scenario, 
                      period, 
                      'Load', 
                      tx_losses_p_.loc[idx_, 'Zone'].to_numpy()[0],
                      tx_losses_p_.loc[idx_, 'Load'].to_numpy()[0]]]
            
    dfs_ = pd.DataFrame(np.array(dfs_), columns = ['Scenario', 'Period', 'Technology', 'Zone', 'Energy'])

    return pd.concat([dispatch_, dfs_], axis = 0).reset_index(drop = True)


def _group_dispatch_technologies_by_zone_and_date(df_, tech_labels_):
    groups_ = tech_labels_['group'].unique()
    for group in groups_:
        df_.loc[df_['technology'].isin(tech_labels_.loc[tech_labels_['group'] == group, 'technology'].to_list()), 'technology'] = group
    return df_.groupby(['load_zone', 'period', 'month', 'day', 'interval', 'technology', 'scenario']).sum().reset_index(drop = False)


# # Grab data from databases for plotting new and existing capacity
# def _load_capacity_production(scen_labels_, path):

#     scenarios_ = scen_labels_['scenario'].unique()
#     zones_     = scen_labels_['zone'].unique()
#     dfs_       = []

#     # Open connection: open database and grab meta-data
#     for scenario in scenarios_:
#         print(scenario)
#         dir_name        = r'{}/{}'.format(path, scenario)
#         capacity_table_ = pd.read_csv(dir_name + r'/1/results/project_period.csv', low_memory = False)
#         capacity_table_ = capacity_table_[['technology', 'period', 'load_zone', 'capacity_mw', 'energy_capacity_mwh']]
#         capacity_table_ = capacity_table_.groupby(['technology', 'period', 'load_zone'], as_index = False).sum()
#         capacity_table_ = capacity_table_.rename(columns = {'period': 'Period', 
#                                                             'load_zone': 'Zone', 
#                                                             'capacity_mw': 'Power', 
#                                                             'energy_capacity_mwh': 'Energy', 
#                                                             'technology': 'Technology'})
#         capacity_table_['Status']   = 'new'
#         capacity_table_['Scenario'] = scenario

#     return capacity_table_[['Scenario', 'Period', 'Technology', 'Zone', 'Status', 'Power', 'Energy']]

def _processing_energy_dispatch(scenarios_, path, model):
    
    ed_p_ = []
    for scenario in scenarios_['scenario']:
        print(scenario)
        
        dir_name = r'{}/{}'.format(path, scenario)

        if model == 'production':
            ed_   = []
            load_ = []
            for folder in next(os.walk(dir_name))[1]:
                ed_.append(pd.read_csv(dir_name + f'/{folder}/results/project_timepoint.csv', low_memory = False))
                load_.append(pd.read_csv(dir_name + f'/{folder}/inputs/load_mw.tab', sep = '\t', engine = 'python'))
            ed_   = pd.concat(ed_, axis = 0).reset_index(drop = True)
            load_ = pd.concat(load_, axis = 0).reset_index(drop = True)
            
        elif model == 'capex':
            ed_   = pd.read_csv(dir_name + f'/results/project_timepoint.csv', low_memory = False)
            load_ = pd.read_csv(dir_name + f'/inputs/load_mw.tab', sep = '\t', engine = 'python') 
            
        # Define or rename missing columns 
        load_ = load_.rename(columns = {'LOAD_ZONES': 'load_zone', 'load_mw': 'power_mw'})

        load_['technology'] = 'Load'

        ed_ = ed_[['load_zone', 'technology', 'timepoint', 'power_mw']]
        ed_ = ed_.groupby(['load_zone', 'technology', 'timepoint']).sum().reset_index(drop = False)
        ed_ = pd.concat([ed_, load_]).reset_index(drop = True)
        ed_['scenario'] = scenario
        ed_p_.append(ed_)
        
    ed_ = pd.concat(ed_p_, axis = 0).reset_index(drop = True)

    try:
        ed_ = _processing_transmission(ed_, path)
    except:
        pass
        
    return ed_

def _processing_transmission(ed_, path):
    ed_p_ = ed_.copy()

    df_ = []
    for scenario in ed_['scenario'].unique():

        dir_name = r'{}/{}'.format(path, scenario)

        tx_ = pd.read_csv(dir_name + f'/results/transmission_timepoint.csv', low_memory = False)

        for zone in ed_['load_zone'].unique():
            tx_p_ = tx_.copy()
            
            idx_   = tx_p_['load_zone_to'] == zone
            tx_p_  = tx_p_.loc[idx_, ['load_zone_to', 'timepoint', 'transmission_flow_mw', 'transmission_losses_lz_to']].reset_index(drop = True)
            tx_p_  = tx_p_.rename(columns = {'load_zone_to': 'load_zone'})
            
            tx_pp_               = tx_p_.copy()
            tx_pp_['technology'] = 'Tx_Losses'
            tx_pp_               = tx_pp_.rename(columns = {'transmission_losses_lz_to': 'power_mw'})
            tx_pp_['power_mw']   = - tx_pp_['power_mw']
            tx_pp_               = tx_pp_.drop(columns = ['transmission_flow_mw'])
            
            tx_ppp_                                           = tx_p_.copy()
            tx_ppp_['technology']                             = 'Import'
            tx_ppp_                                           = tx_ppp_.rename(columns = {'transmission_flow_mw': 'power_mw'})
            tx_ppp_                                           = tx_ppp_.drop(columns = ['transmission_losses_lz_to'])
            tx_ppp_.loc[tx_ppp_['power_mw'] < 0., 'power_mw'] = 0.

            tx_pppp_                                            = tx_p_.copy()
            tx_pppp_['technology']                              = 'Export'
            tx_pppp_                                            = tx_pppp_.rename(columns = {'transmission_flow_mw': 'power_mw'})
            tx_pppp_                                            = tx_pppp_.drop(columns = ['transmission_losses_lz_to'])
            tx_pppp_.loc[tx_pppp_['power_mw'] > 0., 'power_mw'] = 0.

            tx_p_             = pd.concat([tx_pp_, tx_ppp_, tx_pppp_], axis = 0).reset_index(drop = True)
            tx_p_['scenario'] = scenario
            df_ += [tx_p_]    
            
    df_ = pd.concat(df_, axis = 0).reset_index(drop = True)
    return pd.concat([ed_, df_]).reset_index(drop = True)


def _group_dispatch_technologies_by_zone_and_date_production(df_, tech_labels_):
    groups_ = tech_labels_['group'].unique()
    for group in groups_:
        df_.loc[df_['technology'].isin(tech_labels_.loc[tech_labels_['group'] == group, 'technology'].to_list()), 'technology'] = group
    return df_.groupby(['load_zone', 'technology', 'scenario', 'timepoint']).sum().reset_index(drop = False)


# Grab data from databases for plotting new and existing capacity
def _load_capacity(scen_labels_, path, gp_model):

    # Load project capacity table and process them from database
    def __load_new_and_existing_csv(capacity_, projects_, zones_, scenario):

        capacity_['capacity_mw'] = capacity_['capacity_mw'].astype(float)
        capacity_['Status']      = 'new'

        for project in projects_['project'].unique():
            if capacity_.loc[(capacity_['project'] == project) & (capacity_['period'] == 2020), 'capacity_mw'].to_numpy()[0] != 0.:
                capacity_.loc[capacity_['project'] == project, 'Status'] = 'existing'

        periods_ = capacity_['period'].unique()
        techs_   = capacity_['technology'].unique()
        status_  = capacity_['Status'].unique()

        capacity_all_ = []

        for tech, i_tech in zip(techs_, range(len(techs_))):
            for period, i_period in zip(periods_, range(len(periods_))):
                for zone, i_zone in zip(zones_, range(len(zones_))):
                    for status, i_status in zip(status_, range(len(status_))):

                        # Find specific row from database
                        if zone == 'India':
                            idx_ = (capacity_['period'] == period) & (capacity_['technology'] == tech) & (capacity_['Status'] == status)
                        else:
                            idx_ = (capacity_['period'] == period) & (capacity_['technology'] == tech) & (capacity_['Status'] == status)

                        capacity_all_ += [[scenario,
                                           period,
                                           tech,
                                           zone,
                                           status,
                                           np.sum(capacity_.loc[idx_, 'capacity_mw']),
                                           np.sum(capacity_.loc[idx_, 'energy_capacity_mwh'])]]

        return pd.DataFrame(np.array(capacity_all_), columns = ['Scenario', 'Period', 'Technology', 'Zone', 'Status', 'Power', 'Energy']).sort_values(by = ['Scenario', 'Period', 'Technology', 'Zone']).reset_index(drop = True)

    scenarios_ = scen_labels_['scenario'].unique()
    zones_     = scen_labels_['zone'].unique()
    dfs_       = []

    # Open connection: open database and grab meta-data
    for scenario in scenarios_:
        print(scenario)
        dir_name        = r'{}/{}'.format(path, scenario)

        if gp_model == 'production':
            capacity_table_ = pd.read_csv(dir_name + r'/1/results/project_period.csv', low_memory = False)
            capacity_table_ = capacity_table_[['technology', 'period', 'load_zone', 'capacity_mw', 'energy_capacity_mwh']]
            capacity_table_ = capacity_table_.groupby(['technology', 'period', 'load_zone'], as_index = False).sum()
            capacity_table_ = capacity_table_.rename(columns = {'period': 'Period', 
                                                                'load_zone': 'Zone', 
                                                                'capacity_mw': 'Power', 
                                                                'energy_capacity_mwh': 'Energy', 
                                                                'technology': 'Technology'})
            capacity_table_['Status']   = 'new'
            capacity_table_['Scenario'] = scenario
            dfs_.append(capacity_table_)

        
        elif gp_model == 'capex':
            capacity_table_ = pd.read_csv(dir_name + r'/results/project_period.csv', low_memory = False)
            spec_table_     = pd.read_csv(dir_name + r'/inputs/spec_capacity_period_params.tab', sep = '\t', engine = 'python')
            project_table_  = pd.read_csv(dir_name + r'/inputs/projects.tab', sep = '\t', engine = 'python')
            project_table_  = project_table_[project_table_['project'].isin(pd.unique(spec_table_['project']))]
            # Load specified capacity from csv files
            dfs_.append(__load_new_and_existing_csv(capacity_table_, project_table_, zones_, scenario))

    dfs_           = pd.concat(dfs_, axis = 0).reset_index(drop = True)
    dfs_['Power']  = dfs_['Power'].astype(float)
    dfs_['Energy'] = dfs_['Energy'].astype(float)
    dfs_['Period'] = dfs_['Period'].astype(int)
    return dfs_[['Scenario', 'Period', 'Technology', 'Zone', 'Status', 'Power', 'Energy']]


# Grab data from databases for plotting energy dispatch and clean energy targets
def _load_energy_dispatch(scen_labels_, path, gp_model):

    # Load energy dispatch table and process data from database
    def __load_ed_from_csv(ed_, zones_, scenario):
        
        periods_  = ed_['period'].unique()
        techs_    = ed_['technology'].unique()
        dispatch_ = []
        for tech, i_tech in zip(techs_, range(len(techs_))):
            for period, i_period in zip(periods_, range(len(periods_))):
                for zone, i_zone in zip(zones_, range(len(zones_))):
                    # Find specific row from database 
                    if zone == 'all_nodes':
                        idx_ = (ed_['period'] == period) & (ed_['technology'] == tech)
                    else:
                        idx_ = (ed_['period'] == period) & (ed_['technology'] == tech) & (ed_['load_zone'] == zone)
                                                
                    dispatch_ += [[scenario, 
                                   period, 
                                   tech, 
                                   zone, 
                                   np.sum(ed_.loc[idx_, 'number_of_hours_in_timepoint']*ed_.loc[idx_, 'timepoint_weight']*ed_.loc[idx_, 'power_mw'])]]

        return pd.DataFrame(np.array(dispatch_), columns = ['Scenario', 'Period', 'Technology', 'Zone', 'Energy'])

    # Load energy dispatch table and process data from database
    def __load_demand_from_csv(table_, zones_, scenario):
        
        periods_ = table_['period'].unique()
        demand_  = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                # Find specific row from database 
                if zone == 'all_nodes':
                    idx_ = (table_['period'] == period)
                else:
                    idx_ = (table_['period'] == period) & (table_['load_zone'] == zone)

                demand_ += [[scenario, 
                             period, 
                             'Shedding', 
                             zone, 
                             np.sum(table_.loc[idx_, 'number_of_hours_in_timepoint']*table_.loc[idx_, 'timepoint_weight']*table_.loc[idx_, 'unserved_energy_mw'])]]

                demand_ += [[scenario, 
                             period, 
                             'Curtailment', 
                             zone, 
                             np.sum(table_.loc[idx_, 'number_of_hours_in_timepoint']*table_.loc[idx_, 'timepoint_weight']*table_.loc[idx_, 'overgeneration_mw'])]]

        return pd.DataFrame(np.array(demand_), columns = ['Scenario', 'Period', 'Technology', 'Zone', 'Energy'])

    def _load_tx_losses_from_csv(table_, zones_, scenario):
        
        periods_ = table_['period'].unique()
        df_  = []
        for period, i_period in zip(periods_, range(len(periods_))):
            for zone, i_zone in zip(zones_, range(len(zones_))):
                # Find specific row from database 
                if zone == 'all_nodes':
                    idx_ = (table_['period'] == period)
                else:
                    idx_ = (table_['period'] == period) & (table_['load_zone_to'] == zone)

                df_ += [[scenario, period, 'Tx_Losses', zone, 
                         -np.sum(table_.loc[idx_, 'number_of_hours_in_timepoint']*table_.loc[idx_, 'timepoint_weight']*table_.loc[idx_, 'transmission_losses_lz_to'])]]

                idx_ = idx_ & (table_.loc[idx_, 'transmission_flow_mw'] > 0)
                df_ += [[scenario, period, 'Import', zone, 
                         np.sum(table_.loc[idx_, 'number_of_hours_in_timepoint']*table_.loc[idx_, 'timepoint_weight']*table_.loc[idx_, 'transmission_flow_mw'])]]

                idx_ = idx_ & (table_.loc[idx_, 'transmission_flow_mw'] < 0)
                df_ += [[scenario, period, 'Export', zone, 
                         np.sum(table_.loc[idx_, 'number_of_hours_in_timepoint']*table_.loc[idx_, 'timepoint_weight']*table_.loc[idx_, 'transmission_flow_mw'])]]

        return pd.DataFrame(np.array(df_), columns = ['Scenario', 'Period', 'Technology', 'Zone', 'Energy'])
        
    scenarios_ = scen_labels_['scenario'].unique()
    zones_     = scen_labels_['zone'].unique()
    dfs_       = []
    # Open connection: open database and grab meta-data
    for scenario in scenarios_:
        print(scenario)
        dir_name = r'{}/{}'.format(path, scenario)

        if gp_model == 'production':
            ed_     = []
            demand_ = []
            for folder in next(os.walk(dir_name))[1]:
                ed_.append(pd.read_csv(dir_name + f'/{folder}/results/project_timepoint.csv', low_memory = False))
                demand_.append(pd.read_csv(dir_name + f'/{folder}/results/system_load_zone_timepoint.csv', low_memory = False))
            ed_     = pd.concat(ed_, axis = 0).reset_index(drop = True)
            demand_ = pd.concat(demand_, axis = 0).reset_index(drop = True)
            
        elif gp_model == 'capex':
            ed_        = pd.read_csv(dir_name + f'/results/project_timepoint.csv', low_memory = False)
            demand_    = pd.read_csv(dir_name + f'/results/system_load_zone_timepoint.csv', low_memory = False)

            try:
                tx_losses_ = pd.read_csv(dir_name + f'/results/transmission_timepoint.csv', low_memory = False)
                dfs_      += [_load_tx_losses_from_csv(tx_losses_, zones_, scenario)]
            except:
                pass

        
        dfs_ += [__load_ed_from_csv(ed_, zones_, scenario)]
        dfs_ += [__load_demand_from_csv(demand_, zones_, scenario)]

    dfs_           = pd.concat(dfs_, axis = 0).reset_index(drop = True)
    dfs_['Energy'] = dfs_['Energy'].astype(float)

    return dfs_

__all__ = ['_load_capacity',
           '_group_capacity_technologies', 
           '_load_new_and_existing_capacity_by_zone',
           '_group_capacity_technologies_by_zone',
           '_group_dispatch_technologies_by_zone',
           '_load_energy_dispatch', 
           '_load_energy_transmission', 
           '_merge_ed_and_tx',
           '_group_dispatch_technologies', 
           '_load_RPS', 
           '_load_system_cost', 
           '_load_technology_costs', 
           '_group_technology_costs', 
           '_load_GHG_emissions', 
           '_load_energy_flow_by_scenario_and_period',
           '_load_transmission_capacity_by_scenario_and_period',
           '_GHG_emissions_intensity',
           '_group_capacity', 
           '_load_energy_exchange',
           '_load_energy_trading',
           '_merge_dispatch_and_tx_losses', 
           '_processing_energy_dispatch', 
           '_group_dispatch_technologies_by_zone_and_date', 
           '_group_dispatch_technologies_by_zone_and_date_production']
