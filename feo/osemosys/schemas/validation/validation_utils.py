import numpy as np
import pandas as pd

from feo.osemosys.utils import json_dict_to_dataframe


def check_sums_one(data, leniency, cols, cols_to_groupby):
    data_df = json_dict_to_dataframe(data)
    data_df.columns = cols
    assert np.allclose(data_df.groupby(cols_to_groupby)["VALUE"].sum(), 1, atol=leniency), (
        f"demand_profile must sum to one (within {leniency}) for all REGION,"
        f" YEAR, and commodity; commodity {id} does not"
    )


def check_min_vals_lower_max(min_data, max_data, columns, error_msg):
    """Check that values in min_data are lower than corresponding values in max_data

    Args:
        min_data (data instance): data instance with min values
        max_data (data instance): data instance with max values
        columns (list[str]): list of column names
        error_msg (str): error message to display
    """
    # Convert JSON style data to dataframes
    min_df = json_dict_to_dataframe(min_data.data)
    min_df.columns = columns
    max_df = json_dict_to_dataframe(max_data.data)
    max_df.columns = columns

    # Combine dataframes
    columns.remove("VALUE")
    merged_df = pd.merge(
        min_df, max_df, on=columns, suffixes=("_min", "_max"), how="outer"
    ).dropna()

    # Check that values in min_data are lower than those in max_data
    assert (merged_df["VALUE_min"] <= merged_df["VALUE_max"]).all(), f"{error_msg}"
