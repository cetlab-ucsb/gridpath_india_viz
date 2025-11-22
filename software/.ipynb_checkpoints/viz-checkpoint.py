import os

import pandas as pd
import numpy as np
import itertools
import geopandas as gpd

import matplotlib as mpl
import matplotlib.pyplot as plt

from matplotlib.ticker import MultipleLocator
from matplotlib.lines import Line2D
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.transforms import ScaledTranslation

def _plot_new_and_existing_capacity(ax, df_, scens_label_, tech_label_, 
                                    y_lim_max    = None,
                                    units        = 1e3,
                                    ylabel       = 'Existing & New Capacity (GW)',
                                    y_period_loc = -1600.,
                                    y_grid_inc   = 500,
                                    div_line_len = 0.325,
                                    legend       = True,
                                    title        = ''):

    y_period_loc = y_period_loc*y_lim_max

    def __make_new_and_existing_capacit_legend(ax, df_, techs_):

        tech_idx_ = np.sort(np.unique(techs_['order']))

        ax.bar(0., 0., 0., bottom    = 0.,
                           label     = 'Existing',
                           color     = 'None',
                           lw        = 0.,
                           hatch     = 'xx',
                           edgecolor = 'lightgray',
                           zorder    = 10)

        for i_tech in tech_idx_[::-1]:
            tech  = tech_label_.loc[tech_label_['order'] == i_tech, 'group'].unique()[0]
            color = tech_label_.loc[tech_label_['order'] == i_tech, 'group_color'].unique()[0]
            idx_  = df_['technology'] == tech
            if idx_.sum() > 0:
                if df_.loc[idx_, 'capacity_mw'].sum() != 0:
                    ax.bar(0., 0., 0., bottom = 0.,
                                       color  = color,
                                       label  = tech,
                                       zorder = 10)

    periods_  = np.sort(df_['period'].unique())
    scens_    = scens_label_['scenario'].unique()    
    tech_idx_ = np.sort(np.unique(tech_label_['order']))

    ticks_    = []
    labels_   = []
    offsets_  = []
    lengths_  = []
    x_period_ = []
    
    i_scen = 0
    offset = 0
    y_max  = 0
    
    width  = 1/(len(scens_) + 1.5)
    x_     = np.linspace(0, len(periods_) - 1, len(periods_))
    
    for scen, label, zone in zip(scens_label_['scenario'], scens_label_['label'], scens_label_['zone']):

        df_p_ = df_.copy()
        
        if (df_p_['load_zone'] == zone).sum() == 0.:
            df_p_['load_zone'] = zone
            df_p_ = df_p_.groupby(['period', 
                                   'technology', 
                                   'load_zone', 
                                   'status',
                                   'scenario']).agg({'capacity_mw': 'sum'}).reset_index(drop = False)
            
        idx_ = (df_p_['scenario'] == scen) & (df_p_['load_zone'] == zone)
                
        for period, i_period in zip(periods_, range(len(periods_))):
            idx_1_ = idx_ & (df_p_['period'] == period)
            if (i_scen == 0) & (i_period == 0): 
                __make_new_and_existing_capacit_legend(ax, df_p_, tech_label_)

            for i_tech in tech_idx_:
                
                tech  = tech_label_.loc[tech_label_['order'] == i_tech, 'group'].unique()[0]
                color = tech_label_.loc[tech_label_['order'] == i_tech, 'group_color'].unique()[0]
                
                idx_2_ = idx_1_ & (df_p_['status'] == 'existing') & (df_p_['technology'] == tech)

                if idx_2_.sum() == 1.:
                    power = df_p_.loc[idx_2_, 'capacity_mw'].to_numpy()[0]

                    ax.bar(x_[i_period], power/units, width, bottom    = offset/units,
                                                             color     = color,
                                                             lw        = 0.,
                                                             hatch     = 'x',
                                                             edgecolor = 'lightgray', zorder = 10)

                    offset += power

            for i_tech in tech_idx_:
                
                tech  = tech_label_.loc[tech_label_['order'] == i_tech, 'group'].unique()[0]
                color = tech_label_.loc[tech_label_['order'] == i_tech, 'group_color'].unique()[0]
                
                idx_3_ = idx_1_ & (df_p_['technology'] == tech) & (df_p_['status'] == 'new')
                if idx_3_.sum() == 1.:
                    power = df_p_.loc[idx_3_, 'capacity_mw'].to_numpy()[0]

                    ax.bar(x_[i_period], power/units, width, bottom = offset/units,
                                                             color  = color,
                                                             zorder = 10)

                    offset += power

            if y_max < offset:
                y_max = offset

            ticks_.append(x_[i_period])
            labels_.append(label)
            offsets_.append(offset/units)
            x_period_.append(x_[i_period])

            offset = 0.

        x_ = x_ + .9/len(scens_)
        i_scen += 1
        
    z_ = x_ - .9/len(scens_)

    x_period_ = np.mean(np.array(x_period_).reshape(len(scens_), len(periods_)), axis = 0)
    y_period_ = np.max(np.array(offsets_).reshape(len(scens_), len(periods_)), axis = 0)

    ax.set_ylabel(ylabel, fontsize = 18)

    if legend:
        ax.legend(loc            = 'center left',
                  bbox_to_anchor = (1, 0.5),
                  frameon        = False,
                  prop           = {'size': 15})

    if y_lim_max != None:
        ax.set_ylim(0., y_lim_max)
        y_max = y_lim_max
    else:
        ax.set_ylim(0., y_period_.max()*1.2)
        y_max /= units
        
    N_steps  = int(np.ceil(y_max/y_grid_inc))
    y_ticks_ = np.linspace(0, int(N_steps*y_grid_inc), N_steps + 1, dtype = int)
    
    ax.set_yticks(y_ticks_, y_ticks_)
    ax.set_xticks(x_period_, periods_)

    ax.xaxis.set_tick_params(labelsize = 19, 
                             left      = False)
    
    ax.yaxis.set_tick_params(labelsize = 15, 
                             left      = False)
    
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))

    ax.axhline(0, linewidth = .5, 
                  linestyle = '-', 
                  color     = 'k', 
                  clip_on   = False, 
                  zorder    = 10)
    
    ax.set_title(title, fontsize = 20, y = 0.912)

    ax.spines[['right', 'top', 'left', 'bottom']].set_visible(False)
    ax.grid(axis = 'y')
    
    
def _plot_new_and_existing_storage(ax, df_, scens_label_, tech_label_, 
                                   units        = 1e3,
                                   ylabel       = 'Existing & New Capacity (GW)',
                                   y_period_loc = -6250.,
                                   y_grid_inc   = 2000,
                                   div_line_len = 0.325,
                                   y_lim_max    = None,
                                   legend       = True,
                                   title        = ''):

    y_period_loc = y_period_loc*y_lim_max

    def __make_new_and_existing_capacit_legend(ax, df_, techs_):
        
        tech_idx_ = np.sort(np.unique(techs_['order']))

        ax.bar(0., 0., 0., bottom    = 0.,
                           label     = 'Existing',
                           color     = 'None',
                           lw        = 0.,
                           hatch     = 'xx',
                           edgecolor = 'lightgray',
                           zorder    = 10)
            
        for i_tech in tech_idx_[::-1]:
            tech  = tech_label_.loc[tech_label_['order'] == i_tech, 'group'].unique()[0]
            color = tech_label_.loc[tech_label_['order'] == i_tech, 'group_color'].unique()[0]
            
            idx_ = df_['technology'] == tech
            if idx_.sum() > 0:
                if df_.loc[idx_, 'capacity_mwh'].sum() != 0:
                    ax.bar(0., 0., 0., bottom = 0.,
                                       color  = color,
                                       label  = tech,
                                       zorder = 10)

    periods_  = np.sort(df_['period'].unique())
    scens_    = scens_label_['scenario'].unique()    
    tech_idx_ = np.sort(np.unique(tech_label_['order']))

    ticks_    = []
    labels_   = []
    offsets_  = []
    lengths_  = []
    x_period_ = []
    
    i_scen = 0
    offset = 0
    y_max  = 0
    
    width  = 1/(len(scens_) + 1.5)
    x_     = np.linspace(0, len(periods_) - 1, len(periods_))
    
    for scen, label, zone in zip(scens_label_['scenario'], scens_label_['label'], scens_label_['zone']):

        df_p_ = df_.copy()
        
        if (df_p_['load_zone'] == zone).sum() == 0.:
            df_p_['load_zone'] = zone
            df_p_ = df_p_.groupby(['period', 
                                   'technology', 
                                   'load_zone', 
                                   'status',
                                   'scenario']).agg({'capacity_mwh': 'sum'}).reset_index(drop = False)
            
        idx_ = (df_p_['scenario'] == scen) & (df_p_['load_zone'] == zone)
                
        for period, i_period in zip(periods_, range(len(periods_))):
            idx_1_ = idx_ & (df_p_['period'] == period)
            if (i_scen == 0) & (i_period == 0): 
                __make_new_and_existing_capacit_legend(ax, df_p_, tech_label_)
                
            for i_tech in tech_idx_:
                
                tech  = tech_label_.loc[tech_label_['order'] == i_tech, 'group'].unique()[0]
                color = tech_label_.loc[tech_label_['order'] == i_tech, 'group_color'].unique()[0]
                
                idx_2_ = idx_1_ & (df_p_['status'] == 'existing') & (df_p_['technology'] == tech)

                if idx_2_.sum() == 1.:
                    power = df_p_.loc[idx_2_, 'capacity_mwh'].to_numpy()[0]

                    ax.bar(x_[i_period], power/units, width, bottom    = offset/units,
                                                             color     = color,
                                                             lw        = 0.,
                                                             hatch     = 'x',
                                                             edgecolor = 'lightgray', zorder = 10)

                    offset += power

            for i_tech in tech_idx_:
                
                tech  = tech_label_.loc[tech_label_['order'] == i_tech, 'group'].unique()[0]
                color = tech_label_.loc[tech_label_['order'] == i_tech, 'group_color'].unique()[0]
                
                idx_3_ = idx_1_ & (df_p_['technology'] == tech) & (df_p_['status'] == 'new')
                
                if idx_3_.sum() == 1.:
                    power = df_p_.loc[idx_3_, 'capacity_mwh'].to_numpy()[0]

                    ax.bar(x_[i_period], power/units, width, bottom = offset/units,
                                                             color  = color,
                                                             zorder = 10)

                    offset += power

            if y_max < offset:
                y_max = offset

            ticks_.append(x_[i_period])
            labels_.append(label)
            offsets_.append(offset/units)
            x_period_.append(x_[i_period])

            offset = 0.

        x_ = x_ + .9/len(scens_)
        i_scen += 1
        
    z_ = x_ - .9/len(scens_)

    x_period_ = np.mean(np.array(x_period_).reshape(len(scens_), len(periods_)), axis = 0)
    y_period_ = np.max(np.array(offsets_).reshape(len(scens_), len(periods_)), axis = 0)

    ax.set_ylabel(ylabel, fontsize = 18)


    if legend:
        ax.legend(loc            = 'center left',
                  bbox_to_anchor = (1, 0.5),
                  frameon        = False,
                  prop           = {'size': 15})

    if y_lim_max != None:
        ax.set_ylim(0., y_lim_max)
        y_max = y_lim_max
    else:
        ax.set_ylim(0., )
        y_max /= units
        
    N_steps  = int(np.ceil(y_max/y_grid_inc))
    y_ticks_ = np.linspace(0, int(N_steps*y_grid_inc), N_steps + 1, dtype = int)
    ax.set_yticks(y_ticks_, y_ticks_)
    #ax.set_xticks(ticks_, labels_, rotation = 90)
    ax.set_xticks(x_period_, periods_)
    
    ax.xaxis.set_tick_params(labelsize = 19, 
                             left      = False)
    
    ax.yaxis.set_tick_params(labelsize = 15, 
                             left      = False)

    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))

    ax.set_title(title, fontsize = 20, y = 0.912)
    
    ax.axhline(0, linewidth = .5, 
                  linestyle = '-', 
                  color     = 'k', 
                  clip_on   = False, 
                  zorder    = 10)

    ax.spines[['right', 'top', 'left', 'bottom']].set_visible(False)
    ax.grid(axis = 'y')

def _plot_dispatch(ax, df_, scens_label_, tech_label_, 
                   y_lim_max    = None,
                   y_lim_min    = None,
                   units        = 1e6,
                   ylabel       = r'Electricity Generation (TWh)',
                   y_period_loc = -3870.,
                   y_grid_inc   = 1000,
                   div_line_len = .425,
                   legend       = True,
                   title        = ''):
    
    y_period_loc = y_period_loc*(y_lim_max - y_lim_min)

    def __make_dispatch_legend(ax, df_, techs_):

        tech_idx_ = np.sort(np.unique(techs_['order_v2']))

        ax.bar(0., 0., 0., bottom    = 0.,
                           label     = 'Existing',
                           color     = 'None',
                           lw        = 0.,
                           hatch     = 'xx',
                           edgecolor = 'lightgray',
                           zorder    = 10)
        
        for i_tech in tech_idx_[::-1]:
            tech  = tech_label_.loc[tech_label_['order_v2'] == i_tech, 'group'].unique()[0]
            color = tech_label_.loc[tech_label_['order_v2'] == i_tech, 'group_color'].unique()[0]
            
            idx_ = df_['technology'] == tech
            if idx_.sum() > 0:
                if df_.loc[idx_, 'power_mw'].to_numpy().sum() != 0:
                    ax.bar(0., 0., 0., bottom = 0.,
                                       color  = color,
                                       label  = tech.replace('_', ' '),
                                       zorder = 2,
                                       ec     = 'None',
                                       lw     = 0.,
                                       aa     = True)

    periods_  = np.sort(df_['period'].unique())
    scens_    = scens_label_['scenario'].unique()    
    tech_idx_ = np.sort(np.unique(tech_label_['order']))

    width = 1./(len(scens_) + 1.5)
    x_    = np.linspace(0, len(periods_) - 1, len(periods_))

    ticks_    = []
    labels_   = []
    x_period_ = []
    y_period_ = []
    
    i_scen          = 0
    offset_positive = 0.
    offset_negative = 0.    
    y_max           = 0
    y_min           = 0
    
    for scen, label, zone in zip(scens_label_['scenario'], scens_label_['label'], scens_label_['zone']):
        df_p_ = df_.copy()
        
        if (df_p_['load_zone'] == zone).sum() == 0.:
            df_p_['load_zone'] = zone
            df_p_ = df_p_.groupby(['period', 
                                   'technology', 
                                   'load_zone', 
                                   'scenario']).agg({'power_mw': 'sum'}).reset_index(drop = False)
            
        idx_ = (df_p_['scenario'] == scen) & (df_p_['load_zone'] == zone)

        for period, i_period in zip(periods_, range(len(periods_))):
            idx_1_ = idx_ & (df_p_['period'] == period)
            
            if (i_scen == 0) & (i_period == 0): 
                __make_dispatch_legend(ax, df_p_, tech_label_)

            for i_tech in tech_idx_:
                
                tech  = tech_label_.loc[tech_label_['order'] == i_tech, 'group'].unique()[0]
                color = tech_label_.loc[tech_label_['order'] == i_tech, 'group_color'].unique()[0]
                
                idx_2_ = idx_1_ & (df_p_['technology'] == tech)

                if idx_2_.sum() == 1:
                    power = float(df_p_.loc[idx_2_, 'power_mw'].to_numpy()[0])

                    if power != 0:
                        if power > 0:
                            offset = offset_positive
                        else:
                            offset = offset_negative

                        ax.bar(x_[i_period], power/units, width, bottom = offset/units,
                                                                 color  = color,
                                                                 zorder = 2,
                                                                 ec     = 'None',
                                                                 lw     = 0.,
                                                                 aa     = True)

                        if power >= 0:
                            offset_positive += power
                        else:
                            offset_negative += power

            if offset_negative/units < y_min: 
                y_min = offset_negative/units
            if offset_positive/units > y_max: 
                y_max = offset_positive/units

            ticks_.append(x_[i_period])
            labels_.append(label)
            x_period_.append(x_[i_period])
            y_period_.append(offset_positive)
            
            offset_positive = 0.
            offset_negative = 0.

        x_ = x_ + .9/len(scens_)
        
        i_scen += 1
        
    z_ = x_ - .9/len(scens_)

    x_period_ = np.mean(np.array(x_period_).reshape(len(scens_), len(periods_)), axis = 0)
    y_period_ = np.max(np.array(y_period_).reshape(len(scens_), len(periods_)), axis = 0)

    ax.set_ylabel(ylabel, fontsize = 18)

    ax.axhline(0, linewidth = .5, 
                  linestyle = '-', 
                  color     = 'k', 
                  clip_on   = False, 
                  zorder    = 10)
    
    if legend:
        ax.legend(loc            = 'center left',
                  bbox_to_anchor = (1.025, 0.6),
                  frameon        = False,
                  prop           = {'size': 15})

    if (y_lim_min != None) & (y_lim_max != None):
        ax.set_ylim(y_lim_min, y_lim_max)
        y_max = y_lim_max
        
    N_steps  = int(np.ceil(y_max/y_grid_inc))
    y_ticks_ = np.linspace(0, int(N_steps*y_grid_inc), N_steps + 1, dtype = int)
    ax.set_yticks(y_ticks_, y_ticks_)
    
    #ax.set_xticks(ticks_, labels_, rotation = 90)
    ax.set_xticks(x_period_, periods_)

    ax.xaxis.set_tick_params(labelsize = 19, left = False)
    ax.yaxis.set_tick_params(labelsize = 15, left = False)

    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))

    ax.set_title(title, fontsize = 18, y = 0.9125)

    ax.spines[['right', 'top', 'left', 'bottom']].set_visible(False)
    ax.grid(axis = 'y')


# Plot system cost for different scenarios
def _plot_total_cost(ax, df_, scen_labels_, 
                     USD_to_INR   = 72,
                     legend       = False,
                     units        = 1e9,
                     title        = '', 
                     legend_title = 'Scenario', 
                     y_min        = None, 
                     y_max        = None):
        
    axp = ax.twinx()
    for scen, zone in zip(scen_labels_['scenario'], scen_labels_['zone']):    

        data_ = df_.loc[(df_['scenario'] == scen) & (df_['load_zone'] == zone)].copy()        
        idx_  = np.argsort(data_['period'].to_numpy())
        
        x_ = data_['period'].to_numpy()
        y_ = data_['variable_cost'].to_numpy() 
        w_ = data_['fixed_cost'].to_numpy()

        ax.plot(x_[idx_], (y_[idx_] + w_[idx_])/units, 
                color     = scen_labels_.loc[scen_labels_['scenario'] == scen, 'color'].to_numpy()[0], 
                linestyle = scen_labels_.loc[scen_labels_['scenario'] == scen, 'linestyle'].to_numpy()[0],
                label     = scen_labels_.loc[scen_labels_['scenario'] == scen, 'label'].to_numpy()[0],
                marker    = scen_labels_.loc[scen_labels_['scenario'] == scen, 'marker'].to_numpy()[0],
                linewidth = scen_labels_.loc[scen_labels_['scenario'] == scen, 'linewidth'].to_numpy()[0], 
                zorder    = scen_labels_.loc[scen_labels_['scenario'] == scen, 'order'].to_numpy()[0],
                alpha     = 0.75)
        
        #axp.plot(x_[idx_], USD_to_INR*y_[idx_]/units)
    
    ax.set_xticks(x_[idx_], x_[idx_])
    
    ax.xaxis.set_tick_params(labelsize = 18)
    ax.yaxis.set_tick_params(labelsize = 18)
    axp.yaxis.set_tick_params(labelsize = 18)

    #ax.set_ylabel(r'Costs (USD per MWh)', fontsize = 18)
    ax.set_ylabel(r'Costs (Billion USD)', fontsize = 20)
    axp.set_ylabel(r'(Lakh Crores INR)', fontsize = 20)

    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    axp.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))

    if (y_min != None) & (y_max != None):
        ax.set_ylim(y_min, y_max)
        axp.set_ylim(USD_to_INR*y_min/1000, USD_to_INR*y_max/1000)

    if legend:
        ax.legend(loc            = 'center left', 
                  title          = legend_title,
                  handlelength   = 1.75,
                  bbox_to_anchor = (1, 0.5), 
                  frameon        = False,
                  title_fontsize = 20,
                  prop           = {'size': 18})
    
    ax.set_title(title, fontsize = 22, 
                        y        = 0.9125)

# Plot levelized cost of electricity for different scenarios
def _plot_levelized_cost(ax, df_1_, df_2_, scen_labels_, 
                         USD_to_INR   = 72,
                         legend       = False,
                         title        = '', 
                         legend_title = 'Scenario', 
                         y_min        = None, 
                         y_max        = None):
    
    axp = ax.twinx()

    for scen, zone in zip(scen_labels_['scenario'], scen_labels_['zone']):    
        
        data_ = df_1_.loc[(df_1_['scenario'] == scen) & (df_1_['load_zone'] == zone)].copy()  
        load_ = df_2_.loc[(df_2_['scenario'] == scen) & (df_2_['load_zone'] == zone)].copy()        
        idx_  = np.argsort(data_['period'].to_numpy())
        
        x_ = data_['period'].to_numpy()
        y_ = data_['variable_cost'].to_numpy() 
        w_ = data_['fixed_cost'].to_numpy()
        z_ = load_['load_mw'].to_numpy()
        
        ax.plot(x_[idx_], (y_[idx_] + w_[idx_])/z_[idx_], 
                color     = scen_labels_.loc[scen_labels_['scenario'] == scen, 'color'].to_numpy()[0], 
                linestyle = scen_labels_.loc[scen_labels_['scenario'] == scen, 'linestyle'].to_numpy()[0],
                label     = scen_labels_.loc[scen_labels_['scenario'] == scen, 'label'].to_numpy()[0],
                marker    = scen_labels_.loc[scen_labels_['scenario'] == scen, 'marker'].to_numpy()[0],
                linewidth = scen_labels_.loc[scen_labels_['scenario'] == scen, 'linewidth'].to_numpy()[0], 
                zorder    = scen_labels_.loc[scen_labels_['scenario'] == scen, 'order'].to_numpy()[0],
                alpha     = 0.75)
    
        #axp.plot(x_[idx_], USD_to_INR*y_[idx_]/z_[idx_])

    ax.set_xticks(x_[idx_], x_[idx_])
       
    y_ = np.array([3, 4, 5])
    axp.set_yticks(y_, y_)

    ax.xaxis.set_tick_params(labelsize = 18)
    ax.yaxis.set_tick_params(labelsize = 18)
    axp.yaxis.set_tick_params(labelsize = 18)

    ax.set_ylabel(r'Costs (USD per MWh)', fontsize = 20)
    axp.set_ylabel(r'(INR per kWh)', fontsize = 20)

    #axp.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))

    if (y_min != None) & (y_max != None):
        ax.set_ylim(y_min, y_max)
        axp.set_ylim(USD_to_INR*y_min/1000., USD_to_INR*y_max/1000.)

    if legend:
        ax.legend(loc            = 'center left',
                  title          = legend_title,
                  handlelength   = 1.75,
                  bbox_to_anchor = (1, 0.5), 
                  frameon        = False,
                  title_fontsize = 20,
                  prop           = {'size': 18})
    
    ax.set_title(title, fontsize = 22, 
                        y        = 0.9125)

# Plot GHG emissions for different scenarios
def _plot_carbon_emissions(ax, df_, scen_labels_, 
                           title        = '', 
                           units        = 1e6,
                           legend       = False, 
                           legend_title = 'Scenario', 
                           y_min        = None, 
                           y_max        = None):
    
    for scen, zone in zip(scen_labels_['scenario'], scen_labels_['zone']):    

        data_ = df_.loc[(df_['scenario'] == scen) & (df_['load_zone'] == zone)].copy()        
        idx_  = np.argsort(data_['period'].to_numpy())
        x_    = data_['period'].to_numpy()
        y_    = data_['carbon_emissions_tons'].to_numpy()
        
        ax.plot(x_[idx_], y_[idx_]/units, 
                color     = scen_labels_.loc[scen_labels_['scenario'] == scen, 'color'].to_numpy()[0], 
                linestyle = scen_labels_.loc[scen_labels_['scenario'] == scen, 'linestyle'].to_numpy()[0],
                label     = scen_labels_.loc[scen_labels_['scenario'] == scen, 'label'].to_numpy()[0],
                marker    = scen_labels_.loc[scen_labels_['scenario'] == scen, 'marker'].to_numpy()[0],
                linewidth = scen_labels_.loc[scen_labels_['scenario'] == scen, 'linewidth'].to_numpy()[0],  
                zorder    = scen_labels_.loc[scen_labels_['scenario'] == scen, 'order'].to_numpy()[0],
                alpha     = 0.75)

    ax.set_xticks(x_[idx_], x_[idx_])
    ax.xaxis.set_tick_params(labelsize = 18)
    ax.yaxis.set_tick_params(labelsize = 18)
    ax.set_ylabel(r'GHG Emissions (MtCO$_2$)', fontsize = 20)
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    
    if (y_min != None) & (y_max != None):
        ax.set_ylim(y_min, y_max)

    if legend:
        ax.legend(loc            = 'center left', 
                  title          = legend_title,
                  handlelength   = 1.75,
                  bbox_to_anchor = (1, 0.5),
                  frameon        = False,
                  title_fontsize = 20,
                  prop           = {'size': 18})
    
    ax.set_title(title, fontsize = 22, 
                        y        = 0.9125)

# Plot GHG emissions for different scenarios
def _plot_carbon_emissions_intesity(ax, df_, scen_labels_, 
                                    title        = '', 
                                    legend       = False, 
                                    legend_title = 'Scenario', 
                                    y_min        = None, 
                                    y_max        = None):

    for scen, zone in zip(scen_labels_['scenario'], scen_labels_['zone']):    

        data_ = df_.loc[(df_['scenario'] == scen) & (df_['load_zone'] == zone)].copy()        
        idx_  = np.argsort(data_['period'].to_numpy())
        x_    = data_['period'].to_numpy()
        y_    = data_['carbon_emissions_tons'].to_numpy()
        z_    = data_['load_mw'].to_numpy()

        ax.plot(x_[idx_], y_[idx_]/z_[idx_], 
                color     = scen_labels_.loc[scen_labels_['scenario'] == scen, 'color'].to_numpy()[0], 
                linestyle = scen_labels_.loc[scen_labels_['scenario'] == scen, 'linestyle'].to_numpy()[0],
                label     = scen_labels_.loc[scen_labels_['scenario'] == scen, 'label'].to_numpy()[0],
                marker    = scen_labels_.loc[scen_labels_['scenario'] == scen, 'marker'].to_numpy()[0],
                linewidth = scen_labels_.loc[scen_labels_['scenario'] == scen, 'linewidth'].to_numpy()[0],
                zorder    = scen_labels_.loc[scen_labels_['scenario'] == scen, 'order'].to_numpy()[0],
                alpha     = 0.75)

    ax.set_xticks(x_[idx_], x_[idx_]), 
    ax.xaxis.set_tick_params(labelsize = 18)
    ax.yaxis.set_tick_params(labelsize = 18)
    ax.set_ylabel(r'GHG Emissions Intensity (tCO$_2$/MWh)', fontsize = 20)
    #ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    
    if (y_min != None) & (y_max != None):
        ax.set_ylim(y_min, y_max)

    if legend:
        ax.legend(loc            = 'center left', 
                  title          = legend_title,
                  handlelength   = 1.75,
                  bbox_to_anchor = (1, 0.5),
                  frameon        = False,
                  title_fontsize = 20,
                  prop           = {'size': 18})
    
    ax.set_title(title, fontsize = 22, 
                        y        = 0.9125)  

# Plot clean energy fraction (%) for different scenarios
def _plot_clean_energy(ax, df_, scen_labels_, 
                       legend       = False,
                       title        = '', 
                       legend_title = 'Scenario', 
                       y_min        = None, 
                       y_max        = None):
    
    for scen, zone in zip(scen_labels_['scenario'], scen_labels_['zone']):    

        data_ = df_.loc[(df_['scenario'] == scen) & (df_['load_zone'] == zone)].copy()   
        data_ = data_.sort_values(by = ['period'])
        x_    = data_.loc[data_['technology'] == 'clean', 'period'].to_numpy()
        y_    = data_.loc[data_['technology'] == 'clean', 'power_mw'].to_numpy()
        z_    = data_.loc[data_['technology'] == 'no_clean', 'power_mw'].to_numpy()
        
        ax.plot(x_, 100.*y_/(y_ + z_), 
                color     = scen_labels_.loc[scen_labels_['scenario'] == scen, 'color'].to_numpy()[0], 
                linestyle = scen_labels_.loc[scen_labels_['scenario'] == scen, 'linestyle'].to_numpy()[0],
                label     = scen_labels_.loc[scen_labels_['scenario'] == scen, 'label'].to_numpy()[0],
                marker    = scen_labels_.loc[scen_labels_['scenario'] == scen, 'marker'].to_numpy()[0],
                linewidth = scen_labels_.loc[scen_labels_['scenario'] == scen, 'linewidth'].to_numpy()[0], 
                zorder    = scen_labels_.loc[scen_labels_['scenario'] == scen, 'order'].to_numpy()[0],
                alpha     = 0.75)
    
    ax.set_xticks(x_, x_)
    ax.xaxis.set_tick_params(labelsize = 18)
    ax.yaxis.set_tick_params(labelsize = 18)
    ax.set_ylabel(r'Clean Energy (%)', fontsize = 20)
    #ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))

    if (y_min != None) & (y_max != None):
        ax.set_ylim(y_min, y_max)
        
    if legend:
        ax.legend(loc            = 'center left', 
                  title          = legend_title,
                  handlelength   = 1.75,
                  bbox_to_anchor = (1.1, 0.5), 
                  frameon        = False,
                  title_fontsize = 20,
                  prop           = {'size': 18})
    
    ax.set_title(title, fontsize = 22, 
                        y        = 0.9125)
    
# Plot syestem losses (%) for different scenarios
def _plot_losses(ax, df_, scen_labels_, 
                 legend = False,
                 title  = '', legend_title = 'Scenario', y_min = None, y_max = None):
    
    for scen, zone in zip(scen_labels_['scenario'], scen_labels_['zone']):    

        data_ = df_.loc[(df_['scenario'] == scen) & (df_['load_zone'] == zone)].copy()   
        data_ = data_.sort_values(by = ['period'])

        x_ = data_.loc[data_['technology'] == 'gen', 'period'].to_numpy()
        y_ = data_.loc[data_['technology'] == 'tx_losses', 'power_mw'].to_numpy()
        z_ = data_.loc[data_['technology'] == 'stor_losses', 'power_mw'].to_numpy()
        w_ = data_.loc[data_['technology'] == 'gen', 'power_mw'].to_numpy()

        ax.plot(x_, - 100.*(y_ + z_)/w_, 
                color     = scen_labels_.loc[scen_labels_['scenario'] == scen, 'color'].to_numpy()[0], 
                linestyle = scen_labels_.loc[scen_labels_['scenario'] == scen, 'linestyle'].to_numpy()[0],
                label     = scen_labels_.loc[scen_labels_['scenario'] == scen, 'label'].to_numpy()[0],
                marker    = scen_labels_.loc[scen_labels_['scenario'] == scen, 'marker'].to_numpy()[0],
                zorder    = scen_labels_.loc[scen_labels_['scenario'] == scen, 'order'].to_numpy()[0],
                linewidth = scen_labels_.loc[scen_labels_['scenario'] == scen, 'linewidth'].to_numpy()[0], 
                alpha     = 0.75)
    
    ax.set_xticks(x_, x_)
    ax.xaxis.set_tick_params(labelsize = 14)
    ax.yaxis.set_tick_params(labelsize = 14)
    ax.set_ylabel(r'System Losses (%)', fontsize = 18)
    #ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))

    if (y_min != None) & (y_max != None):
        ax.set_ylim(y_min, y_max)
        
    if legend:
        ax.legend(loc            = 'center left', 
                  title          = legend_title,
                  handlelength   = 1.75,
                  bbox_to_anchor = (1, 0.5), 
                  frameon        = False,
                  title_fontsize = 18,
                  prop           = {'size': 16})
    
    ax.set_title(title, fontsize = 18, 
                        y        = 0.9125)
    
# Plot land use (MHa) for different scenarios
def _plot_land_use(ax, df_, scen_labels_, 
                   ylabel       = r'Land Use (MHa)',
                   units        = 1e6,
                   legend       = False,
                   title        = '', 
                   legend_title = 'Scenario', 
                   y_min        = None, 
                   y_max        = None):
    
    df_p_ = df_[['period', 'scenario', 'load_zone', 'area_m2']].copy()
    df_p_ = df_p_.groupby(['period', 'scenario', 'load_zone']).sum().reset_index(drop = False)

    for scen, zone in zip(scen_labels_['scenario'], scen_labels_['zone']):    

        data_ = df_p_.loc[(df_p_['scenario'] == scen) & (df_p_['load_zone'] == zone)].copy()   
        data_ = data_.sort_values(by = ['period'])

        x_ = data_['period'].to_numpy()
        y_ = data_['area_m2'].to_numpy()

        ax.plot(x_, 0.0001*y_/units, 
                color     = scen_labels_.loc[scen_labels_['scenario'] == scen, 'color'].to_numpy()[0], 
                linestyle = scen_labels_.loc[scen_labels_['scenario'] == scen, 'linestyle'].to_numpy()[0],
                label     = scen_labels_.loc[scen_labels_['scenario'] == scen, 'label'].to_numpy()[0],
                marker    = scen_labels_.loc[scen_labels_['scenario'] == scen, 'marker'].to_numpy()[0],
                zorder    = scen_labels_.loc[scen_labels_['scenario'] == scen, 'order'].to_numpy()[0],
                linewidth = scen_labels_.loc[scen_labels_['scenario'] == scen, 'linewidth'].to_numpy()[0], 
                alpha     = 0.75)
    
    ax.set_xticks(x_, x_)
    ax.xaxis.set_tick_params(labelsize = 14)
    ax.yaxis.set_tick_params(labelsize = 14)
    ax.set_ylabel(ylabel, fontsize = 18)
    #ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))

    if (y_min != None) & (y_max != None):
        ax.set_ylim(y_min, y_max)
        
    if legend:
        ax.legend(loc            = 'center left', 
                  title          = legend_title,
                  bbox_to_anchor = (1, 0.5),
                  handlelength   = 1.75,
                  frameon        = False,
                  title_fontsize = 18,
                  prop           = {'size': 16})
    
    ax.set_title(title, fontsize = 18, 
                        y        = 0.9125)
    
# Plot available land (%) for different scenarios
def _plot_available_land(ax, df_, scen_labels_, 
                         ylabel       = r'Total Land Used Area (%)',
                         units        = 1e6,
                         legend       = False,
                         title        = '',
                         legend_title = 'Scenario', 
                         y_min        = None, 
                         y_max        = None):
    
    df_p_ = df_[['period', 'scenario', 'load_zone', 'area_m2']].copy()
    df_p_ = df_p_.groupby(['period', 'scenario', 'load_zone']).sum().reset_index(drop = False)

    for scen, zone in zip(scen_labels_['scenario'], scen_labels_['zone']):    

        data_ = df_p_.loc[(df_p_['scenario'] == scen) & (df_p_['load_zone'] == zone)].copy()   
        data_ = data_.sort_values(by = ['period'])

        x_ = data_['period'].to_numpy()
        y_ = data_['area_m2'].to_numpy()

        ax.plot(x_, 100.*(0.0001*y_/units)/328.7, 
                color     = scen_labels_.loc[scen_labels_['scenario'] == scen, 'color'].to_numpy()[0], 
                linestyle = scen_labels_.loc[scen_labels_['scenario'] == scen, 'linestyle'].to_numpy()[0],
                label     = scen_labels_.loc[scen_labels_['scenario'] == scen, 'label'].to_numpy()[0],
                marker    = scen_labels_.loc[scen_labels_['scenario'] == scen, 'marker'].to_numpy()[0],
                zorder    = scen_labels_.loc[scen_labels_['scenario'] == scen, 'order'].to_numpy()[0],
                linewidth = scen_labels_.loc[scen_labels_['scenario'] == scen, 'linewidth'].to_numpy()[0], 
                alpha     = 0.75)
    
    ax.set_xticks(x_, x_)
    ax.xaxis.set_tick_params(labelsize = 14)
    ax.yaxis.set_tick_params(labelsize = 14)
    ax.set_ylabel(ylabel, fontsize = 18)
    #ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))

    if (y_min != None) & (y_max != None):
        ax.set_ylim(y_min, y_max)
        
    if legend:
        ax.legend(loc            = 'center left', 
                  title          = legend_title,
                  handlelength   = 1.75,
                  bbox_to_anchor = (1, 0.5), 
                  frameon        = False,
                  title_fontsize = 18,
                  prop           = {'size': 16})
    
    ax.set_title(title, fontsize = 18, 
                        y        = 0.9125)