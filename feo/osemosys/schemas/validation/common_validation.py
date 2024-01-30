import numpy as np

from feo.osemosys.utils import json_dict_to_dataframe


def check_sums_one(data, leniency, cols, cols_to_groupby):
    data_df = json_dict_to_dataframe(data)
    data_df.columns = cols
    assert np.allclose(data_df.groupby(cols_to_groupby)["VALUE"].sum(), 1, atol=leniency), (
        f"demand_profile must sum to one (within {leniency}) for all REGION,"
        f" YEAR, and commodity; commodity {id} does not"
    )
