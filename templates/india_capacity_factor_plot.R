# create capacity factor plots

# inputs -----------------

  args = commandArgs(trailingOnly = TRUE)
  db_dir          = args[1]
  sel_scenario    = args[2]
  # sel_scenario    = 'RPS10_VRElow_SThigh_CONVhigh'
  # db_dir          = '0801'
  cap_fname       = '_capacity_total_data_all_zones.csv'
  en_fname        = '_energy_data_all_zones.csv'

# load packages --------

  library(data.table)
  library(ggplot2)
  library(hrbrthemes)
  library(extrafont)

# read in data -------
  
  dt_capacity = fread(here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', paste0(sel_scenario, cap_fname)), header = T)
  keycols = c('load_zone', 'project', 'period')
  setkeyv(dt_capacity, keycols)
  
  dt_energy = fread(here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', paste0(sel_scenario, en_fname)), header = T)
  keycols = c('load_zone', 'period')
  setkeyv(dt_energy, keycols)
  
# match energy with capacity --------
  
  match_proj = dt_energy[dt_capacity, on = .(scenario, load_zone, period, project, technology)]
  
# calculate energy at timepoint -------
  
  match_proj[, energy_mwh := power_mw * timepoint_weight]
  match_proj[, nameplate_mwh := capacity_mw * timepoint_weight]
  
# calculate capacity factor -----
  
  match_proj[, capacity_factor := energy_mwh/nameplate_mwh]

# get average capacity factor for projects ------
  
  match_proj[, period := as.character(period)]
  avg_cf = match_proj[, .(mean_cf = mean(capacity_factor, na.rm = T)), by = .(scenario, load_zone, period, project, technology)]
  
# recategorize fuels -------
  
  avg_cf[technology %like% 'Coal', type := 'Coal']
  avg_cf[is.na(type), type := technology]
  
# reorder levels --------
  
  avg_cf = avg_cf[, type := factor(type, levels = c("Battery",
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
  
  loadzones = unique(match_proj[, load_zone])
  
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

# figure: box plot of capacity factors --------
  
  fig_box = ggplot(avg_cf[!type %in% c('Battery', 'Hydro_Pumped', 'CT')], aes(x = type, y = mean_cf, group = type, color = type)) + 
    geom_boxplot() +
    facet_grid(rows = vars(period)) +
    labs(title = paste0('Average capacity factor', ' - ', sel_scenario),
         subtitle = 'MWh',
         x = NULL,
         y = NULL, 
         fill = NULL) +
    # scale_y_continuous(labels = scales::comma, expand = c(0,0)) +
    scale_color_manual(values = pal_fuel) +
    theme_line +
    theme(axis.text.x = element_text(size = 13))
  
  fname = paste0('average_capacity_factor_by_technology__', 'India', '.pdf')
  
  dir.create(here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'capacity-factor-plots'), showWarnings = FALSE)
  
  ggsave(fig_box, 
         filename = here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'capacity-factor-plots', fname), 
         width = 15, 
         height = 12)
  
  embed_fonts(here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'capacity-factor-plots', fname),
              outfile = here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'capacity-factor-plots', fname))
  
  