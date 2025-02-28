# create dispatch plots

# inputs -----------------

  args = commandArgs(trailingOnly = TRUE)
  db_dir          = args[1]
  sel_scenario    = args[2]
  # db_dir          = '0801'
  # sel_scenario    = 'RPS10_VRElow_SThigh_CONVhigh_ret3035'
  data_fname      = '_dispatch_data_all_zones.csv'

# load packages --------

  library(data.table)
  library(ggplot2)
  library(hrbrthemes)
  library(extrafont)

# read in data -------

  dt_dispatch = fread(here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', paste0(sel_scenario, data_fname)), header = T)
  keycols = c('load_zone', 'timepoint')
  setkeyv(dt_dispatch, keycols)

# calculate load + exports -------

  dt_dispatch[, Load_plus_Exports := Load + Exports]
  dt_dispatch[, Load_plus_Exports_plus_Storage_Charging := Load + Exports + Storage_Charging]

# melt data from wide to long --------

  dispatch_long = melt(dt_dispatch, id.vars = c('scenario', 'load_zone', 'timepoint'), variable.name = 'variable', value.name = 'value_mw')
  dispatch_long[, value_mw := as.numeric(as.character(value_mw))]
  setkeyv(dispatch_long, keycols)

# rename load + exports ------

  dispatch_long[variable == 'Load_plus_Exports', variable := 'Load + Exports']
  dispatch_long[variable == 'Load_plus_Exports_plus_Storage_Charging', variable := 'Load + Exports + Storage Charging']

# recategorize fuels -------

  dispatch_long[variable %like% 'Coal', type := 'Coal']
  dispatch_long[is.na(type), type := variable]

# remove unused variables -----

  dispatch_long = dispatch_long[!type %in% c('Exports', 'Storage_Charging', 'Unserved_Energy')]

# aggregate by type ------

  dispatch_agg = dispatch_long[, .(value_mw = sum(value_mw, na.rm = T)), by = .(scenario, load_zone, timepoint, type)]

# get years/periods ------

  dispatch_agg[, period := as.numeric(substr(timepoint, start = 1, stop = 4))]
  
# get month -------
  
  dispatch_agg[, month := substr(timepoint, start = 5, stop = 6)]
  
# get month -------
  
  dispatch_agg[, hour := substr(timepoint, start = 7, stop = 8)]
  
# get complete list of periods in timepoints ------
  
  prds = seq(2020, 2040, 5)
  # prds = data.table(period = seq(2020, 2040, 5))
  
  timepoint_prds = c(unique(dispatch_agg[, period]))
  matched_prds = sapply(timepoint_prds, function(a, b) {b[which.min(abs(a-b))]}, prds)
  
  all_prds = data.table(period = timepoint_prds,
                        match_period = matched_prds)
  
# match period to nearest period -----
  
  dispatch_agg = dispatch_agg[all_prds, on = .(period)]
  dispatch_agg[, period := match_period]
  dispatch_agg[, match_period := NULL]
  
# get index -----
  
  dispatch_agg[, index := 1:.N, by = .(scenario, load_zone, period, type)]
  
# calculate unique number of hours -----
  
  dispatch_agg[, no_of_hours := uniqueN(index), by = .(scenario, load_zone, period, type)]
  
# only keep load zones with more than one hour of data -------
  
  dispatch_agg = dispatch_agg[no_of_hours > 1]
  
# reorder levels --------
  
  dispatch_agg = dispatch_agg[, type := factor(type, levels = c('Load + Exports + Storage Charging', 
                                                                'Load + Exports', 
                                                                'Load',
                                                                "Imports", 
                                                                "Curtailment_Hydro", 
                                                                "Curtailment_Variable", 
                                                                "Battery",
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
  
  loadzones = unique(dispatch_agg[, load_zone])
  
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
    
    pal_type = c('Load + Exports + Storage Charging' = 3, 
                 'Load + Exports' = 2, 
                 'Load' = 1)
  
  # theme -------
  
    theme_line = theme_ipsum(base_family = 'Secca Soft',
                             grid = 'Y', 
                             plot_title_size = 20, 
                             subtitle_size = 18,
                             axis_title_just = 'center',
                             axis_title_size = 18, 
                             axis_text_size = 16,
                             strip_text_size = 16)  +
      theme(plot.title = element_text(hjust = 0, face = 'bold'),
            plot.title.position = 'plot',
            plot.subtitle = element_text(hjust = 0),
            plot.caption = element_text(size = 10, color = '#5c5c5c', face = 'plain'),
            # axis.text.x = element_text(margin = margin(t = .3, unit = "cm")),
            axis.line.x = element_line(color = 'black'),
            axis.ticks.x = element_line(color = 'black'),
            axis.ticks.length.x = unit(0.25, "cm"),
            # axis.text.y = element_text(margin = margin(r = .3, unit = "cm")),
            strip.text = element_text(hjust = 0.5),
            plot.margin = unit(c(1,1,1,1), "lines"),
            legend.text = element_text(size = 14),
            legend.position = 'right')
  
  
  # area chart --------
  
    for (i in loadzones) {
      
      fig_dispatch = ggplot() + 
        geom_area(data = dispatch_agg[load_zone == i & type %in% names(pal_fuel)], aes(x = index, y = value_mw, group = type, fill = type)) +
        geom_line(data = dispatch_agg[load_zone == i & (type %in% c('Load', 'Load + Exports', 'Load + Exports + Storage Charging'))], 
                  aes(x = index, y = value_mw, lty = type)) +
        facet_grid(. ~ period) +      
        labs(title = paste0('Dispatch by technology for ', i, ' - scenario: ', sel_scenario),
             subtitle = 'MW',
             x = 'Hour Ending',
             y = NULL, 
             fill = NULL,
             lty = NULL) +
        scale_y_continuous(labels = scales::comma, expand = c(0,0)) +
        scale_fill_manual(values = pal_fuel) +
        scale_linetype_manual(values = pal_type) + 
        theme_line
      
      # fig_dispatch
      
      fname = paste0('dispatch_by_technology_', i, '.pdf')
      
      dir.create(here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'dispatch-plots'), showWarnings = FALSE)
      
      ggsave(fig_dispatch, 
             filename = here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'dispatch-plots', fname), 
             width = 14, 
             height = 6.25)
      
      embed_fonts(here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'dispatch-plots', fname),
                  outfile = here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'dispatch-plots', fname))
      
      rm(fig_dispatch, fname)
      
    }
  