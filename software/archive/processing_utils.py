import os

import pandas as pd
import numpy as np
import itertools

# User-defined scenario filter (can be left blank for all scenarios)
def _filter_capacity(grouped_capacity_, scenario = '' , status = ''):
    # Apply the scenario and status filters if specified
    if scenario and status:
        filtered_data = grouped_capacity_[
            (grouped_capacity_['Status'] == status) &
            (grouped_capacity_['Scenario'] == scenario)
        ]
    elif scenario:
        filtered_data = grouped_capacity_[
            (grouped_capacity_['Scenario'] == scenario)
        ]
    elif status:
        filtered_data = grouped_capacity_[
            (grouped_capacity_['Status'] == status)
        ]
    else:
        # If neither scenario nor gen_status is specified, no filtering applied
        filtered_data = grouped_capacity_

    # Convert to wide format by pivoting
    return filtered_data.pivot_table(index   = 'Technology',
                                     columns = ['Scenario', 'Period'],
                                     values  = 'Power',
                                     aggfunc = 'sum').reset_index(drop = False)
    
__all__ = ['_filter_capacity']
