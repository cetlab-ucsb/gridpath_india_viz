import os

import pandas as pd
import numpy as np
import itertools

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from matplotlib.lines import Line2D
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

# TODO:
# * Short the legend following the color code

plt.rcParams['legend.handlelength'] = 1
plt.rcParams['legend.handleheight'] = 1.125
#plt.rcParams["font.family"]         = "Avenir"
#mpl.rcParams['pdf.fonttype'] = 42

mpl.rcParams.update({"pdf.use14corefonts": True})

def _plot_new_and_existing_capacity(data_, scens_label_, tech_label_,
                                    units        = 1e3,
                                    units_label  = '(GW)',
                                    y_period     = 0.,
                                    y_grid_inc   = 500,
                                    div_line_len = 0.,
                                    save         = True,
                                    legend       = True,
                                    title        = '',
                                    file_name    = 'noname.pdf'):

    def __make_new_and_existing_capacit_legend(df_, techs_, colors_, ax):

        ax.bar(0., 0., 0., bottom    = 0.,
                           label     = 'Existing',
                           color     = 'None',
                           lw        = 0.,
                           hatch     = 'xx',
                           edgecolor = 'lightgray',
                           zorder    = 10)

        for tech, i_tech in zip(techs_, range(len(techs_))):
            idx_ = df_['Technology'] == tech
            if idx_.sum() > 0:
                if df_.loc[idx_, 'Power'].sum() != 0:
                    ax.bar(0., 0., 0., bottom = 0.,
                                       color  = colors_[i_tech],
                                       label  = tech,
                                       zorder = 10)

    scens_  = scens_label_['scenario'].to_list()
    labels_ = scens_label_['label'].to_list()
    zones_  = scens_label_['zone'].to_list()

    periods_ = np.sort(data_['Period'].unique())

    techs_, idx_ = np.unique(tech_label_['group'], return_index = True)
    colors_      = tech_label_.loc[tech_label_.index[idx_], 'group_color'].to_list()


    offset = 0.
    y_max  = 0
    width  = 1/(len(scens_) + 1)
    x_     = np.linspace(0, len(periods_) - 1, len(periods_))
    fig = plt.figure(figsize = (10, 7.5))
    ax  = plt.subplot(111)

    ticks_        = []
    ticks_labels_ = []
    ticks_labels_length_ = []

    offsets_  = []
    lengths_  = []
    x_period_ = []
    for scen, i_scen in zip(scens_, range(len(scens_))):

        zone = zones_[i_scen]

        df_ = data_.loc[data_['Zone'] == zone].sort_values(by = ['Period'])

        lengths_.append(len(scen))
        for period, i_period in zip(periods_, range(len(periods_))):
            if (i_scen == 0) & (i_period == 0): 
                __make_new_and_existing_capacit_legend(df_, techs_, colors_, ax)

            for tech, i_tech in zip(techs_, range(len(techs_))):
                idx_ = (df_['Zone'] == zone) & (df_['Period'] == period)
                idx_ = idx_ & (df_['Scenario'] == scen) & (df_['Technology'] == tech)
                idx_ = idx_ & (df_['Status'] == 'existing')

                if idx_.sum() == 1.:
                    power = df_.loc[idx_, 'Power'].to_numpy()[0]
                    color = tech_label_.loc[tech_label_['group'] == tech, 'group_color'] .unique()

                    ax.bar(x_[i_period], power/units, width, bottom    = offset/units,
                                                             color     = color,
                                                             lw        = 0.,
                                                             hatch     = 'x',
                                                             edgecolor = 'lightgray', zorder = 10)

                    offset += power

            for tech, i_tech in zip(techs_, range(len(techs_))):
                idx_ = (df_['Zone'] == zone) & (df_['Period'] == period) & (df_['Scenario'] == scen)
                idx_ = idx_ & (df_['Technology'] == tech) & (df_['Status'] == 'new')

                if idx_.sum() == 1.:
                    power = df_.loc[idx_, 'Power'].to_numpy()[0]
                    color = tech_label_.loc[tech_label_['group'] == tech, 'group_color'] .unique()

                    ax.bar(x_[i_period], power/units, width, bottom = offset/units,
                                                             color  = color,
                                                             zorder = 10)

                    offset += power

            if y_max < offset:
                y_max = offset

            ticks_.append(x_[i_period])
            ticks_labels_.append('{}'.format(labels_[i_scen]))
            offsets_.append(offset/units)

            ticks_labels_length_.append(len(ticks_labels_[-1]))


            offset = 0.

            x_period_.append(x_[i_period])


        x_ = x_ + .9/len(scens_)
    z_ = x_ - .9/len(scens_)

    x_period_ = np.mean(np.array(x_period_).reshape(len(scens_), len(periods_)), axis = 0)
    y_period_ = np.max(np.array(offsets_).reshape(len(scens_), len(periods_)), axis = 0)
    
    for x_period, y_period, period in zip(x_period_, y_period_, periods_):
        plt.text(x_period, (0.05*y_period_[-1] + y_period), '{}'.format(period), fontsize            = 18, 
                                                                                 weight              = 'bold',
                                                                                 horizontalalignment = 'center', 
                                                                                 verticalalignment   = 'center')

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

    ax.xaxis.set_tick_params(labelsize = 12, left = False)
    ax.yaxis.set_tick_params(labelsize = 12, left = False)

    ax.set_ylabel(units_label, fontsize = 18)
    ax.set_yticks(y_ticks_, y_ticks_)

    if legend:
        ax.legend(loc            = 'center left',
                  bbox_to_anchor = (1, 0.5),
                  frameon        = False,
                  prop           = {'size': 12})

    plt.ylim(-1.,y_period_.max()*1.2)

    plt.title(title, fontsize = 20,
                     y        = 0.912)

    ax.spines[['right', 'top', 'left', 'bottom']].set_visible(False)
    plt.grid(axis = 'y')

    if save:
        plt.savefig(file_name, bbox_inches = 'tight', dpi = 600)
        plt.show()

# Plot GHG emissions for different scenarios
def _plot_emissions(emissions_, scen_labels_, save       = False,
                                              title      = '',
                                              legend     = False,
                                              units      = 1e6,
                                              unit_label = r'GHG Emissions (MtCO$_2$)',
                                              file_name  = 'noname.pdf'):


    scens_      = scen_labels_['scenario'].to_list()
    zones_      = scen_labels_['zone'].to_list()
    colors_     = scen_labels_['color'].to_list()
    labels_     = scen_labels_['label'].to_list()
    linestyles_ = scen_labels_['linestyle'].to_list()
    markers_    = scen_labels_['marker'].to_list()

    data_ = emissions_.groupby(['Scenario', 'Period', 'Zone']).sum().reset_index(drop = False)

    fig = plt.figure(figsize = (4., 5))
    ax  = plt.subplot(111)

    for i_scen in range(len(scens_)):

        df_ = data_.loc[(data_['Scenario'] == scens_[i_scen]) & (emissions_['Zone'] == zones_[i_scen])]

        ax.plot(df_['Period'], df_['GHG']/units, color     = colors_[i_scen],
                                                 linestyle = linestyles_[i_scen],
                                                 marker    = markers_[i_scen],
                                                 label     = '{}'.format(labels_[i_scen]),
                                                 linewidth = 1.5,
                                                 alpha     = 0.75)

    x_labels_ = emissions_['Period'].unique()
    x_        = np.linspace(0, x_labels_.shape[0] - 1, x_labels_.shape[0])

    ax.set_xticks(x_, x_labels_)
    ax.xaxis.set_tick_params(labelsize = 14)
    ax.yaxis.set_tick_params(labelsize = 14)
    ax.set_ylabel(r'GHG Emissions (MtCO$_2$)', fontsize = 18)
    ax.set_ylim(df_['GHG'].min()*.9/units,df_['GHG'].max()*1.1/units)

    if legend:
        ax.legend(loc            = 'center left',
                  title          = 'Scenarios',
                  bbox_to_anchor = (1, 0.5),
                  frameon        = False,
                  title_fontsize = 16,
                  prop           = {'size': 12})

    plt.title(title, fontsize = 18,
                     y        = 0.9125)

    if save: plt.savefig(file_name, bbox_inches = 'tight',
                                    dpi         = 600)

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
                                           dpi         = 600)

    plt.show()
#
# # Plot GHG emissions for different scenarios
# def _plot_emissions(emissions_, scen_labels_, save      = False,
#                                               title     = '',
#                                               legend    = False,
#                                               units = 1e6,
#                                               unit_label = r'GHG Emissions (MtCO$_2$)',
#                                               file_name = 'noname.pdf'):
#
#
#     scens_      = scen_labels_['scenario'].to_list()
#     zones_      = scen_labels_['zone'].to_list()
#     colors_     = scen_labels_['color'].to_list()
#     labels_     = scen_labels_['label'].to_list()
#     linestyles_ = scen_labels_['linestyle'].to_list()
#
#
#     data_ = emissions_.groupby(['Scenario', 'Period', 'Zone']).sum().reset_index(drop = False)
#
#
#     fig = plt.figure(figsize = (4., 5))
#     ax  = plt.subplot(111)
#
#     for i_scen in range(len(scens_)):
#
#         df_ = data_.loc[(data_['Scenario'] == scens_[i_scen]) & (emissions_['Zone'] == zones_[i_scen])]
#
#         ax.plot(df_['Period'], df_['GHG']/units, color     = colors_[i_scen],
#                                                      linestyle = linestyles_[i_scen],
#                                                      label     = '{}'.format(labels_[i_scen]),
#                                                      linewidth = 1.5,
#                                                      alpha     = 0.75)
#
#     x_labels_ = np.sort(emissions_['Period'].unique())
#     x_        = np.linspace(0, x_labels_.shape[0] - 1, x_labels_.shape[0])
#
#     ax.set_xticks(x_, x_labels_)
#     ax.xaxis.set_tick_params(labelsize = 14)
#     ax.yaxis.set_tick_params(labelsize = 14)
#     ax.set_ylabel(unit_label, fontsize = 18)
#     #ax.set_ylim(0, 100)
#
#     if legend:
#         ax.legend(loc            = 'center left',
#                   title          = 'Scenarios',
#                   bbox_to_anchor = (1, 0.5),
#                   frameon        = False,
#                   title_fontsize = 16,
#                   prop           = {'size': 12})
#
#     plt.title(title, fontsize = 18,
#                      y        = 0.9125)
#
#     if save: plt.savefig(file_name, bbox_inches = 'tight',
#                                     dpi         = 300)
#
#     plt.show()
#

# Plot GHG emissions for different scenarios
def _plot_emissions_intensity(emissions_, scen_labels_, save       = False,
                                                        title      = '',
                                                        legend     = False,
                                                        unit_label = r'GHG Intensity (MtCO$_2$/MWh)',
                                                        file_name  = 'noname.pdf'):


    scens_      = scen_labels_['scenario'].to_list()
    zones_      = scen_labels_['zone'].to_list()
    colors_     = scen_labels_['color'].to_list()
    labels_     = scen_labels_['label'].to_list()
    linestyles_ = scen_labels_['linestyle'].to_list()
    markers_    = scen_labels_['marker'].to_list()

    data_       = emissions_.groupby(['Scenario', 'Period', 'Zone']).sum().reset_index(drop = False)

    fig = plt.figure(figsize = (4., 5))
    ax  = plt.subplot(111)

    for i_scen in range(len(scens_)):

        df_ = data_.loc[(data_['Scenario'] == scens_[i_scen]) & (emissions_['Zone'] == zones_[i_scen])]

        ax.plot(df_['Period'], df_['Intensity'], color     = colors_[i_scen],
                                                 linestyle = linestyles_[i_scen],
                                                 marker    = markers_[i_scen],
                                                 label     = '{}'.format(labels_[i_scen]),
                                                 linewidth = 1.5,
                                                 alpha     = 0.75)

    x_labels_ = np.sort(emissions_['Period'].unique())
    x_        = np.linspace(0, x_labels_.shape[0] - 1, x_labels_.shape[0])

    ax.set_xticks(x_, x_labels_)
    ax.xaxis.set_tick_params(labelsize = 14)
    ax.yaxis.set_tick_params(labelsize = 14)
    ax.set_ylabel(unit_label, fontsize = 18)
    ax.set_ylim(df_['Intensity'].min()*0.9, df_['Intensity'].max()*1.1)

    if legend:
        ax.legend(loc            = 'center left',
                  title          = 'Scenarios',
                  bbox_to_anchor = (1, 0.5),
                  frameon        = False,
                  title_fontsize = 16,
                  prop           = {'size': 12})

    plt.title(title, fontsize = 18,
                     y        = 0.9125)

    if save: plt.savefig(file_name, bbox_inches = 'tight',
                                    dpi         = 600)

    plt.show()

# Plot system cost for different scenarios
def _plot_system_cost(system_cost_, scen_labels_, save       = False,
                                                  legend     = False,
                                                  title      = '',
                                                  units      = 1,
                                                  unit_label = r'Costs (USD per MWh)',
                                                  file_name  = 'noname.pdf'):

    scens_      = scen_labels_['scenario'].to_list()
    zones_      = scen_labels_['zone'].to_list()
    colors_     = scen_labels_['color'].to_list()
    labels_     = scen_labels_['label'].to_list()
    linestyles_ = scen_labels_['linestyle'].to_list()
    markers_    = scen_labels_['marker'].to_list()
    data_       = system_cost_.groupby(['Scenario', 'Period', 'Zone']).sum().reset_index(drop = False)

    fig = plt.figure(figsize = (4, 5))
    ax  = plt.subplot(111)

    for i_scen in range(len(scens_)):
        scen  = scens_[i_scen]
        data_ = system_cost_.loc[(system_cost_['Scenario'] == scen) & (system_cost_['Zone'] == zones_[i_scen])]
        idx_  = np.argsort(data_['Period'])

        ax.plot(data_['Period'].to_numpy()[idx_], data_['LCOE'].to_numpy()[idx_],
                color     = colors_[i_scen],
                linestyle = linestyles_[i_scen],
                label     = labels_[i_scen],
                marker    = markers_[i_scen],
                linewidth = 1.5,
                alpha     = 0.75)

    x_labels_ = np.sort(system_cost_['Period'].unique())
    x_        = np.linspace(0, x_labels_.shape[0] - 1, x_labels_.shape[0])

    ax.set_xticks(x_, x_labels_)
    ax.xaxis.set_tick_params(labelsize = 14)
    ax.yaxis.set_tick_params(labelsize = 14)
    ax.set_ylabel(unit_label, fontsize = 18)
    ax.set_ylim(data_['LCOE'].min()*0.9,  data_['LCOE'].max()*1.1)

    if legend:
        ax.legend(loc            = 'center left',
                  title          = 'Scenario',
                  bbox_to_anchor = (1, 0.5),
                  frameon        = False,
                  title_fontsize = 16,
                  prop           = {'size': 12})

    plt.title(title, fontsize = 18,
                     y        = 0.9125)

    if save: plt.savefig(file_name, bbox_inches = 'tight', dpi = 600)

    plt.show()

def _plot_dispatch(data_, scens_label_, tech_label_,
                   units        = 1e6,
                   units_label  = r'Electricity Generation (TWh)',
                   y_period     = 0.,
                   y_grid_inc   = 500,
                   div_line_len = 0.,
                   save         = True,
                   legend       = True,
                   title        = '',
                   file_name    = 'noname.pdf'):

    def __make_dispatch_legend(data_, techs_, colors_, ax):
        for tech, i_tech in zip(techs_, range(len(techs_))):
            idx_ = data_['Technology'] == tech
            if idx_.sum() > 0:
                if data_.loc[idx_, 'Energy'].to_numpy().sum() != 0:
                    ax.bar(0., 0., 0., bottom = 0.,
                                       color  = colors_[i_tech],
                                       label  = tech.replace('_', ' '),
                                       zorder = 2,
                                       ec     = 'None',
                                       lw     = 0.,
                                       aa     = True)


    scens_  = scens_label_['scenario'].to_list()
    labels_ = scens_label_['label'].to_list()
    zones_  = scens_label_['zone'].to_list()

    periods_ = np.sort(data_['Period'].unique())
    techs_   = pd.unique(tech_label_['group'])

    colors_ = [tech_label_.loc[tech_label_['group'] == tech, 'group_color'].unique()[0] for tech in techs_]

    width           = 1./(len(scens_) + 1)
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
    x_period_     = []
    y_period_     = []
    offset_       = []
    for scen, i_scen in zip(scens_, range(len(scens_))):

        zone = zones_[i_scen]
        df_  = data_.loc[data_['Zone'] == zone].sort_values(by = ['Period'])

        for period, i_period in zip(periods_, range(len(periods_))):

            if (i_scen == 0) & (i_period == 0): __make_dispatch_legend(df_, techs_, colors_, ax)

            for tech, i_tech in zip(techs_, range(len(techs_))):
                idx_ = (df_['Scenario'] == scen) & (df_['Technology'] == tech) & (df_['Period'] == period)

                if idx_.sum() == 1:
                    energy = float(df_.loc[idx_, 'Energy'].to_numpy()[0])
                    color  = tech_label_.loc[tech_label_['group'] == tech, 'group_color'].unique()

                    if energy != 0:
                        if energy > 0:
                            offset = offset_positive
                        else:
                            offset = offset_negative

                        ax.bar(x_[i_period], energy/units, width, bottom = offset/units,
                                                                  color  = color,
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
            ticks_labels_.append('{}'.format(labels_[i_scen]))

            if offset_negative/units < y_min: y_min = offset_negative/units
            if offset_positive/units > y_max: y_max = offset_positive/units

            x_period_.append(x_[i_period])
            y_period_.append(offset_positive)
            offset_.append(offset_negative)
            offset_positive = 0.
            offset_negative = 0.
            #x_period_.append(x_[i_period])

            y += 1

        x_ = x_ + .9/len(scens_)
    z_ = x_ - .9/len(scens_)

    x_period_ = np.mean(np.array(x_period_).reshape(len(scens_), len(periods_)), axis = 0)
    y_period_ = np.max(np.array(y_period_).reshape(len(scens_), len(periods_)), axis = 0)

    for x_period, y_period, period in zip(x_period_, y_period_, periods_):
        plt.text(x_period, (0.05*y_period_[-1] + y_period)/units, '{}'.format(period), fontsize            = 18, 
                                                                                       weight              = 'bold',
                                                                                       horizontalalignment = 'center', 
                                                                                       verticalalignment   = 'center')

    ax.set_xticks(ticks_, ticks_labels_, rotation = 90)
    ax.xaxis.set_tick_params(labelsize = 12, left = False)

    N_steps  = int(np.ceil((y_max/units)/y_grid_inc))
    y_ticks_ = np.linspace(0, int(N_steps*y_grid_inc), N_steps + 1, dtype = int)

    ax.set_ylabel(units_label, fontsize = 18)
    ax.set_yticks(y_ticks_, y_ticks_)
    ax.yaxis.set_tick_params(labelsize = 12, left = False)

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

    if legend:
        ax.legend(loc            = 'center left',
                  bbox_to_anchor = (1, 0.5),
                  frameon        = False,
                  prop           = {'size': 12})

    plt.title(title, fontsize = 18,
                     y        = 0.9125)

    ax.spines[['right', 'top', 'left', 'bottom']].set_visible(False)
    ax.grid(axis = 'y')

    if save:
        plt.savefig(file_name, bbox_inches = 'tight',
                               dpi         = 600)

    plt.show()
    
# Plot energy dispatch for a given day
def _plot_zone_energy_dispatch(ed_, scen_labels_, tech_labels_, dispatch_labels_, units     = 1e3,
                                                                                  save      = False, 
                                                                                  legend    = False,
                                                                                  file_name = 'noname.pdf'):
     
    def __processing(ed_, scen, zone, period, month, day):
        idx_ = (ed_['day'] == day) & (ed_['month'] == month)
        idx_ = idx_ & (ed_['period'] == period) & (ed_['scenario'] == scen) & (ed_['load_zone'] == zone)
        return ed_.loc[idx_].reset_index(drop = True)

    x_  = np.linspace(0, 23, 24)
    ed_p_ = ed_.loc[~(ed_['technology'] == 'Tx_Losses')].reset_index(drop = True).copy()

    N_plots = dispatch_labels_.shape[0]

    N_y = N_plots // 4

    if N_y > 0:
        N_x = 4
    else:
        N_x = N_plots

    fig = plt.figure(figsize = (N_x*7.5, (N_y + 1)*4))
    
    index_ = []
    for i in range(N_y + 1):
        for j in range(N_x):
            index_.append([i, j])   

    for k in range(dispatch_labels_.shape[0]):     

        row_       = dispatch_labels_.iloc[k]
        scen       = row_['scenario']
        zone       = row_['load_zone']
        period     = row_['period']
        month      = row_['month']
        day        = row_['day']
        scen_label = row_['label']

        ed_pp_ = __processing(ed_p_.copy(), scen, zone, period, month, day)

        zone_p = zone.replace('_', ' ')

        ax = plt.subplot2grid((N_y + 1, N_x), (index_[k][0], index_[k][1]))
        ax.set_title(f'{zone_p} ({month:02}/{day:02}/{period})\n{scen_label}', fontsize = 16)
        
        all_colors_ = []
        legend_     = []
        y_          = []
        for tech in tech_labels_['group'].unique():
            ed_ppp_ = ed_pp_.loc[ed_pp_['technology'] == tech, 'power_mw'].to_numpy()/units
            idx_    = ed_ppp_ > 0.

            if idx_.sum() > 0.:
                y_p_       = np.zeros((ed_ppp_.shape[0],))
                y_p_[idx_] = ed_ppp_[idx_]
                color      = tech_labels_.loc[tech_labels_['group']== tech, 'group_color'].to_numpy()[0]
                all_colors_.append(color)
                y_.append(y_p_)

                ax.bar(0., 0., 0., bottom    = 0. ,
                                   label     = tech,
                                   color     = color,
                                   lw        = 0.,
                                   edgecolor = "None", 
                                   zorder    = 10)

        ax.stackplot(x_, np.vstack(y_), colors = all_colors_, 
                                        zorder = 10, 
                                        lw     = 0.)
    
        all_colors_ = []
        y_          = []
        for tech in tech_labels_['group'].unique():
            ed_ppp_ = ed_pp_.loc[ed_pp_['technology'] == tech, 'power_mw'].to_numpy()/units
            idx_    = ed_ppp_ < 0.
    
            if idx_.sum() > 0.:
                y_p_       = np.zeros((ed_ppp_.shape[0],))
                y_p_[idx_] = ed_ppp_[idx_]
                color      = tech_labels_.loc[tech_labels_['group']== tech, 'group_color'].to_numpy()[0]
    
                all_colors_.append(color)
                y_.append(y_p_)
    
        ax.bar(0., 0., 0., bottom    = 0. ,
                           label     = 'Exports',
                           color     = '#900C3F',
                           lw        = 0.,
                           hatch     = 'xx', 
                           edgecolor = 'lightgray', 
                           zorder    = 10)
        
        ax.bar(0., 0., 0., bottom    = 0. ,
                           label     = 'Charge',
                           color     = 'None',
                           lw        = 0.,
                           hatch     = 'xx', 
                           edgecolor = 'lightgray', 
                           zorder    = 10)
        if len(y_) > 0.:    
            ax.stackplot(x_, np.vstack(y_), colors    = all_colors_, 
                                             zorder    = 10, 
                                             hatch     = 'xx', 
                                             edgecolor = 'lightgrey', 
                                             lw        = 0.)
    
        load_ = ed_pp_.loc[ed_pp_['technology'] == 'Load', 'power_mw'].to_numpy()/units
    
        ax.plot(x_, load_, color     = 'r', 
                           linestyle = '--', 
                           label     = 'Demand',
                           lw        = 1.75, 
                           alpha     = 1., 
                           zorder    = 11)

        if index_[k][1] == 0: ax.set_ylabel(r'Energy (GWh)', fontsize = 16)
    
        
        ax.grid(axis = 'y')
        ax.set_xticks(x_, [f'{x.astype(int)}:00' for x in x_], rotation = 90)
    
        ax.xaxis.set_tick_params(labelsize = 12)
        ax.yaxis.set_tick_params(labelsize = 12)
    
        ax.axhline(0, linewidth = .5, 
                      linestyle = '-', 
                      color     = 'k', 
                      clip_on   = False, 
                      zorder    = 10)

    
        ax.set_xlim(0, 23)
        
    if legend:
        ax.legend(loc            = 'center left', 
                  bbox_to_anchor = (1.1, 0.475),
                  frameon        = False,
                  prop           = {'size': 14})

    if N_y > 0:
        plt.tight_layout(w_pad = -15)
    else:
        plt.tight_layout()

    if save: plt.savefig(file_name, bbox_inches = 'tight', 
                                    dpi         = 600)
    plt.show()
    
# Plot energy dispatch for a given day
def _plot_zone_energy_dispatch_production(ed_, scen_labels_, tech_labels_, dispatch_labels_, units     = 1e3,
                                                                                             save      = False, 
                                                                                             legend    = False,
                                                                                             file_name = 'noname.pdf'):
     
    figures_ = dispatch_labels_['subplot'].unique()
    N_plots  = len(figures_)

    N_x = 2
    N_y = N_plots // N_x

    if N_y > 0:
        N_x = N_x
    else:
        N_x = N_plots

    fig = plt.figure(figsize = (N_x*10, (N_y + 1)*5))
    
    index_ = []
    for i in range(N_y + 1):
        for j in range(N_x):
            index_.append([i, j])   

    for k in figures_:   
        timepoints_ = dispatch_labels_.loc[dispatch_labels_['subplot'] == k, 'timepoint'].to_list()
        scen        = dispatch_labels_.loc[dispatch_labels_['subplot'] == k, 'scenario'].to_list()[0]
        load_zone   = dispatch_labels_.loc[dispatch_labels_['subplot'] == k, 'load_zone'].to_list()[0]
        
        k -= 1

        ed_pp_ = ed_.loc[ed_['timepoint'].isin(timepoints_)]

        ax = plt.subplot2grid((N_y + 1, N_x), (index_[k][0], index_[k][1]))
        #ax.set_title(f'({month:02}/{day:02}/{period})\n{scen_label}', fontsize = 16)
        
        all_colors_ = []
        legend_     = []
        y_          = []
        for tech in tech_labels_['group'].unique():
            idx_    = (ed_pp_['technology'] == tech) & (ed_pp_['scenario'] == scen) & (ed_pp_['load_zone'] == load_zone)
            ed_ppp_ = ed_pp_.loc[idx_, 'power_mw'].to_numpy()/units
            idx_    = ed_ppp_ > 0.

            if idx_.sum() > 0.:
                y_p_       = np.zeros((ed_ppp_.shape[0],))
                y_p_[idx_] = ed_ppp_[idx_]
                color      = tech_labels_.loc[tech_labels_['group']== tech, 'group_color'].to_numpy()[0]
                all_colors_.append(color)
                y_.append(y_p_)

                ax.bar(0., 0., 0., bottom    = 0. ,
                                   label     = tech,
                                   color     = color,
                                   lw        = 0.,
                                   edgecolor = "None", 
                                   zorder    = 10)

        ax.stackplot(timepoints_, np.vstack(y_), colors = all_colors_, 
                                        zorder = 10, 
                                        lw     = 0.)
    
        all_colors_ = []
        y_          = []
        for tech in tech_labels_['group'].unique():
            idx_    = (ed_pp_['technology'] == tech) & (ed_pp_['scenario'] == scen) & (ed_pp_['load_zone'] == load_zone)
            ed_ppp_ = ed_pp_.loc[idx_, 'power_mw'].to_numpy()/units
            idx_    = ed_ppp_ < 0.
    
            if idx_.sum() > 0.:
                y_p_       = np.zeros((ed_ppp_.shape[0],))
                y_p_[idx_] = ed_ppp_[idx_]
                color      = tech_labels_.loc[tech_labels_['group']== tech, 'group_color'].to_numpy()[0]

                all_colors_.append(color)
                y_.append(y_p_)
    
        ax.bar(0., 0., 0., bottom    = 0. ,
                           label     = 'Export',
                           color     = '#900C3F',
                           lw        = 0.,
                           hatch     = 'xx', 
                           edgecolor = 'lightgray', 
                           zorder    = 10)
        
        ax.bar(0., 0., 0., bottom    = 0. ,
                           label     = 'Charge',
                           color     = 'None',
                           lw        = 0.,
                           hatch     = 'xx', 
                           edgecolor = 'lightgray', 
                           zorder    = 10)
        
        if len(y_) > 0.:    
            ax.stackplot(timepoints_, np.vstack(y_), colors    = all_colors_, 
                                             zorder    = 10, 
                                             hatch     = 'xx', 
                                             edgecolor = 'lightgrey', 
                                             lw        = 0.)
        idx_  = (ed_pp_['technology'] == 'Load') & (ed_pp_['scenario'] == scen) & (ed_pp_['load_zone'] == load_zone)
        load_ = ed_pp_.loc[idx_, 'power_mw'].to_numpy()/units
    
        ax.plot(timepoints_, load_, color     = 'r', 
                           linestyle = '--', 
                           label     = 'Demand',
                           lw        = 1.75, 
                           alpha     = 1., 
                           zorder    = 11)

        if index_[k][1] == 0: ax.set_ylabel(r'Energy (GWh)', fontsize = 16)
    
        
        ax.grid(axis = 'y')
        ax.set_xticks(timepoints_[::2], timepoints_[::2], rotation = 90)
    
        ax.xaxis.set_tick_params(labelsize = 12)
        ax.yaxis.set_tick_params(labelsize = 12)
    
        ax.axhline(0, linewidth = .5, 
                      linestyle = '-', 
                      color     = 'k', 
                      clip_on   = False, 
                      zorder    = 10)
    
        ax.set_xlim(timepoints_[0], timepoints_[-1])
        
    if legend:
        ax.legend(loc            = 'center left', 
                  bbox_to_anchor = (1.1, 0.475),
                  frameon        = False,
                  prop           = {'size': 14})

    # if N_y > 0:
    #     plt.tight_layout(w_pad = -1)
    # else:
    plt.tight_layout()

    if save: 
        plt.savefig(file_name, bbox_inches = 'tight', 
                               dpi         = 600)
    plt.show()

__all__ = ['_plot_new_and_existing_capacity',
           '_plot_emissions_intensity',
           '_plot_emissions',
           '_plot_system_cost',
           '_plot_dispatch', 
           '_plot_zone_energy_dispatch', 
           '_plot_zone_energy_dispatch_production']
