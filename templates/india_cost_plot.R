# create cost plots

# inputs -----------------

  args = commandArgs(trailingOnly = TRUE)
  db_dir          = args[1]
  sel_scenario    = args[2]
# sel_scenario    = 'RPS70_VRElow_SThigh_CONVhigh'
  data_fname      = '_cost_data_all_zones.csv'

# load packages --------

  library(data.table)
  library(ggplot2)
  library(hrbrthemes)
  library(extrafont)

# read in data -------

  dt_cost = fread(here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', paste0(sel_scenario, data_fname)), header = T)
  keycols = c('load_zone', 'period')
  setkeyv(dt_cost, keycols)
  
# rename columns -----
  
  setnames(dt_cost, "Cost Component", "cost_component")
  setnames(dt_cost, "Cost", "cost_million_usd")
  
# aggregate by type ------
  
  cost_agg = dt_cost[, .(cost_million_usd = sum(cost_million_usd, na.rm = T)), by = .(scenario, load_zone, period, cost_component)]
  
# aggregate to country level -------
  
  cost_tot = dt_cost[, .(cost_million_usd = sum(cost_million_usd, na.rm = T)), by = .(scenario, period, cost_component)]
  
# reorder levels --------
  
  cost_agg = cost_agg[, cost_component := factor(cost_component, levels = c("Hurdle_Rates",
                                                                            "Transmission_Capacity",
                                                                            "Shutdowns",
                                                                            "Startups",
                                                                            "Variable_OM",
                                                                            "Fuel",
                                                                            "Capacity"))]
  
  cost_tot = cost_tot[, cost_component := factor(cost_component, levels = c("Hurdle_Rates",
                                                                           "Transmission_Capacity",
                                                                           "Shutdowns",
                                                                           "Startups",
                                                                           "Variable_OM",
                                                                           "Fuel",
                                                                           "Capacity"))]

# get list of loadzones -------
  
  loadzones = unique(cost_agg[, load_zone])

# ------------------------------- plot -------------------------------
  
  # color palettes ------
  
    pal_fuel  = c("Capacity"= "#66c2a5",
                  "Fuel" = "#fc8d62",
                  "Variable_OM" = "#8da0cb",
                  "Startups" = "#e78ac3",
                  "Shutdowns" = "#a6d854",
                  "Transmission_Capacity" = "#ffd92f",
                  "Hurdle_Rates" = "#e5c494")
    
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
  
    fig_cost = ggplot(cost_tot, aes(x = as.character(period), y = cost_million_usd/1e3, group = cost_component, fill = cost_component)) + 
      geom_bar(position = 'stack', stat = 'identity') +
      labs(title = paste0('Cost', ' - ', sel_scenario),
           subtitle = 'Billion USD',
           x = NULL,
           y = NULL, 
           fill = NULL) +
      scale_y_continuous(labels = scales::comma, expand = c(0,0), breaks = seq(0, 170, 10), limits = c(NA, 170)) +
      # scale_y_continuous(labels = scales::comma, expand = c(0,0)) +
      scale_fill_manual(values = pal_fuel) +
      theme_line
    
    fname = paste0('cost_by_component__', 'India', '.pdf')
    
    dir.create(here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'cost-plots'), showWarnings = FALSE)
    
    ggsave(fig_cost, 
           filename = here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'cost-plots', fname), 
           width = 9.8, 
           height = 6.25)
    
    embed_fonts(here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'cost-plots', fname),
                outfile = here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'cost-plots', fname))
  
  # load zone level plots --------

    for (i in loadzones) {
      
      data = cost_agg[load_zone == i]
      data_agg = data[, .(cost_million_usd = sum(cost_million_usd, na.rm = T)), by = period]
      # max_y = roundUp(max(data_agg[, energy_mwh]))
      max_y = ceiling(max(data_agg[, cost_million_usd])/1e6)*1e6
      
      fig_cost = ggplot(data, aes(x = as.character(period), y = cost_million_usd, group = cost_component, fill = cost_component)) + 
        geom_bar(position = 'stack', stat = 'identity') +
        labs(title = paste0('Cost for ', i, ' - ', sel_scenario),
             subtitle = 'Million USD',
             x = NULL,
             y = NULL, 
             fill = NULL) +
        # scale_y_continuous(labels = scales::comma, expand = c(0,0), breaks = seq(0, max_y*1e6, (max_y*1e6 - 0)/10)) +
        scale_y_continuous(labels = scales::comma, expand = c(0,0)) +
        scale_fill_manual(values = pal_fuel) +
        theme_line
      
      fname = paste0('cost_by_component_', i, '.pdf')
      
      dir.create(here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'cost-plots'), showWarnings = FALSE)
      
      ggsave(fig_cost, 
             filename = here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'cost-plots', fname), 
             width = 9.8, 
             height = 6.25)
      
      embed_fonts(here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'cost-plots', fname),
                  outfile = here::here('scenarios', db_dir, sel_scenario, 'results', 'figures', 'cost-plots', fname))
      
      rm(fig_cost, fname)
      
    }

  
