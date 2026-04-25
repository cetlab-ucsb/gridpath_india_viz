# create energy plots

# inputs -----------------

  args = commandArgs(trailingOnly = TRUE)
  db_dir          = args[1]
  sel_scenario    = args[2]
  # sel_scenario    = 'RPS10_VRElow_SThigh_CONVhigh'
  # db_dir          = '0801'
  data_fname      = '_energy_data_all_zones.csv'

# load packages --------

  library(data.table)
  library(ggplot2)
  library(hrbrthemes)
  library(extrafont)

# read in data -------

  dt_energy = fread(here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', paste0(sel_scenario, data_fname)), header = T)
  keycols = c('load_zone', 'technology', 'timepoint')
  setkeyv(dt_energy, keycols)

# recategorize fuels -------
  
  dt_energy[technology %like% 'Coal', type := 'Coal']
  dt_energy[is.na(type), type := technology]

# aggregate by type ------
  
  energy_agg = dt_energy[, .(energy_mwh = sum(power_mw*timepoint_weight, na.rm = T)), by = .(scenario, load_zone, period, type)]
  
# aggregate to country level -------
  
  energy_tot = dt_energy[, .(energy_mwh = sum(power_mw*timepoint_weight, na.rm = T)), by = .(scenario, period, type)]
  
# reorder levels --------
  
  energy_agg = energy_agg[, type := factor(type, levels = c("Battery",
                                                            "Hydro_Pumped",
                                                            "Wind",
                                                            "Solar",
                                                            "Hydro_Storage",
                                                            "Hydro_ROR",
                                                            "CT",
                                                            "CCGT",
                                                            "Biomass",
                                                            "WHR",
                                                            "Diesel",
                                                            "Subcritical_Oil",
                                                            "Coal",
                                                            "Nuclear"))]
  
  energy_tot = energy_tot[, type := factor(type, levels = c("Battery",
                                                            "Hydro_Pumped",
                                                            "Wind",
                                                            "Solar",
                                                            "Hydro_Storage",
                                                            "Hydro_ROR",
                                                            "CT",
                                                            "CCGT",
                                                            "Biomass",
                                                            "WHR",
                                                            "Diesel",
                                                            "Subcritical_Oil",
                                                            "Coal",
                                                            "Nuclear"))]

# get list of loadzones -------
  
  loadzones = unique(energy_agg[, load_zone])

# ------------------------------- plot -------------------------------
  
  # color palettes ------
  
    pal_fuel  = c("Biomass"= "#8c613c",
                  "Coal" = "#414141",
                  "CCGT" = "#c44e52",
                  "CT" = "#fb9a99",
                  "Diesel" = "#eb8a19",
                  "Subcritical_Oil" = "#fdbf6f",
                  "Hydro_Pumped" = "#0080b4",
                  "Hydro_ROR" = "#193e64",
                  "Hydro_Storage" = "#3a6ea3",
                  "Nuclear" = "#55a868",
                  "Solar" = "#ff7f00",
                  "Wind" = "#86afb5",              
                  "Curtailment_Variable" = "#cd563e",
                  "Curtailment_Hydro" = "#80b1d3",
                  "Battery" = "#6a3d9a",
                  "WHR" = "#858585",
                  "Imports" = "#aaaeb4")
    
  # theme -------
  
    theme_line = theme_ipsum(base_family = 'Secca Soft',
                             grid = 'Y', 
                             plot_title_size = 18, 
                             subtitle_size = 18,
                             axis_title_just = 'center',
                             axis_title_size = 18, 
                             axis_text_size = 16,
                             strip_text_size = 16)  +
      theme(plot.title = element_text(hjust = 0, face = 'bold'),
            plot.title.position = 'plot',
            plot.subtitle = element_text(hjust = 0),
            plot.caption = element_text(size = 10, color = '#5c5c5c', face = 'plain'),
            axis.line.x = element_line(color = 'black'),
            axis.ticks.x = element_line(color = 'black'),
            axis.ticks.length.x = unit(0.25, "cm"),
            axis.text.y = element_text(margin = margin(r = .3, unit = "cm")),
            plot.margin = unit(c(1,1,1,1), "lines"),
            legend.text = element_text(size = 14),
            legend.position = 'right')
  # country level plots -------
  
    fig_energy = ggplot(energy_tot, aes(x = as.character(period), y = energy_mwh, group = type, fill = type)) + 
      geom_bar(position = 'stack', stat = 'identity') +
      labs(title = paste0('Energy', ' - ', sel_scenario),
           subtitle = 'MWh',
           x = NULL,
           y = NULL, 
           fill = NULL) +
      scale_y_continuous(labels = scales::comma, expand = c(0,0), breaks = seq(0, 4e9, 5e8), limits = c(NA, 4e9)) +
      # scale_y_continuous(labels = scales::comma, expand = c(0,0)) +
      scale_fill_manual(values = pal_fuel) +
      theme_line
    
    fname = paste0('energy_by_technology__', 'India', '.pdf')
    
    dir.create(here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'energy-plots'), showWarnings = FALSE)
    
    ggsave(fig_energy, 
           filename = here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'energy-plots', fname), 
           width = 9.8, 
           height = 6.25)
    
    embed_fonts(here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'energy-plots', fname),
                outfile = here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'energy-plots', fname))
  
  # load zone level plots --------

    for (i in loadzones) {
      
      data = energy_agg[load_zone == i]
      data_agg = data[, .(energy_mwh = sum(energy_mwh, na.rm = T)), by = period]
      # max_y = roundUp(max(data_agg[, energy_mwh]))
      max_y = ceiling(max(data_agg[, energy_mwh])/1e6)*1e6
      
      fig_energy = ggplot(data, aes(x = as.character(period), y = energy_mwh, group = type, fill = type)) + 
        geom_bar(position = 'stack', stat = 'identity') +
        labs(title = paste0('Energy for ', i, ' - ', sel_scenario),
             subtitle = 'MWh',
             x = NULL,
             y = NULL, 
             fill = NULL) +
        # scale_y_continuous(labels = scales::comma, expand = c(0,0), breaks = seq(0, max_y*1e6, (max_y*1e6 - 0)/10)) +
        scale_y_continuous(labels = scales::comma, expand = c(0,0)) +
        scale_fill_manual(values = pal_fuel) +
        theme_line
      
      # fig_energy
      
      # data = energy_agg[load_zone == i]
      # if (sum(data[, energy_mwh]) > 100e6) {
      #   fig_energy = fig_energy + 
      #     scale_y_continuous(labels = scales::comma, expand = c(0,0), breaks = seq(0, 500e6, 20e6))
      # } else {
      #   fig_energy = fig_energy + 
      #     scale_y_continuous(labels = scales::comma, expand = c(0,0), breaks = seq(0, 100e6, 2e6))
      # }
      
      fname = paste0('energy_by_technology_', i, '.pdf')
      
      dir.create(here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'energy-plots'), showWarnings = FALSE)
      
      ggsave(fig_energy, 
             filename = here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'energy-plots', fname), 
             width = 9.8, 
             height = 6.25)
      
      embed_fonts(here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'energy-plots', fname),
                  outfile = here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'energy-plots', fname))
      
      rm(fig_energy, fname)
      
    }

  
