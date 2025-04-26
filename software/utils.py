import os, string

import pandas as pd
import numpy as np

# Grab data from databases for plotting energy dispatch and clean energy targets
def _load_dispatch_by_zone(scen_labels_):

    # Load energy dispatch table and process data from database
    def __load_dispatch_from_csv(df_, scenario):
        
        df_['power_mw'] = df_['number_of_hours_in_timepoint'] * df_['timepoint_weight'] * df_['power_mw']

        df_ = df_[['period', 'technology', 'load_zone', 'power_mw']]
        df_ = df_.groupby(['period', 
                           'technology', 
                           'load_zone']).agg({'power_mw': 
                                              'sum'}).reset_index(drop = False)
        
        df_['scenario'] = scenario
                
        return df_

    dfs_ = []
    # Open connection: open database and grab meta-data
    for scen, path in zip(scen_labels_['scenario'], scen_labels_['path']):
        print(scen, path)
        
        dir_name  = r'{}/{}'.format(path, scen)
        dispatch_ = pd.read_csv(dir_name + f'/results/project_timepoint.csv', 
                                low_memory = False)
        
        dfs_ += [__load_dispatch_from_csv(dispatch_, scen)]

    return pd.concat(dfs_, axis = 0).reset_index(drop = True)


def _load_demand_by_zone(scen_labels_):
    
    # Load energy dispatch table and process data from database
    def __load_demand_from_csv(df_, scenario):
        
        df_['overgeneration_mw'] = df_['number_of_hours_in_timepoint'] * df_['timepoint_weight'] * df_['overgeneration_mw']
        
        df_['unserved_energy_mw'] = df_['number_of_hours_in_timepoint'] * df_['timepoint_weight'] * df_['unserved_energy_mw']
        
        df_['power_mw'] = df_['number_of_hours_in_timepoint'] * df_['timepoint_weight'] * df_['static_load_mw']

        df_1_ = df_[['period', 
                     'load_zone', 
                     'overgeneration_mw']].copy()
        
        df_1_['technology'] = 'Curtailment'   
        
        df_1_ = df_1_.rename(columns = {'overgeneration_mw': 'power_mw'})
        df_1_ = df_1_.groupby(['period', 
                               'technology', 
                               'load_zone']).agg({'power_mw': 
                                                  'sum'}).reset_index(drop = False)

        df_2_ = df_[['period', 
                     'load_zone',
                     'unserved_energy_mw']].copy()
        
        df_2_['technology'] = 'Shedding'           
        
        df_2_ = df_2_.rename(columns = {'unserved_energy_mw': 'power_mw'})
        df_2_ = df_2_.groupby(['period', 
                               'technology', 
                               'load_zone']).agg({'power_mw': 
                                                  'sum'}).reset_index(drop = False)
        df_3_ = df_[['period', 
                     'load_zone', 
                     'power_mw']].copy()
        
        df_3_['technology'] = 'Demand'   
        
        df_3_ = df_3_.groupby(['period', 
                               'technology',
                               'load_zone']).agg({'power_mw': 
                                                  'sum'}).reset_index(drop = False)
        
        df_4_ = df_[['period', 
                     'load_zone', 
                     'total_power_mw']].copy()
        
        df_4_['technology'] = 'Peak'   
        
        df_4_ = df_4_.rename(columns = {'total_power_mw': 'power_mw'})
        df_4_ = df_4_.groupby(['period', 
                               'technology', 
                               'load_zone']).agg({'power_mw': 
                                                  'max'}).reset_index(drop = False)
        
        df_ = pd.concat([df_1_, df_2_, df_3_, df_4_], axis = 0).reset_index(drop = True)

        df_['scenario'] = scenario
                                  
        return df_
    
    dfs_ = []
    # Open connection: open database and grab meta-data
    for scen, path in zip(scen_labels_['scenario'], scen_labels_['path']):
        print(scen, path)
        
        dir_name = r'{}/{}'.format(path, scen)
        demand_  = pd.read_csv(dir_name + f'/results/system_load_zone_timepoint.csv', 
                               low_memory = False)
        
        dfs_ += [__load_demand_from_csv(demand_, scen)]

    return pd.concat(dfs_, axis = 0).reset_index(drop = True)

# Grab data from databases for plotting energy dispatch and clean energy targets
def _load_transmission_by_zone(scen_labels_):

    def __load_tx_losses_from_csv(df_, scenario):
        
        df_['transmission_losses_lz_to']= - df_['number_of_hours_in_timepoint'] * df_['timepoint_weight'] * df_['transmission_losses_lz_to'] 
        
        df_['transmission_losses_lz_from'] = - df_['number_of_hours_in_timepoint'] * df_['timepoint_weight'] * df_['transmission_losses_lz_from']
        
        df_['transmission_flow_mw'] = df_['number_of_hours_in_timepoint'] * df_['timepoint_weight'] * df_['transmission_flow_mw']

        df_1_ = df_[['period', 
                     'load_zone_to', 
                     'transmission_losses_lz_to']].copy()
        
        df_1_['technology'] = 'Transmission Losses'
        
        df_1_ = df_1_.rename(columns = {'transmission_losses_lz_to': 'power_mw', 
                                        'load_zone_to': 'load_zone'})

        df_2_ = df_[['period', 
                     'load_zone_from',
                     'transmission_losses_lz_from']].copy()
        
        df_2_['technology'] = 'Transmission Losses'
        
        df_2_ = df_2_.rename(columns = {'transmission_losses_lz_from': 'power_mw',
                                        'load_zone_from': 'load_zone'})
        
        df_3_ = df_[['period', 'load_zone_to', 'transmission_flow_mw']].copy()
        df_3_ = df_3_.rename(columns = {'transmission_flow_mw': 'power_mw',
                                        'load_zone_to': 'load_zone'})

        df_3_.loc[df_3_['power_mw'] >= 0., 'technology'] = 'Import'
        df_3_.loc[df_3_['power_mw'] < 0., 'technology']  = 'Export'
        
        df_4_ = df_[['period', 'load_zone_from', 'transmission_flow_mw']].copy()
        df_4_ = df_4_.rename(columns = {'transmission_flow_mw': 'power_mw',
                                        'load_zone_from': 'load_zone'})

        df_4_['power_mw'] = - df_4_['power_mw']

        df_4_.loc[df_4_['power_mw'] >= 0., 'technology'] = 'Import'
        df_4_.loc[df_4_['power_mw'] < 0., 'technology']  = 'Export'
        
        df_ = pd.concat([df_1_, df_2_, df_3_, df_4_], axis = 0)
        
        df_ = df_.groupby(['period', 
                           'technology', 
                           'load_zone']).agg({'power_mw':
                                              'sum'}).reset_index(drop = False)

        df_['scenario'] = scenario
        
        return df_

    dfs_ = []
    # Open connection: open database and grab meta-data
    for scen, path in zip(scen_labels_['scenario'], scen_labels_['path']):
        print(scen, path)
        
        dir_name   = r'{}/{}'.format(path, scen)
        tx_losses_ = pd.read_csv(dir_name + f'/results/transmission_timepoint.csv', 
                                 low_memory = False)
        
        dfs_ += [__load_tx_losses_from_csv(tx_losses_, scen)]

    return pd.concat(dfs_, axis = 0).reset_index(drop = True)

# Grab data from databases for plotting new and existing capacity
def _load_capacity_by_zone(scen_labels_):

    # Load project capacity table and process them from database
    def __load_new_and_existing_csv(df_, scenario):

        df_['capacity_mw'] = df_['capacity_mw'].astype(float)
        df_['status']      = 'new'
        df_                = df_[['project', 
                                  'period', 
                                  'technology',
                                  'load_zone', 
                                  'status', 
                                  'capacity_mw', 
                                  'energy_capacity_mwh']]

        idx_  = (df_['period'] == 2020) & (df_['capacity_mw'] != 0.)
        
        df_.loc[capacity_['project'].isin(df_.loc[idx_, 'project'].unique()), 
                'status'] = 'existing'
        
        df_ = df_.groupby(['period', 
                           'technology', 
                           'load_zone', 
                           'status']).agg({'capacity_mw': 'sum', 
                                           'energy_capacity_mwh': 'sum'})

        df_ = df_.reset_index(drop = False).rename(columns = {'energy_capacity_mwh':
                                                              'capacity_mwh'})

        df_['scenario'] = scenario

        return df_
    
    dfs_ = []
    # Open connection: open database and grab meta-data
    for scen, path in zip(scen_labels_['scenario'],  scen_labels_['path']):
        print(scen, path)
        dir_name  = r'{}/{}'.format(path, scen)
        capacity_ = pd.read_csv(dir_name + r'/results/project_period.csv', 
                                low_memory = False)
        df_       = __load_new_and_existing_csv(capacity_, scen)
        
        # Load specified capacity from csv files
        dfs_.append(df_)

    return pd.concat(dfs_, axis = 0).reset_index(drop = True)

def _group_capacity_technologies_by_zone(capacity_, tech_labels_):

    for group in tech_labels_['group'].unique():
        idx_ = capacity_['technology'].isin(tech_labels_.loc[tech_labels_['group'] == group, 'technology'])
        capacity_.loc[idx_, 'technology'] = group
        
    capacity_ = capacity_.groupby(['period', 
                                   'technology', 
                                   'load_zone', 
                                   'status', 
                                   'scenario']).agg({'capacity_mw': 'sum', 
                                                     'capacity_mwh': 'sum'})

    return capacity_.reset_index(drop = False)

def _group_dispatch_technologies_by_zone(df_, tech_labels_):

    for group in tech_labels_['group'].unique():
        idx_ = df_['technology'].isin(tech_labels_.loc[tech_labels_['group'] == group, 'technology'])
        df_.loc[idx_, 'technology'] = group
        
    df_ = df_.groupby(['period', 
                       'technology', 
                       'load_zone', 
                       'scenario']).agg({'power_mw': 'sum'})

    return df_.reset_index(drop = False)

