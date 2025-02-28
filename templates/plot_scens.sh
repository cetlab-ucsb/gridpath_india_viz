#db_dir='/Users/meas/github/gridpath-india/db'
db_name='0810_oftx'

#db='../db/0801.db'

for i in RPS10_VRElow_SThigh_CONVhigh
do
  bash create_energy_plots.sh $db_name $i
  bash create_capacity_total_plots.sh $db_name $i
  bash create_capacity_new_plots.sh $db_name $i
  bash create_cost_plots.sh $db_name $i
  bash create_dispatch_plots.sh $db_name $i
done

