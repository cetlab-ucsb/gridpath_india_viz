# Copyright 2016-2020 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Create plot of new capacity by period and technology for a given
scenario/zone/subproblem/stage.
"""

from argparse import ArgumentParser
import pandas as pd
import sys
import os

d = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, d)

from db.common_functions import connect_to_database
from gridpath.auxiliary.db_interface import get_scenario_id_and_name
from viz.common_functions import get_parent_parser# , get_capacity_data

def create_parser():
    parser = ArgumentParser(add_help=True, parents=[get_parent_parser()])
    parser.add_argument("--scenario", help="The scenario name. Required if "
                                           "no --scenario_id is specified.")
    parser.add_argument("--db_save", help="Name of folder to save results to")

    return parser

def parse_arguments(arguments):
    """

    :return:
    """
    parser = create_parser()
    parsed_arguments = parser.parse_args(args=arguments)

    return parsed_arguments

def get_loadzones(conn, scenario_id):
    """get list of load zones"""

    # list of load zones in scenario
    query = """SELECT load_zone
    FROM results_system_load_balance
    WHERE scenario_id = {}
    ;""".format(scenario_id, ",".join(["?"]))

    df = pd.read_sql(query, conn)
    return df['load_zone'].unique()

def get_capacity_data(conn, subproblem, stage, capacity_col,
                      scenario_id=None, load_zone=None, period=None):
    """
    Get capacity results by scenario/period/technology. Users can
    optionally provide a subset of scenarios/load_zones/periods.
    Note: if load zone is not provided, will aggregate across load zones.

    :param conn:
    :param subproblem:
    :param stage:
    :param capacity_col: str, capacity column in results_project_capacity
    :param scenario_id: int or list of int, optional (default: return all
        scenarios)
    :param load_zone: str or list of str, optional (default: aggregate across
        load_zones)
    :param period: int or list of int, optional (default: return all periods)
    :return: DataFrame with columns scenario_id, period, technology, capacity_mw
    """

    params = [subproblem, stage]
    sql = """SELECT scenario_name AS scenario, period, technology, project, 
        sum({}) AS capacity_mw
        FROM results_project_capacity
        INNER JOIN 
        (SELECT scenario_name, scenario_id FROM scenarios) as scen_table
        USING (scenario_id)
        WHERE subproblem_id = ?
        AND stage_id = ?""".format(capacity_col)
    if period is not None:
        period = period if isinstance(period, list) else [period]
        sql += " AND period in ({})".format(",".join("?"*len(period)))
        params += period
    if scenario_id is not None:
        scenario_id = scenario_id if isinstance(scenario_id, list) else [scenario_id]
        sql += " AND scenario_id in ({})".format(",".join("?"*len(scenario_id)))
        params += scenario_id
    if load_zone is not None:
        load_zone = load_zone if isinstance(load_zone, list) else [load_zone]
        sql += " AND load_zone in ({})".format(",".join("?"*len(load_zone)))
        params += load_zone
    sql += " GROUP BY scenario, period, technology, project;"

    df = pd.read_sql(
        sql,
        con=conn,
        params=params
    )

    return df


def get_plotting_data(conn, subproblem, stage, scenario_id=None,
                      load_zone=None, period=None, **kwargs):
    """
    See get_capacity_data()

    **kwargs needed, so that an error isn't thrown when calling this
    function with extra arguments from the UI.
    """

    return get_capacity_data(conn, subproblem, stage, "capacity_mw",
                             scenario_id, load_zone, period)


# inputs
parsed_args = parse_arguments(arguments=None)
db_loc = parsed_args.database
sel_scenario = parsed_args.scenario
save_db = parsed_args.db_save

# connect to database
conn = connect_to_database(db_path=db_loc)
c = conn.cursor()

# get scenario id and scenario name
scenario_id, scenario = get_scenario_id_and_name(scenario_id_arg=None, scenario_name_arg=sel_scenario, c=c, script="capacity_total_plot")

# get array of load zones
loadzones = get_loadzones(conn=conn, scenario_id=scenario_id)

# loop through all load zones and get energy data
appended_data = []
for lz in loadzones:

    df = get_plotting_data(conn=conn, scenario_id=scenario_id, load_zone=lz, stage=1, subproblem=1)
    df.insert(0, 'load_zone', lz)

    appended_data.append(df)

# concat all dataframes together into one dataframe
total_df = pd.concat(appended_data, axis=0, sort=False)

# add scenario as column
# total_df['scenario'] = sel_scenario

# reorder columns
total_df = total_df[['scenario', 'load_zone', 'period', 'project', 'technology', 'capacity_mw']]

# save csv
filename = sel_scenario + '_capacity_total_data_all_zones.csv'
fileloc = os.path.join(sys.path[0], 'scenarios', save_db, sel_scenario, 'results', 'figures')

if not os.path.exists(fileloc):
    os.makedirs(fileloc)

total_df.to_csv(os.path.join(fileloc,  filename), index=False)
print('File ' + filename + ' saved in ' + fileloc)