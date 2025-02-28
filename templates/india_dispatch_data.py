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
Make csv of dispatch data for all load zones for a specified scenario
"""

from argparse import ArgumentParser
import pandas as pd
import sys
import os

d = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, d)

from db.common_functions import connect_to_database
from gridpath.auxiliary.db_interface import get_scenario_id_and_name
from viz.common_functions import show_hide_legend, show_plot, \
    get_parent_parser, get_tech_colors, get_tech_plotting_order, get_unit

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


def get_timepoints(conn, scenario_id, starting_tmp=None, ending_tmp=None,stage_id=1):
    """
    Note: assumes timepoints are ordered!
    :param conn:
    :param scenario_id:
    :param starting_tmp:
    :param ending_tmp:
    :param stage_id:
    :return:
    """

    if starting_tmp is None:
        start_query = ""
    else:
        start_query = "AND timepoint >= {}".format(starting_tmp)

    if ending_tmp is None:
        end_query = ""
    else:
        end_query = "AND timepoint <= {}".format(ending_tmp)

    query = """SELECT timepoint
        FROM inputs_temporal
        INNER JOIN
        (SELECT temporal_scenario_id FROM scenarios WHERE scenario_id = {})
        USING (temporal_scenario_id)
        WHERE stage_id = {}
        {}
        {}
        ;""".format(scenario_id, stage_id, start_query, end_query)

    tmps = [i[0] for i in conn.execute(query).fetchall()]

    return tmps


def get_loadzones(conn, scenario_id):
    """get list of load zones"""

    # list of load zones in scenario
    query = """SELECT load_zone
    FROM results_system_load_balance
    WHERE scenario_id = {}
    ;""".format(scenario_id, ",".join(["?"]))

    df = pd.read_sql(query, conn)
    return df['load_zone'].unique()


def get_power_by_tech_results(conn, scenario_id, load_zone, timepoints):
    """
    Get results for power by technology for a given load_zone and set of
    points.
    :param conn:
    :param scenario_id:
    :param load_zone:
    :param timepoints
    :return:
    """

    # Power by technology
    query = """SELECT timepoint, technology, power_mw
        FROM results_project_dispatch_by_technology
        WHERE scenario_id = {}
        AND load_zone = '{}'
        AND timepoint IN ({})
        ;""".format(scenario_id, load_zone, ",".join(["?"] * len(timepoints)))

    df = pd.read_sql(query, conn, params=timepoints)
    if not df.empty:
        df = df.pivot(index="timepoint", columns="technology")["power_mw"]

    return df

def get_variable_curtailment_results(c, scenario_id, load_zone, timepoints):
    """
    Get variable generator curtailment for a given load_zone and set of
    timepoints.
    :param c:
    :param scenario_id:
    :param load_zone:
    :param timepoints:
    :return:
    """
    query = """SELECT scheduled_curtailment_mw
            FROM results_project_curtailment_variable
            WHERE scenario_id = {}
            AND load_zone = '{}'
            AND timepoint IN ({})
            ;""".format(
                scenario_id, load_zone, ",".join(["?"] * len(timepoints))
            )

    curtailment = [i[0] for i in c.execute(query, timepoints).fetchall()]

    return curtailment

def get_hydro_curtailment_results(c, scenario_id, load_zone, timepoints):
    """
    Get conventional hydro curtailment for a given load_zone and set of
    timepoints.
    :param scenario_id:
    :param load_zone:
    :param timepoints:
    :return:
    """
    query = """SELECT scheduled_curtailment_mw
            FROM results_project_curtailment_hydro
            WHERE scenario_id = {}
            AND load_zone = '{}'
            AND timepoint IN ({});""".format(
                scenario_id, load_zone, ",".join(["?"] * len(timepoints))
            )

    curtailment = [i[0] for i in c.execute(query, timepoints).fetchall()]

    return curtailment

def get_imports_exports_results(c, scenario_id, load_zone, timepoints):
    """
    Get imports/exports results for a given load_zone and set of timepoints.
    :param c:
    :param scenario_id:
    :param load_zone:
    :param timepoints:
    :return:
    """
    query = """SELECT net_imports_mw
        FROM results_transmission_imports_exports
        WHERE scenario_id = {}
        AND load_zone = '{}'
        AND timepoint IN ({})
        ;""".format(scenario_id, load_zone, ",".join(["?"] * len(timepoints)))

    net_imports = c.execute(query, timepoints).fetchall()

    imports = [i[0] if i[0] > 0 else 0 for i in net_imports]
    exports = [-e[0] if e[0] < 0 else 0 for e in net_imports]

    return imports, exports

def get_load(c, scenario_id, load_zone, timepoints):
    """

    :param c:
    :param scenario_id:
    :param load_zone:
    :param timepoints
    :return:
    """

    query = """SELECT load_mw, unserved_energy_mw
        FROM results_system_load_balance
        WHERE scenario_id = {}
        AND load_zone = '{}'
        AND timepoint IN ({});""".format(
            scenario_id, load_zone, ",".join(["?"] * len(timepoints))
        )

    load_balance = c.execute(query, timepoints).fetchall()

    load = [i[0] for i in load_balance]
    unserved_energy = [i[1] for i in load_balance]

    return load, unserved_energy

# inputs
parsed_args = parse_arguments(arguments=None)
db_loc = parsed_args.database
sel_scenario = parsed_args.scenario
save_db = parsed_args.db_save

# connect to database
conn = connect_to_database(db_path=db_loc)
c = conn.cursor()

scenario_id, scenario = get_scenario_id_and_name(scenario_id_arg=None, scenario_name_arg=sel_scenario, c=c, script="dispatch_plot")
timepoints = get_timepoints(conn, scenario_id)

loadzones = get_loadzones(conn=conn, scenario_id=scenario_id)

appended_data = []
for lz in loadzones:
    df = get_power_by_tech_results(conn=conn,
                                   scenario_id=scenario_id,
                                   load_zone=lz,
                                   timepoints=timepoints)

    df['timepoint'] = timepoints

    df["Storage_Charging"] = 0
    stor_techs = df.columns[(df < 0).any()]
    for tech in stor_techs:
        df["Storage_Charging"] += -df[tech].clip(upper=0)
        df[tech] = df[tech].clip(lower=0)

    curtailment_variable = get_variable_curtailment_results(c=c, scenario_id=scenario_id, load_zone=lz,
                                                            timepoints=timepoints)
    if curtailment_variable:
        df["Curtailment_Variable"] = curtailment_variable

    curtailment_hydro = get_hydro_curtailment_results(c=c, scenario_id=scenario_id, load_zone=lz,
                                                      timepoints=timepoints)
    if curtailment_hydro:
        df["Curtailment_Hydro"] = curtailment_hydro

    imports, exports = get_imports_exports_results(c=c, scenario_id=scenario_id, load_zone=lz,
                                                   timepoints=timepoints)
    if imports:
        df["Imports"] = imports
    if exports:
        df["Exports"] = exports

    load_balance = get_load(c=c, scenario_id=scenario_id, load_zone=lz, timepoints=timepoints)
    df["Load"] = load_balance[0]
    df["Unserved_Energy"] = load_balance[1]

    df.insert(0, 'load_zone', lz)

    appended_data.append(df)

total_df = pd.concat(appended_data, axis=0, sort=False)
total_df = total_df.drop(['technology', 'power_mw'], axis=1)
# total_df = total_df.reset_index().rename(columns={'index':'timepoint'})

total_df['scenario'] = sel_scenario

# total_df = total_df[['scenario', 'load_zone', 'timepoint', 'Biomass', 'CCGT', 'CT', 'Diesel', 'Hydro_Pumped', 'Hydro_ROR', 'Hydro_Storage', 'Nuclear',
#                      'Subcritical_Coal', 'Subcritical_Oil', 'Supercritical_Coal', 'WHR', 'Solar', 'Wind', 'Battery', 'Storage_Charging', 'Curtailment_Variable',
#                      'Curtailment_Hydro', 'Imports', 'Exports', 'Load', 'Unserved_Energy']]
total_df = total_df[['scenario', 'load_zone', 'timepoint', 'Biomass', 'CCGT', 'CT', 'Diesel', 'Hydro_Pumped', 'Hydro_ROR', 'Hydro_Storage', 'Nuclear',
                     'Subcritical_Coal_Small', 'Subcritical_Coal_Large', 'Supercritical_Coal', 'WHR', 'Solar', 'Wind', 'Battery', 'Storage_Charging', 'Curtailment_Variable',
                     'Imports', 'Exports', 'Load', 'Unserved_Energy']]

# save csv
filename = sel_scenario + '_dispatch_data_all_zones.csv'
fileloc = os.path.join(sys.path[0], 'scenarios', save_db, sel_scenario, 'results', 'figures')

if not os.path.exists(fileloc):
    os.makedirs(fileloc)

total_df.to_csv(os.path.join(fileloc,  filename), index=False)
print('File ' + filename + ' saved in ' + fileloc)