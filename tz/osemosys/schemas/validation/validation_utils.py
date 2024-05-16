import numpy as np
import pandas as pd

from tz.osemosys.utils import json_dict_to_dataframe


def check_sums_one(data, leniency, cols, cols_to_groupby):
    data_df = pd.json_normalize(data)
    data_df.columns = cols
    assert np.allclose(data_df.groupby(cols_to_groupby)["VALUE"].sum(), 1, atol=leniency), (
        f"demand_profile must sum to one (within {leniency}) for all REGION,"
        f" YEAR, and commodity; commodity {id} does not"
    )


def check_min_vals_lower_max(min_data, max_data, columns):
    """Check that values in min_data are lower than corresponding values in max_data

    Args:
        min_data (data instance): data instance with min values
        max_data (data instance): data instance with max values
        columns (list[str]): list of column names

    Returns:
        bool: True if all data in max_data is >= corresponding data in min_data, otherwise False
    """
    # Convert JSON style data to dataframes
    min_df = json_dict_to_dataframe(min_data.data)
    max_df = json_dict_to_dataframe(max_data.data)

    if len(min_df.columns) == 1:
        min_df.columns = ["VALUE_min"]
    else:
        min_df.columns = columns

    if len(max_df.columns) == 1:
        max_df.columns = ["VALUE_max"]
    else:
        max_df.columns = columns

    # Check max values are >= min values
    if len(max_df.columns) == 1 and len(min_df.columns) == 1:
        if max_df.iloc[0, 0] >= min_df.iloc[0, 0]:
            return True
        else:
            return False
    elif len(max_df.columns) == 1:
        min_df["VALUE_max"] = max_df.iloc[0, 0]
        return (min_df["VALUE"] <= min_df["VALUE_max"]).all()
    elif len(min_df.columns) == 1:
        max_df["VALUE_min"] = min_df.iloc[0, 0]
        return (max_df["VALUE_min"] <= max_df["VALUE"]).all()
    # If both min and max values have all dimensions specified
    else:
        columns.remove("VALUE")
        merged_df = pd.merge(
            min_df, max_df, on=columns, suffixes=("_min", "_max"), how="outer"
        ).dropna()

    # Check that values in min_data are lower than those in max_data
    return (merged_df["VALUE_min"] <= merged_df["VALUE_max"]).all()
