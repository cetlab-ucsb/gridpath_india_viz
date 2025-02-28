#!/bin/bash

#scen_dir='/Users/meas/github/gridpath-india/scenarios'
ext=".db"
db_dir='../db/'
db_name=$1
db=$db_dir$db_name$ext
scenario=$2

python india_energy_data.py --database "$db" --scenario $scenario --db_save $db_name

Rscript india_energy_plot.R $db_name $scenario