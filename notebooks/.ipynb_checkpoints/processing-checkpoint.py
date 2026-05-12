import os

import pandas as pd
import numpy as np
import itertools
import geopandas as gpd

def _group_cost_by_technology(df_1_, df_2_, scen_labels_):

    columns_ = ['period', 'technology', 'scenario', 'load_zone']
    
    dfs_1_ = []
    dfs_2_ = []
    # Open connection: open database and grab metadata
    for scen, zone in zip(scen_labels_['scenario'], scen_labels_['zone']):
        
        df_1_p_ = df_1_.loc[df_1_['scenario'] == scen].copy()
        df_2_p_ = df_2_.loc[df_2_['scenario'] == scen].copy()

        idx_1_ = df_1_p_['load_zone'] == zone
        idx_2_ = df_2_p_['load_zone'] == zone

        if idx_1_.sum() == 0.:
            df_1_p_['load_zone'] = 'all'
            df_2_p_['load_zone'] = 'all'
        else:
            df_1_p_ = df_1_p_.loc[idx_].reset_index(drop = True)
            df_2_p_ = df_2_p_.loc[idx_].reset_index(drop = True)

        dfs_1_.append(df_1_p_.groupby(columns_).sum().reset_index(drop = False))
        dfs_2_.append(df_2_p_.groupby(columns_).sum().reset_index(drop = False))

    df_1_ = pd.concat(dfs_1_, axis = 0).reset_index(drop = True)
    df_2_ = pd.concat(dfs_2_, axis = 0).reset_index(drop = True)

    df_1_['period']        = df_1_['period'].astype(int)
    df_1_['fixed_cost']    = df_1_['fixed_cost'].astype(float)
    df_1_['variable_cost'] = df_1_['variable_cost'].astype(float)

    df_2_['period']  = df_2_['period'].astype(int)
    df_2_['load_mw'] = df_2_['load_mw'].astype(float)
    
    return df_1_, df_2_

def _group_technology(df_, tech_labels_):

    for group in tech_labels_['group'].unique():
        df_.loc[df_['technology'].isin(tech_labels_.loc[
                                       tech_labels_['group'] == group, 'technology']), 'technology'] = group
        
    df_ = df_.groupby(['period', 
                       'technology', 
                       'load_zone', 
                       'scenario']).agg({'variable_cost': 'sum', 
                                         'fixed_cost': 'sum'})

    return df_.reset_index(drop = False)
    

def _group_emissions_by_zone(df_, scen_labels_, 
                             columns_ = ['period', 'scenario', 'load_zone']):
    
    dfs_ = []
    # Open connection: open database and grab metadata
    for scen, zone in zip(scen_labels_['scenario'], 
                          scen_labels_['zone']):
        
        df_p_ = df_.loc[df_['scenario'] == scen].copy()
        
        idx_ = df_p_['load_zone'] == zone
        
        if idx_.sum() == 0.:
            df_p_['load_zone'] = 'all'
        else:
            df_p_ = df_p_.loc[idx_].reset_index(drop = True)
        
        dfs_.append(df_p_.groupby(columns_).sum().reset_index(drop = False))
        
    df_                          = pd.concat(dfs_, axis = 0).reset_index(drop = True)
    df_['period']                = df_['period'].astype(int)
    df_['carbon_emissions_tons'] = df_['carbon_emissions_tons'].astype(float)
    df_['load_mw']               = df_['load_mw'].astype(float)

    return df_

def _group_clean_energy_by_zone(df_, scen_labels_, columns_ = ['period', 'scenario', 'technology', 'load_zone']):
    
    dfs_ = []
    # Open connection: open database and grab metadata
    for scen, zone in zip(scen_labels_['scenario'], scen_labels_['zone']):
        
        df_p_ = df_.loc[df_['scenario'] == scen].copy()
        
        idx_ = df_p_['load_zone'] == zone
        
        if idx_.sum() == 0.:
            df_p_['load_zone'] = 'all'
        else:
            df_p_ = df_p_.loc[idx_].reset_index(drop = True)
        
        dfs_.append(df_p_.groupby(columns_).sum().reset_index(drop = False))
        
    df_             = pd.concat(dfs_, axis = 0).reset_index(drop = True)
    df_['period']   = df_['period'].astype(int)
    df_['power_mw'] = df_['power_mw'].astype(float)

    return df_


def _group_cost_by_zone(df_1_, df_2_, scen_labels_, columns_ = ['period', 'scenario', 'load_zone']):
    
    dfs_1_ = []
    dfs_2_ = []

    # Open connection: open database and grab metadata
    for scen, zone in zip(scen_labels_['scenario'], scen_labels_['zone']):
        
        df_1_p_ = df_1_.loc[df_1_['scenario'] == scen].copy()
        df_2_p_ = df_2_.loc[df_2_['scenario'] == scen].copy()

        idx_ = df_1_p_['load_zone'] == zone
        
        if idx_.sum() == 0.:
            df_1_p_['load_zone'] = 'all'
            df_2_p_['load_zone'] = 'all'

        else:
            df_1_p_ = df_1_p_.loc[idx_].reset_index(drop = True)
            df_2_p_ = df_2_p_.loc[idx_].reset_index(drop = True)

        dfs_1_.append(df_1_p_.groupby(columns_).sum().reset_index(drop = False))
        dfs_2_.append(df_2_p_.groupby(columns_).sum().reset_index(drop = False))

    dfs_1_ = pd.concat(dfs_1_, axis = 0).reset_index(drop = True)
    dfs_2_ = pd.concat(dfs_2_, axis = 0).reset_index(drop = True)

    dfs_1_['period']        = dfs_1_['period'].astype(int)
    dfs_2_['load_mw']       = dfs_2_['load_mw'].astype(float)
    dfs_1_['fixed_cost']    = dfs_1_['fixed_cost'].astype(float)
    dfs_1_['variable_cost'] = dfs_1_['variable_cost'].astype(float)

    return dfs_1_, dfs_2_


def _group_capacity_by_zone(df_, scen_labels_, columns_ = ['period', 
                                                           'technology', 
                                                           'scenario', 
                                                           'load_zone', 
                                                           'status']):
    
    dfs_ = []
    # Open connection: open database and grab meta-data
    for scen, zone in zip(scen_labels_['scenario'], scen_labels_['zone']):
        
        df_p_ = df_.loc[df_['scenario'] == scen].copy()
        
        idx_ = df_p_['load_zone'] == zone
        
        if idx_.sum() == 0.:
            df_p_['load_zone'] = 'all'
        else:
            df_p_ = df_p_.loc[idx_].reset_index(drop = True)
        
        dfs_.append(df_p_.groupby(columns_).sum().reset_index(drop = False))
        
    df_                 = pd.concat(dfs_, axis = 0).reset_index(drop = True)
    df_['period']       = df_['period'].astype(int)
    df_['capacity_mw']  = df_['capacity_mw'].astype(float)
    df_['capacity_mwh'] = df_['capacity_mwh'].astype(float)

    return df_

def _group_capacity_by_technology(capacity_, tech_labels_):

    for group in tech_labels_['group'].unique():
        capacity_.loc[capacity_['technology'].isin(tech_labels_.loc[tech_labels_['group'] == group, 'technology']), 'technology'] = group
        
    capacity_ = capacity_.groupby(['period', 
                                   'technology', 
                                   'load_zone', 
                                   'status', 
                                   'scenario']).agg({'capacity_mw': 'sum', 
                                                     'capacity_mwh': 'sum'})

    return capacity_.reset_index(drop = False)

def _group_dispatch_by_technology(df_, tech_labels_):

    for group in tech_labels_['group'].unique():
        df_.loc[df_['technology'].isin(tech_labels_.loc[tech_labels_['group'] == group, 'technology']), 'technology'] = group
        
    df_ = df_.groupby(['period', 
                       'technology', 
                       'load_zone', 
                       'scenario']).agg({'power_mw': 'sum'})

    return df_.reset_index(drop = False)

def _save_summary_csv(df_, path, file_name):
    df_['system_cost'].to_csv(path + '/' + file_name.format('system_cost'), index = False)
    df_['emissions'].to_csv(path + '/' + file_name.format('emissions'), index = False)
    df_['clean_energy'].to_csv(path + '/' + file_name.format('clean_energy'), index = False)
    
def _save_technology_cost_csv(df_, path, file_name):
    df_ = df_['tech_cost'].drop(columns = ['load_zone'])
    df_.to_csv(path + '/' + file_name, index = False)

def _save_technology_capacity_csv(df_1_, df_2_, load_zones_, path, file_name):
    
    df_ = df_1_.copy()

    for scenario, label in zip(df_2_['scenario'], df_2_['label']):
        df_.loc[df_['scenario'] == scenario, 'scenario'] = label

    df_ = pd.merge(df_, load_zones_, 
                   on  = 'load_zone', 
                   how = 'inner')

    df_.to_csv(path + '/' + file_name, index = False)