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
Make csv of energy data for all load zones for a specified scenario
"""

from argparse import ArgumentParser
import pandas as pd
import sys
import os

d = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, d)

from db.common_functions import connect_to_database
from gridpath.auxiliary.db_interface import get_scenario_id_and_name
from viz.common_functions import get_parent_parser

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

def get_plotting_data(conn, scenario_id, load_zone, stage, **kwargs):
    """
    Get energy results by period for a given scenario/load_zone/stage.

    **kwargs needed, so that an error isn't thrown when calling this
    function with extra arguments from the UI.

    :param conn:
    :param scenario_id:
    :param load_zone:
    :param stage:
    :return:
    """

    # TODO: add curtailment and imports? What about storage charging?

    # Energy by period and technology
    sql = """
        SELECT timepoint, timepoint_weight, period, project, technology, power_mw
        FROM results_project_dispatch
        WHERE scenario_id = ?
        AND load_zone = ?
        AND stage_id = ?
        AND spinup_or_lookahead = 0
        GROUP BY timepoint, timepoint_weight, project, period, technology;
        """

    df = pd.read_sql(
        sql,
        con=conn,
        params=(scenario_id, load_zone, stage)
    )

    return df


# inputs
parsed_args = parse_arguments(arguments=None)
db_loc = parsed_args.database
sel_scenario = parsed_args.scenario
save_db = parsed_args.db_save

# connect to database
conn = connect_to_database(db_path=db_loc)
c = conn.cursor()

# get scenario id and scenario name
scenario_id, scenario = get_scenario_id_and_name(scenario_id_arg=None, scenario_name_arg=sel_scenario, c=c, script="dispatch_plot")

# get array of load zones
loadzones = get_loadzones(conn=conn, scenario_id=scenario_id)

# loop through all load zones and get energy data
appended_data = []
for lz in loadzones:

    df = get_plotting_data(conn=conn, scenario_id=scenario_id, load_zone=lz, stage=1)
    df.insert(0, 'load_zone', lz)

    appended_data.append(df)

# concat all dataframes together into one dataframe
total_df = pd.concat(appended_data, axis=0, sort=False)

# add scenario as column
total_df['scenario'] = sel_scenario

# reorder columns
total_df = total_df[['scenario', 'load_zone', 'timepoint', 'timepoint_weight', 'period', 'project', 'technology', 'power_mw']]

# save csv
filename = sel_scenario + '_energy_data_all_zones.csv'
fileloc = os.path.join(sys.path[0], 'scenarios', save_db, sel_scenario, 'results', 'figures')

if not os.path.exists(fileloc):
    os.makedirs(fileloc)

total_df.to_csv(os.path.join(fileloc,  filename), index=False)
print('File ' + filename + ' saved in ' + fileloc)