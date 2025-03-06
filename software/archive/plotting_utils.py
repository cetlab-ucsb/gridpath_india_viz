import os

import pandas as pd
import numpy as np
import itertools
import geopandas as gpd

import textalloc as ta
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from matplotlib.lines import Line2D
from adjustText import adjust_text
from shapely.ops import cascaded_union
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

# TODO:
# * Short the legend following the color code

plt.rcParams['legend.handlelength'] = 1
plt.rcParams['legend.handleheight'] = 1.125
plt.rcParams["font.family"]         = "Avenir"
#mpl.rcParams['pdf.fonttype'] = 42

mpl.rcParams.update({"pdf.use14corefonts": True})

tech_colors_  = pd.DataFrame(columns = ['color'], 
                             index   = ['Battery', 'Hydrogen', 'WHR',  'Nuclear', 
                                        'Biomass', 'Hydro_Pumped', 'Hydro_ROR', 'Hydro_Storage', 
                                        'Diesel', 'CCGT', 'CT', 'Subcritical_Coal_Large', 
                                        'Subcritical_Coal_Small', 'Supercritical_Coal', 'SolarPV_tilt', 'SolarPV_single', 
                                        'Wind', 'Export', 'Curtailment', 'Tx_Losses', 'Import'])

tech_colors_['color'] = ['#e7c41f', 'teal', '#6ba661', '#8d72b3', 
                         '#6a96ac', '#2a648a', '#2a648a', '#2a648a', 
                         '#924B00', '#6c757d', '#6c757d', '#343a40', 
                         '#343a40', '#343a40', '#ef9226', '#daac77', 
                         '#8dc0cd', '#55A182', '#c94f39', '#656d4a', '#900C3F']

color_groups_  = pd.DataFrame(columns = ['color'], 
                             index   = ['Battery', 'Hydrogen', 'Other',  'Nuclear', 
                                        'Pumped Storage', 'Hydro', 'Diesel', 'Gas', 
                                        'Coal', 'Solar', 'Wind', 'Export', 
                                        'Curtailment', 'Tx_Losses', 'Import'])

color_groups_['color'] = ['#e7c41f', 'teal', '#6ba661', '#8d72b3', 
                          '#6a96ac', '#2a648a', '#924B00', '#6c757d', 
                          '#343a40', '#ef9226', '#8dc0cd', '#55A182', 
                          '#c94f39', '#656d4a', '#900C3F']

scen_colors_ = pd.DataFrame(columns = ['color', 'lines'], 
                            index   = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'])
    
scen_colors_['color'] = ['#92918B', '#126463', '#521A1A', '#2CB7B5', '#756A00', '#CA8250', '#D8A581', '#1F390D', '#900C3F']
scen_colors_['lines'] = ['solid', 'solid', 'dotted', 'dotted', 'dashed', 'dashed', 'dashdot', 'dashdot', 'dashdot']





# Plot new and existing capacity for different scenarios
def _plot_new_and_existing_capacity(data_, scens_, scens_label_, colors_, zone, y_period     = 0.,
                                                                                y_grid_inc   = 500,
                                                                                div_line_len = 0.,
                                                                                save         = True, 
                                                                                legend       = True,
                                                                                path         = '',
                                                                                title        = '',
                                                                                file_name    = 'noname.pdf'):
                                                                     
    def __make_new_and_existing_capacit_legend(techs_, data_, colors_, ax, zone):
                    
        ax.bar(0., 0., 0., bottom = 0., 
                           label     = 'Existing',
                           color     = 'None',
                           lw        = 0.,
                           hatch     = 'xx', 
                           edgecolor = 'lightgray', 
                           zorder    = 10)
                    
        for tech, i_tech in zip(techs_, range(len(techs_))):      
            idx_ = (data_['Technology'] == tech) & (data_['Zone'] == zone) 
            if idx_.sum() > 1:
                if data_.loc[idx_, 'Power'].to_numpy()[0] != 0:
                    ax.bar(0., 0., 0., bottom = 0., 
                                       color  = colors_.loc[tech], 
                                       label  = tech.replace('_', ' '), 
                                       zorder = 10)
                    
    data_    = data_.loc[data_['Zone'] == zone].sort_values(by = ['Period'])
    periods_ = np.sort(data_['Period'].unique())
    techs_   = colors_.index

    offset = 0.
    units  = 1e3
    y_max  = 0
    width  = .8/len(scens_)
    x_     = np.linspace(0, len(periods_) - 1, len(periods_))
    fig = plt.figure(figsize = (10, 7.5))
    ax  = plt.subplot(111)
        
    ticks_        = []
    ticks_labels_ = []
    ticks_labels_length_ = []
    
    offsets_  = []
    lengths_  = []
    x_period_ = [[] for _ in range(len(periods_))]
    
    for scen, i_scen in zip(scens_, range(len(scens_))):

        lengths_.append(len(scen))
        print(scen)

        for period, i_period in zip(periods_, range(len(periods_))):
            if (i_scen == 0) & (i_period == 0): __make_new_and_existing_capacit_legend(techs_, data_, colors_, ax, zone)

            for tech, i_tech in zip(techs_, range(len(techs_))):
                idx_ = (data_['Zone'] == zone) & (data_['Period'] == period)
                idx_ = idx_ & (data_['Scenario'] == scen) & (data_['Technology'] == tech)
                idx_ = idx_ & (data_['Status'] == 'existing')
                
                if idx_.sum() == 1.:
                    power = data_.loc[idx_, 'Power'].to_numpy()[0]
                    ax.bar(x_[i_period], power/units, width, bottom    = offset/units, 
                                                             color     = colors_.loc[tech], 
                                                             lw        = 0.,
                                                             hatch     = 'x', 
                                                             edgecolor = 'lightgray', zorder = 10)

                    offset += power
            
            for tech, i_tech in zip(techs_, range(len(techs_))):
                idx_ = (data_['Zone'] == zone) & (data_['Period'] == period) & (data_['Scenario'] == scen) 
                idx_ = idx_ & (data_['Technology'] == tech) & (data_['Status'] == 'new')

                if idx_.sum() == 1.:
                    power = data_.loc[idx_, 'Power'].to_numpy()[0]
                    ax.bar(x_[i_period], power/units, width, bottom = offset/units, 
                                                             color  = colors_.loc[tech], 
                                                             zorder = 10)

                    offset += power
                
            if y_max < offset: 
                y_max = offset
                            
            ticks_.append(x_[i_period]) 
            ticks_labels_.append('{}'.format(scens_label_[i_scen]))
            offsets_.append(offset)
            
            ticks_labels_length_.append(len(ticks_labels_[-1]))
            
            
            offset = 0.
        
            x_period_[i_period].append(x_[i_period])
        x_ = x_ + .9/len(scens_)
    z_ = x_ - .9/len(scens_)
    
    dx_period = (x_period_[0][1] - x_period_[0][0])/len(scens_)
    x_period_ = [np.mean(x_period) - dx_period for x_period in x_period_]
    for x_period, period in zip(x_period_, periods_):
        plt.text(x_period, y_period, '{}'.format(period), fontsize = 14)

    x_ = np.linspace(0, len(periods_), len(periods_) + 1)
    dz = (x_[1] - z_[0])
    for x in x_:
        ax.axvline(x - dz/2., ymin      = div_line_len, 
                              ymax      = 0., 
                              linewidth = .75, 
                              linestyle = '-', 
                              color     = 'k', 
                              clip_on   = False, 
                              zorder    = 10)
    N_steps  = int(np.ceil((y_max/units)/y_grid_inc))
    y_ticks_ = np.linspace(0, int(N_steps*y_grid_inc), N_steps + 1, dtype = int)
    ax.set_xticks(ticks_, ticks_labels_, rotation = 90)
    ax.set_yticks(y_ticks_, y_ticks_)

    ax.xaxis.set_tick_params(labelsize = 12, left = False)
    ax.yaxis.set_tick_params(labelsize = 12, left = False)
    
    ax.set_ylabel(r'Existing & New Capacity (GW)', fontsize = 18)
    
    if legend:
        ax.legend(loc            = 'center left', 
                  bbox_to_anchor = (1, 0.5),
                  frameon        = False,
                  prop           = {'size': 12})

    plt.ylim(-10., (np.max(offsets_) + 0.075*np.max(offsets_))/units)
    
    plt.title(title, fontsize = 20, 
                     y        = 0.912)

    ax.spines[['right', 'top', 'left', 'bottom']].set_visible(False)
    plt.grid(axis = 'y')
    
    if save: 
        plt.savefig(path + file_name, bbox_inches = 'tight', dpi = 300)
        plt.show()
    
# Plot GHG emissions for different scenarios
def _plot_emissions(emissions_, scens_, scen_labels_, colors_, zone, save      = False, 
                                                                     title     = '', 
                                                                     legend    = False,
                                                                     path      = '', 
                                                                     file_name = 'noname.pdf'):
    
    units = 1e6
                                                     
    fig = plt.figure(figsize = (4., 5))
    ax  = plt.subplot(111)
    
    for i_scen in range(len(scens_)):
        
        idx_  = (emissions_['Scenario'] == scens_[i_scen]) & (emissions_['Zone'] == zone)
        data_ = emissions_.loc[idx_]
        
        ax.plot(data_['Period'], data_['GHG']/units, color     = colors_.loc['C{}'.format(i_scen + 1), 'color'], 
                                                     linestyle = colors_.loc['C{}'.format(i_scen + 1), 'lines'],
                                                     label     = '{}'.format(scen_labels_[i_scen]),
                                                     linewidth = 1.5, 
                                                     alpha     = 0.75)

    x_labels_ = emissions_['Period'].unique()
    x_        = np.linspace(0, x_labels_.shape[0] - 1, x_labels_.shape[0])

    ax.set_xticks(x_, x_labels_)
    ax.xaxis.set_tick_params(labelsize = 14)
    ax.yaxis.set_tick_params(labelsize = 14)
    ax.set_ylabel(r'GHG Emissions (MtCO$_2$)', fontsize = 18)
    #ax.set_ylim(0, 100)

    if legend:
        ax.legend(loc            = 'center left', 
                  title          = 'Scenarios',
                  bbox_to_anchor = (1, 0.5),
                  frameon        = False,
                  title_fontsize = 16,
                  prop           = {'size': 12})
    
    plt.title(title, fontsize = 18, 
                     y        = 0.9125)

    if save: plt.savefig(path + file_name, bbox_inches = 'tight', 
                                           dpi         = 300)

    plt.show()
    
    
# Plot system cost for different scenarios
def _plot_system_cost(system_cost_, scens_, scen_lables_, colors_, zone, save      = False, 
                                                                         legend    = False,
                                                                         title     = '', 
                                                                         path      = '', 
                                                                         file_name = 'noname.pdf'):

    fig = plt.figure(figsize = (4, 5))
    ax  = plt.subplot(111)
    
    for i_scen in range(len(scens_)):
        scen  = scens_[i_scen]
        data_ = system_cost_.loc[(system_cost_['Scenario'] == scen) & (system_cost_['Zone'] == zone)]
        idx_  = np.argsort(data_['Period'])

        ax.plot(data_['Period'].to_numpy()[idx_], data_['LCOE'].to_numpy()[idx_], 
                color     = colors_.loc['C{}'.format(i_scen + 1), 'color'],                                                 
                linestyle = colors_.loc['C{}'.format(i_scen + 1), 'lines'],                                                 
                label     = '{}'.format(scen_lables_[i_scen]),                                                             
                linewidth = 1.5,                                                                  
                alpha     = 0.75) 
    
    x_labels_ = np.sort(system_cost_['Period'].unique())
    x_        = np.linspace(0, x_labels_.shape[0] - 1, x_labels_.shape[0])
    
    ax.set_xticks(x_, x_labels_)
    ax.xaxis.set_tick_params(labelsize = 14)
    ax.yaxis.set_tick_params(labelsize = 14)
    ax.set_ylabel(r'Costs (USD per MWh)', fontsize = 18)
    #ax.set_ylim(40, 75)

    if legend:
        ax.legend(loc            = 'center left', 
                  title          = 'Scenario',
                  bbox_to_anchor = (1, 0.5), 
                  frameon        = False,
                  title_fontsize = 16,
                  prop           = {'size': 12})
    
    plt.title(title, fontsize = 18, 
                     y        = 0.9125)

    #plt.ylim(data_.min() - 0.035*data_.min(), data_.max() + 0.035*data_.max())

    if save: plt.savefig(path + file_name, bbox_inches = 'tight', 
                                           dpi         = 300)

    plt.show()

    
# Plot energy dispatch per technology for different scenarios
def _plot_dispatch(data_, scens_, scens_labels_, colors_, zone, save         = False, 
                                                                legend       = False,
                                                                y_period     = -1500,
                                                                y_grid_inc   = 500,
                                                                div_line_len = 0.,
                                                                title        = '',
                                                                path         = '', 
                                                                file_name    = 'noname.pdf'):

    def __make_dispatch_legend(techs_, data_, colors_, ax, zone):
        for tech, i_tech in zip(techs_, range(len(techs_))):      
            idx_ = (data_['Technology'] == tech) & (data_['Zone'] == zone) 
            if idx_.sum() > 1:
                if data_.loc[idx_, 'Energy'].to_numpy()[0] != 0:
                    ax.bar(0., 0., 0., bottom = 0., 
                                       color  = colors_.loc[tech], 
                                       label  = tech.replace('_', ' '),
                                       zorder = 2, 
                                       ec     = 'None',
                                       lw     = 0., 
                                       aa     = True)
                
    data_    = data_.loc[data_['Zone'] == zone]
    periods_ = np.sort(data_['Period'].unique())
    techs_   = colors_.index

    units           = 1e6
    width           = .8/len(scens_)
    offset_positive = 0.
    offset_negative = 0.
    y               = 0
    y_max           = 0
    y_min           = 0
    
    x_  = np.linspace(0, len(periods_) - 1, len(periods_))

    fig = plt.figure(figsize = (10., 7.5))
    ax  = plt.subplot(111)
    
    ticks_        = []
    ticks_labels_ = []
    x_period_     = [[] for _ in range(len(periods_))]

    for scen, i_scen in zip(scens_, range(len(scens_))):
        for period, i_period in zip(periods_, range(len(periods_))):
            
            if (i_scen == 0) & (i_period == 0): __make_dispatch_legend(techs_, data_, colors_, ax, zone)
            
            for tech, i_tech in zip(techs_, range(len(techs_))):
                idx_ = (data_['Scenario'] == scen) & (data_['Technology'] == tech) & (data_['Period'] == period)
                idx_ = idx_& (data_['Zone'] == zone) 
                
                if idx_.sum() == 1:
                    energy = data_.loc[idx_, 'Energy'].to_numpy()[0]

                    if energy != 0:
                        if energy > 0:
                            offset = offset_positive
                        else:
                            offset = offset_negative


                        ax.bar(x_[i_period], energy/units, width, bottom = offset/units, 
                                                                  color  = colors_.loc[tech],
                                                                  zorder = 2, 
                                                                  ec     = 'None', 
                                                                  lw     = 0., 
                                                                  aa     = True)

                        if energy >= 0:
                            offset_positive += energy
                        else:
                            offset_negative += energy
                            
                if y_max < offset_positive: 
                    y_max = offset_positive
                
            ticks_.append(x_[i_period]) 
            ticks_labels_.append('{}'.format(scens_labels_[i_scen]))

            if offset_negative/units < y_min: y_min = offset_negative/units
            if offset_positive/units > y_max: y_max = offset_positive/units

            offset_positive = 0.
            offset_negative = 0.
            x_period_[i_period].append(x_[i_period])

            y += 1

        x_ = x_ + .9/len(scens_)

    z_ = x_ - .9/len(scens_)

    # for x, period in zip(x_, periods_):
    #     plt.text(x + dz + dx, -np.max(ticks_labels_length_)*71 + dy, '{}'.format(period), fontsize = 14)
    dx_period = (x_period_[0][1] - x_period_[0][0])/len(scens_)
    x_period_ = [np.mean(x_period) - dx_period for x_period in x_period_]
    for x_period, period in zip(x_period_, periods_):
        plt.text(x_period, y_period, '{}'.format(period), fontsize = 14)
        
    x_ = np.linspace(0, len(periods_), len(periods_) + 1)
    dz = (x_[1] - z_[0])
    for x in x_:
        ax.axvline(x - dz/2., ymin      = div_line_len, 
                              ymax      = 0., 
                              linewidth = .75, 
                              linestyle = '-', 
                              color     = 'k', 
                              clip_on   = False, 
                              zorder    = 10)
    
    N_steps  = int(np.ceil((y_max/units)/y_grid_inc))
    y_ticks_ = np.linspace(0, int(N_steps*y_grid_inc), N_steps + 1, dtype = int)
    ax.set_xticks(ticks_, ticks_labels_, rotation = 90)
    ax.set_yticks(y_ticks_[:-1], y_ticks_[:-1])

    ax.xaxis.set_tick_params(labelsize = 12, left = False)
    ax.yaxis.set_tick_params(labelsize = 12, left = False)
    
    ax.set_ylabel('Electricity Generation (TWh)', fontsize = 18)
        
    if legend:
        ax.legend(loc            = 'center left', 
                  bbox_to_anchor = (1, 0.5), 
                  frameon        = False, 
                  prop           = {'size': 12})
        
    plt.title(title.replace('_', ' '), fontsize = 18, 
                                       y        = 0.9125)

    ax.spines[['right', 'top', 'left', 'bottom']].set_visible(False)
    ax.grid(axis = 'y')
        
    if save: 
        plt.savefig(path + file_name, bbox_inches = 'tight', 
                                      dpi         = 350)
        
    plt.show()
    
    
    
__all__ = ['_plot_new_and_existing_capacity', 
           '_plot_emissions',
           '_plot_system_cost',
           '_plot_dispatch']
