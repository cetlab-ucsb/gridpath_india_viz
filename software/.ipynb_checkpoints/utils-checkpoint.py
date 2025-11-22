import os, string

import pandas as pd
import numpy as np

# Grab data from databases for plotting new and existing capacity
def _load_capacity(scen_labels_):

    # Load project capacity table and process them from database
    def __load_new_and_existing_csv(df_, scenario):

        df_['capacity_mw'] = df_['capacity_mw'].astype(float)
        df_['status']      = 'new'
        
        df_ = df_[['project', 
                   'period', 
                   'technology', 
                   'load_zone', 
                   'status', 
                   'capacity_mw', 
                   'energy_capacity_mwh']]

        idx_ = (df_['period'] == 2020) & (df_['capacity_mw'] != 0.)
        df_.loc[capacity_['project'].isin(df_.loc[idx_, 'project'].unique()), 'status'] = 'existing'
        
        df_ = df_.groupby(['period', 
                           'technology', 
                           'load_zone',
                           'status']).agg({'capacity_mw': 'sum', 
                                           'energy_capacity_mwh': 'sum'})

        df_ = df_.reset_index(drop = False).rename(columns = {'energy_capacity_mwh': 'capacity_mwh'})

        df_['scenario'] = scenario

        return df_
    
    dfs_ = []
    # Open connection: open database and grab meta-data
    for scen, path in zip(scen_labels_['scenario'],  scen_labels_['path']):
        print(scen, path)
        dir_name  = r'{}/{}'.format(path, scen)
        capacity_ = pd.read_csv(dir_name + r'/results/project_period.csv', low_memory = False)
        df_       = __load_new_and_existing_csv(capacity_, scen)
        
        # Load specified capacity from csv files
        dfs_.append(df_)

    return pd.concat(dfs_, axis = 0).reset_index(drop = True)

# Grab data from databases for plotting energy dispatch and clean energy targets
def _load_dispatch(scen_labels_):

    # Load energy dispatch table and process data from database
    def __load_dispatch_from_csv(df_, scenario, zone):
        
        df_['power_mw'] = (df_['number_of_hours_in_timepoint'] 
                           * df_['timepoint_weight'] 
                           * df_['power_mw'])

        df_ = df_[['period', 
                   'technology', 
                   'load_zone', 
                   'power_mw']]
            
        df_ = df_.groupby(['period', 
                           'technology', 
                           'load_zone']).agg({'power_mw': 'sum'}).reset_index(drop = False)
        
        df_['scenario'] = scenario
                
        return df_
        
    # Load energy dispatch table and process data from database
    def __load_demand_from_csv(df_, scenario, zone):
        
        df_['overgeneration_mw'] = (df_['number_of_hours_in_timepoint'] 
                                    * df_['timepoint_weight'] 
                                    * df_['overgeneration_mw'])
        
        df_['unserved_energy_mw'] = (df_['number_of_hours_in_timepoint'] 
                                     * df_['timepoint_weight'] 
                                     * df_['unserved_energy_mw'])
        
        df_1_ = df_[['period', 
                     'load_zone', 
                     'overgeneration_mw']].copy()
        
        df_1_['technology'] = 'Curtailment'                
        df_1_ = df_1_.rename(columns = {'overgeneration_mw': 'power_mw'})

        df_2_ = df_[['period', 
                     'load_zone', 
                     'unserved_energy_mw']].copy()
        
        df_2_['technology'] = 'Shedding'                 
        df_2_ = df_2_.rename(columns = {'unserved_energy_mw': 'power_mw'})

        df_ = pd.concat([df_1_, df_2_], axis = 0)
            
        df_ = df_.groupby(['period', 
                           'technology', 
                           'load_zone']).agg({'power_mw': 'sum'}).reset_index(drop = False)
        
        df_['scenario'] = scenario
                                  
        return df_

    def __load_tx_losses_from_csv(df_, scenario, zone):
        
        df_['transmission_losses_lz_to'] = - (df_['number_of_hours_in_timepoint'] 
                                              * df_['timepoint_weight'] 
                                              * df_['transmission_losses_lz_to'])
        
        df_['transmission_losses_lz_from'] = - (df_['number_of_hours_in_timepoint'] 
                                                * df_['timepoint_weight'] 
                                                * df_['transmission_losses_lz_from'])

        df_1_  = df_[['period', 
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
        
        df_ = pd.concat([df_1_, df_2_], axis = 0)
        
        df_ = df_.groupby(['period', 
                           'technology', 
                           'load_zone']).agg({'power_mw': 'sum'}).reset_index(drop = False)

        df_['scenario'] = scenario
        
        return df_

    dfs_ = []
    # Open connection: open database and grab meta-data
    for scenario, zone, path in zip(scen_labels_['scenario'], scen_labels_['zone'], scen_labels_['path']):
        print(scenario, zone, path)
        
        dir_name   = r'{}/{}'.format(path, scenario)
        dispatch_  = pd.read_csv(dir_name + f'/results/project_timepoint.csv', low_memory = False)
        demand_    = pd.read_csv(dir_name + f'/results/system_load_zone_timepoint.csv', low_memory = False)
        tx_losses_ = pd.read_csv(dir_name + f'/results/transmission_timepoint.csv', low_memory = False)
        
        dfs_ += [__load_tx_losses_from_csv(tx_losses_, scenario, zone)]
        dfs_ += [__load_demand_from_csv(demand_, scenario, zone)]
        dfs_ += [__load_dispatch_from_csv(dispatch_, scenario, zone)]

    return pd.concat(dfs_, axis = 0).reset_index(drop = True)
    
def _group_capacity_technologies(capacity_, tech_labels_):

    for group in tech_labels_['group'].unique():
        capacity_.loc[
        capacity_['technology'].isin(tech_labels_.loc[
                                     tech_labels_['group'] == group, 'technology'
                                     ]), 'technology'
        ] = group
        
    capacity_ = capacity_.groupby(['period', 
                                   'technology', 
                                   'load_zone', 
                                   'status', 
                                   'scenario']).agg({'capacity_mw': 'sum', 
                                                     'capacity_mwh': 'sum'})

    return capacity_.reset_index(drop = False)

def _group_dispatch_technologies(df_, tech_labels_):

    for group in tech_labels_['group'].unique():
        df_.loc[
        df_['technology'].isin(tech_labels_.loc[
                               tech_labels_['group'] == group, 'technology'
                               ]), 'technology'
        ] = group
        
    df_ = df_.groupby(['period', 
                       'technology', 
                       'load_zone', 
                       'scenario']).agg({'power_mw': 'sum'})

    return df_.reset_index(drop = False)


# Grab data from databases for plotting GHG emissions
def _load_GHG_emissions(scen_labels_):

    # Load GHG emissions table and process them from database
    def __load_GHG_from_csv(df_, scenario):

        df_['carbon_emissions_tons'] = (df_['number_of_hours_in_timepoint']
                                        * df_['timepoint_weight']
                                        * df_['carbon_emissions_tons'])

        df_ = df_[['period', 'load_zone', 'carbon_emissions_tons']]
        df_ = df_.groupby(['period', 'load_zone']).sum().reset_index(drop = False)
                                                          
        df_['scenario'] = scenario     
        
        return df_
    
    # Load energy dispatch table and process data from database
    def __load_demand_from_csv(df_, scenario):
        
        df_['static_load_mw'] = (df_['number_of_hours_in_timepoint']
                                 * df_['timepoint_weight']
                                 * df_['static_load_mw'])

        df_ = df_[['period', 
                   'load_zone', 
                   'static_load_mw']]
        
        df_ = df_.groupby(['period', 'load_zone']).sum().reset_index(drop = False)
                         
        df_['scenario'] = scenario     

        return df_.rename(columns = {'static_load_mw': 'load_mw'})

    dfs_  = []
    # Open connection: open database and grab meta-data
    for scen, path in zip(scen_labels_['scenario'], scen_labels_['path']):
        print(scen, path)
        dir_name  = r'{}/{}'.format(path, scen)
        # Load GHG emissions from cvs files
        dispatch_  = pd.read_csv(dir_name + f'/results/project_timepoint.csv', low_memory = False)
        emissions_ = __load_GHG_from_csv(dispatch_, scen)
        # Load energy demand from csv files
        load_ = pd.read_csv(dir_name + f'/results/system_load_zone_timepoint.csv', low_memory = False)
        load_ = __load_demand_from_csv(load_, scen)

        dfs_.append(pd.merge(emissions_, load_, on  = ['period', 'load_zone', 'scenario']))
    
    df_                          = pd.concat(dfs_, axis = 0).reset_index(drop = True)
    df_['period']                = df_['period'].astype(int)
    df_['carbon_emissions_tons'] = df_['carbon_emissions_tons'].astype(float)
    df_['load_mw']               = df_['load_mw'].astype(float)
    
    return df_

# Grab data from databases for plotting energy dispatch and clean energy targets
def _load_clean_energy(scen_labels_):

    # Load energy dispatch table and process data from database
    def __load_dispatch_from_csv(df_, scenario, zone):
        
        techs_ = ['CCGT', 
                  'CT', 
                  'Diesel', 
                  'Nuclear',
                  'Supercritical_Coal', 
                  'Subcritical_Coal_Large', 
                  'Subcritical_Coal_Small']
        
        stor_ = ['Battery', 
                 'Hydrogen', 
                 'Hydro_Pumped']

        df_['power_mw'] = (df_['number_of_hours_in_timepoint']
                           * df_['timepoint_weight']
                           * df_['power_mw'])

        df_ = df_[['period', 
                   'technology', 
                   'load_zone', 
                   'power_mw']]
        
        df_ = df_.groupby(['period', 
                           'technology', 
                           'load_zone']).agg({'power_mw': 'sum'}).reset_index(drop = False)
        
        df_                          = df_.loc[~df_['technology'].isin(stor_)].reset_index(drop = True)
        idx_                         = df_['technology'].isin(techs_)
        df_.loc[~idx_, 'technology'] = 'clean'
        df_.loc[idx_, 'technology']  = 'no_clean'
        df_                          = df_.reset_index(drop = True)

        df_['scenario'] = scenario
                
        return df_

    dfs_ = []
    # Open connection: open database and grab meta-data
    for scenario, zone, path in zip(scen_labels_['scenario'], scen_labels_['zone'], scen_labels_['path']):
        print(scenario, path)
        
        dir_name   = r'{}/{}'.format(path, scenario)
        dispatch_  = pd.read_csv(dir_name + f'/results/project_timepoint.csv', low_memory = False)
        
        dfs_ += [__load_dispatch_from_csv(dispatch_, scenario, zone)]
        
    df_             = pd.concat(dfs_, axis = 0).reset_index(drop = True)
    df_['period']   = df_['period'].astype(int)
    df_['power_mw'] = df_['power_mw'].astype(float)
    
    return df_

# Grab data from databases for plotting energy dispatch and clean energy targets
def _load_losses(scen_labels_):

    # Load energy dispatch table and process data from database
    def __load_stor_losses_from_csv(df_, scenario):
        
        techs_ = ['Battery', 
                  'Hydro_Pumped', 
                  'Hydrogen']
        
        df_['power_mw'] = (df_['number_of_hours_in_timepoint']
                           * df_['timepoint_weight']
                           * df_['power_mw'])

        df_  = df_[['period', 
                    'technology', 
                    'load_zone', 
                    'power_mw']]
        
        idx_ = df_['technology'].isin(techs_)
        
        df_.loc[idx_, 'technology']  = 'stor_losses'
        df_.loc[~idx_, 'technology'] = 'gen'
        
        df_ = df_.groupby(['period', 
                           'technology', 
                           'load_zone']).agg({'power_mw': 'sum'}).reset_index(drop = False)
        
        df_['scenario'] = scenario
                
        return df_

    def __load_tx_losses_from_csv(df_, scenario):
        
        df_['transmission_losses_lz_to'] = - (df_['number_of_hours_in_timepoint'] 
                                              * df_['timepoint_weight']
                                              * df_['transmission_losses_lz_to'])
        
        df_['transmission_losses_lz_from'] = - (df_['number_of_hours_in_timepoint']
                                                * df_['timepoint_weight']
                                                * df_['transmission_losses_lz_from'])

        df_1_ = df_[['period', 
                     'load_zone_to', 
                     'transmission_losses_lz_to']].copy()
        
        df_2_ = df_[['period', 
                     'load_zone_from', 
                     'transmission_losses_lz_from']].copy()

        df_1_['technology'] = 'tx_losses'
        df_2_['technology'] = 'tx_losses'

        df_1_ = df_1_.rename(columns = {'transmission_losses_lz_to': 'power_mw', 
                                        'load_zone_to': 'load_zone'})

        df_2_ = df_2_.rename(columns = {'transmission_losses_lz_from': 'power_mw',
                                        'load_zone_from': 'load_zone'})
        
        df_ = pd.concat([df_1_, df_2_], axis = 0)
        df_ = df_.groupby(['period', 
                           'technology', 
                           'load_zone']).agg({'power_mw': 'sum'}).reset_index(drop = False)

        df_['scenario'] = scenario
        
        return df_

    dfs_ = []
    # Open connection: open database and grab meta-data
    for scen, path in zip(scen_labels_['scenario'], scen_labels_['path']):
        print(scen, path)
        
        dir_name  = r'{}/{}'.format(path, scen)
        dispatch_ = pd.read_csv(dir_name + f'/results/project_timepoint.csv', low_memory = False)
        tx_losses_ = pd.read_csv(dir_name + f'/results/transmission_timepoint.csv', low_memory = False)

        dfs_ += [__load_stor_losses_from_csv(dispatch_, scen)]
        dfs_ += [__load_tx_losses_from_csv(tx_losses_, scen)]

    return pd.concat(dfs_, axis = 0).reset_index(drop = True)


# Grab data from databases for plotting LCOE emissions
def _load_land_use(scen_labels_):
 
    # Load energy dispatch table and process data from database
    def __load_dispatch_from_csv(df_, scenario):
        
        df_['power_mw'] = (df_['number_of_hours_in_timepoint']
                           * df_['timepoint_weight']
                           * df_['power_mw'])

        df_ = df_[['period', 
                   'technology', 
                   'load_zone', 
                   'power_mw']]
            
        df_ = df_.groupby(['period', 
                           'technology', 
                           'load_zone']).agg({'power_mw': 'sum'}).reset_index(drop = False)
        
        df_['scenario'] = scenario
                
        return df_

    # Load fix capacity cost table and process data from database
    def __load_capacity_from_csv(df_, scenario):  

        df_ = df_[['period', 
                   'technology', 
                   'load_zone', 
                   'capacity_mw', 
                   'energy_capacity_mwh']]

        df_ = df_.groupby(['period', 
                           'technology', 
                           'load_zone']).agg({'capacity_mw': 'sum', 
                                              'energy_capacity_mwh': 'sum'})

        df_ = df_.reset_index(drop = False).rename(columns = {'energy_capacity_mwh': 'capacity_mwh'})

        df_['scenario'] = scenario

        return df_

    dfs_ = []
    # Open connection: open database and grab meta-data
    for scen, path in zip(scen_labels_['scenario'], scen_labels_['path']):
        print(scen, path)
        dir_name = r'{}/{}'.format(path, scen)        

        # Load fix costs from csv files
        project_ = pd.read_csv(dir_name + f'/results/project_period.csv', low_memory = False)
        df_1_    = __load_capacity_from_csv(project_, scen)

        # Load variables costs from csv files
        dispatch_ = pd.read_csv(dir_name + f'/results/project_timepoint.csv', low_memory = False)
        df_2_     = __load_dispatch_from_csv(dispatch_, scen)

        dfs_ += [pd.merge(df_1_, df_2_, on = ['scenario', 
                                              'technology', 
                                              'period', 
                                              'load_zone'])]
    
    df_                  = pd.concat(dfs_, axis = 0).reset_index(drop = True)
    df_['period']        = df_['period'].astype(int)
    df_['capacity_mw']   = df_['capacity_mw'].astype(float)
    df_['capacity_mwh']  = df_['capacity_mwh'].astype(float)
    df_['power_mw']      = df_['power_mw'].astype(float)

    return df_

# Grab data from databases for plotting LCOE emissions
def _load_cost(scen_labels_):
    
    # Load fuel, and operation and maintanace cost table and process data from database
    def __load_vr_cost_from_csv(df_, scenario):
        
        df_['variable_om_cost']  = (df_['number_of_hours_in_timepoint'] 
                                    * df_['timepoint_weight'] 
                                    * df_['variable_om_cost'])
        df_['variable_om_cost'] += (df_['number_of_hours_in_timepoint']
                                    * df_['timepoint_weight']
                                    * df_['startup_cost'].fillna(0))

        df_ = df_[['period', 
                   'technology', 
                   'load_zone', 
                   'variable_om_cost']]
        
        df_ = df_.rename(columns = {'variable_om_cost': 'variable_cost'})
        df_ = df_.groupby(['period', 
                           'technology',
                           'load_zone']).sum().reset_index(drop = False)
                         
        df_['scenario'] = scenario     

        return df_

    # Load fix capacity cost table and process data from database
    def __load_fx_cost_from_csv(project_, new_, spec_, scenario):
        
        new_ = new_.fillna({'capacity_cost': 0, 'fixed_cost': 0})
        
        new_['fixed_cost'] = new_['capacity_cost'] + new_['fixed_cost']

        new_ = new_[['period', 'technology', 'load_zone', 'fixed_cost']]
        new_ = new_.groupby(['period', 
                             'technology', 
                             'load_zone']).sum().reset_index(drop = False)
                             
        spec_['fixed_cost'] = spec_['fixed_cost_per_mw_yr'] 

        spec_ = pd.merge(spec_, project_, on = ['project'])
        spec_ = spec_[['period', 'technology', 'load_zone', 'fixed_cost']]
        spec_ = spec_.groupby(['period', 
                               'technology', 
                               'load_zone']).sum().reset_index(drop = False)

        df_ = pd.concat([new_, spec_], axis = 0)
        df_ = df_.groupby(['period', 
                           'technology',
                           'load_zone']).sum().reset_index(drop = False)
        
        df_['scenario'] = scenario    

        return df_

    # Load transmission capacity cost table and process data from database
    def __load_tx_cost_from_csv(project_, new_, scenario):

        new_['fixed_cost'] = new_['capacity_cost'] + new_['fixed_cost']
        
        new_ = new_[['period', 
                     'transmission_line', 
                     'max_mw', 
                     'fixed_cost']]
        
        new_ = new_.rename(columns = {'max_mw': 'power_mw'})
        
        df_  = new_.groupby(['period', 
                             'transmission_line']).sum().reset_index(drop = False)
        
        project_ = project_.loc[project_['vintage'] == 2020].reset_index(drop = False)
        
        project_ = project_[['transmission_line', 
                             'tx_annualized_real_cost_per_mw_yr']]
        
#         project_p_                      = project_.copy()
#         project_p_['transmission_line'] = project_p_['transmission_line'].str.replace('_new', '')
#         project_ = pd.concat([project_, project_p_], axis = 0).reset_index(drop = True)

        df_                  = pd.merge(df_, project_, on = ['transmission_line'])
        df_['capacity_cost'] = df_['tx_annualized_real_cost_per_mw_yr']*df_['power_mw']
        df_['load_zone']     = df_['transmission_line'].apply(lambda x: x.split("-")[0])
        
        df_ = df_[['period', 
                   'load_zone', 
                   'capacity_cost', 
                   'fixed_cost']]
        
        df_ = df_.groupby(['period', 
                           'load_zone']).agg({'capacity_cost': 'sum', 
                                              'fixed_cost': 'sum'}).reset_index(drop = False)
        
        df_['fixed_cost'] = df_['capacity_cost'] + df_['fixed_cost']
        df_['variable_cost'] = 0.
        
        df_ = df_[['period', 
                   'load_zone', 
                   'fixed_cost', 
                   'variable_cost']]
        
        df_['technology'] = 'Transmission Losses'    
        df_['scenario']   = scenario    
        
        return df_

    # Load energy dispatch table and process data from database
    def __load_demand_from_csv(df_, scenario):
        
        df_['static_load_mw'] = (df_['number_of_hours_in_timepoint'] 
                                 * df_['timepoint_weight']
                                 * df_['static_load_mw'])

        df_ = df_[['period', 'load_zone', 'static_load_mw']]
        df_ = df_.groupby(['period', 
                           'load_zone']).sum().reset_index(drop = False)
                         
        df_['technology'] = 'Demand'     
        df_['scenario']   = scenario     

        return df_.rename(columns = {'static_load_mw': 'load_mw'})

    dfs_1_ = []
    dfs_2_ = []
    # Open connection: open database and grab meta-data
    for scen, path in zip(scen_labels_['scenario'], scen_labels_['path']):
        print(scen, path)
        dir_name = r'{}/{}'.format(path, scen)        

        # Load energy demand from csv files
        load_ = pd.read_csv(dir_name + f'/results/system_load_zone_timepoint.csv', low_memory = False)
        load_ = __load_demand_from_csv(load_, scen)
        # print(load_.groupby(['period']).agg({'load_mw': 'sum'}).reset_index(drop = False))

        # Load fix costs from csv files
        new_     = pd.read_csv(dir_name + f'/results/project_period.csv', low_memory = False)
        spec_    = pd.read_csv(dir_name + r'/inputs/spec_capacity_period_params.tab', 
                               sep = '\t', 
                               engine = 'python')
        project_ = pd.read_csv(dir_name + r'/inputs/projects.tab', 
                               sep = '\t', 
                               engine = 'python')
        fx_      = __load_fx_cost_from_csv(project_, new_, spec_, scen)
        # print(fx_.groupby(['period']).agg({'fixed_cost': 'sum'}).reset_index(drop = False))

        # Load variables costs from csv files
        vr_ = pd.read_csv(dir_name + f'/results/project_timepoint.csv', 
                          low_memory = False)
        vr_ = __load_vr_cost_from_csv(vr_, scen)
        # print(vr_.groupby(['period']).agg({'variable_cost': 'sum'}).reset_index(drop = False))

        # Load tx costs from csv files
        new_     = pd.read_csv(dir_name + f'/results/transmission_period.csv', 
                               low_memory = False) 
        spec_    = pd.read_csv(dir_name + r'/inputs/specified_transmission_line_capacities.tab', 
                               sep = '\t', engine = 'python')        
        project_ = pd.read_csv(dir_name + r'/inputs/new_build_transmission_vintage_costs.tab', 
                               sep = '\t', engine = 'python')
        tx_      = __load_tx_cost_from_csv(project_, new_, scen)
        # print(tx_.groupby(['period']).agg({'fixed_cost': 'sum', 
        #                                    'variable_cost': 'sum'}).reset_index(drop = False))
        
        df_ = pd.merge(vr_, fx_, on = ['scenario', 'technology', 'period', 'load_zone'])
        df_ = pd.concat([df_, tx_], axis = 0)

        dfs_1_.append(df_)
        dfs_2_.append(load_)
        
    df_1_ = pd.concat(dfs_1_, axis = 0).reset_index(drop = True)
    df_2_ = pd.concat(dfs_2_, axis = 0).reset_index(drop = True)

    df_1_['period']        = df_1_['period'].astype(int)
    df_1_['fixed_cost']    = df_1_['fixed_cost'].astype(float)
    df_1_['variable_cost'] = df_1_['variable_cost'].astype(float)
    
    df_2_['period']  = df_2_['period'].astype(int)
    df_2_['load_mw'] = df_2_['load_mw'].astype(float)

    return df_1_, df_2_

def _group_emissions_by_zone(df_, scen_labels_, 
                             columns_ = ['period', 
                                         'scenario', 
                                         'load_zone']):
    
    dfs_ = []
    # Open connection: open database and grab meta-data
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

def _group_clean_energy_by_zone(df_, scen_labels_, 
                                columns_ = ['period', 
                                            'scenario', 
                                            'technology', 
                                            'load_zone']):
    
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
        
    df_             = pd.concat(dfs_, axis = 0).reset_index(drop = True)
    df_['period']   = df_['period'].astype(int)
    df_['power_mw'] = df_['power_mw'].astype(float)

    return df_

def _group_land_use_by_zone(df_, scen_labels_, land_use_, 
                            columns_ = ['period', 
                                        'scenario', 
                                        'technology', 
                                        'load_zone']):
    
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
    df_['power_mw']     = df_['power_mw'].astype(float)

    df_['area_m2'] = 0.
    for tech in df_['technology'].unique():
        idx_ = df_['technology'] == tech        
        df_.loc[idx_, 'area_m2'] = (land_use_.loc[tech, 'land_use_intensity'] 
                                    * df_.loc[idx_, land_use_.loc[tech, 'type']])


    land_use_['land_use_intensity'] = land_use_['land_use_intensity'].astype(float)
    
    return df_


def _group_cost_by_zone(df_1_, df_2_, scen_labels_, 
                        columns_ = ['period', 
                                    'scenario', 
                                    'load_zone']):
    
    dfs_1_ = []
    dfs_2_ = []

    # Open connection: open database and grab meta-data
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

def _group_demand_by_zone(df_, scen_labels_, 
                          columns_ = ['period', 
                                      'scenario', 
                                      'load_zone']):
    
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
        
    df_            = pd.concat(dfs_, axis = 0).reset_index(drop = True)
    df_['period']  = df_['period'].astype(int)
    df_['load_mw'] = df_['load_mw'].astype(float)
    
    return df_