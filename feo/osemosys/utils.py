import functools
import importlib
import os
import re
from collections import defaultdict
from itertools import chain
from typing import List, Optional

import orjson
import pandas as pd

from feo.osemosys.simpleeval import EvalWithCompoundTypes

from datetime import datetime, timedelta  # noqa


def flatten(list_of_lists):
    return list(chain.from_iterable(list_of_lists))


def _indirect_cls(path):
    mod_name, _cls_name = path.rsplit(".", 1)
    mod = importlib.import_module(mod_name)
    _cls = getattr(mod, _cls_name)
    return _cls


def rsetattr(obj, attrs, val):
    pre = attrs[0:-1]
    post = attrs[-1]
    (rgetattr(obj, pre) if pre else obj)[post] = val
    return None


def rgetattr(obj, attrs, *args):
    def _getattr(obj, attr):
        return obj.get(attr)

    return functools.reduce(_getattr, [obj] + attrs)


def recursive_keys(keys, dictionary):
    for key, value in dictionary.items():
        if isinstance(value, dict):
            yield from recursive_keys(keys + [key], value)
        else:
            yield keys + [key]


def maybe_parse_environ(v):
    if isinstance(v, str):
        if "ENVIRON" in v:
            g = re.search(r"\(.*\)", v)
            return os.environ.get(v[g.start() + 1 : g.end() - 1], None)  # noqa
        else:
            return v
    else:
        return v


def maybe_subsitute_variables(txt, cfg):
    # TODO: Substitute {{$key.subkey}} here
    pass


def maybe_eval_string(expr):
    # TODO: check if we actually want to eval expression?

    evaluator = EvalWithCompoundTypes(
        functions={"sum": sum, "range": range, "max": max, "min": min}
    )

    return evaluator.eval(expr)


def walk_dict(d, f, *args):
    list_of_keys = recursive_keys([], d)

    for sublist in list_of_keys:
        val = rgetattr(d, sublist)
        rsetattr(d, sublist, f(val, *args))

    return d


def makehash():
    return defaultdict(makehash)


def _fill_d(d, target_column, data_columns, t):
    try:
        if len(data_columns) == 1:
            d[str(getattr(t, data_columns[0]))] = getattr(t, target_column)
        elif len(data_columns) == 2:
            d[str(getattr(t, data_columns[0]))][str(getattr(t, data_columns[1]))] = getattr(
                t, target_column
            )
        elif len(data_columns) == 3:
            d[(getattr(t, data_columns[0]))][str(getattr(t, data_columns[1]))][
                str(getattr(t, data_columns[2]))
            ] = getattr(t, target_column)
        elif len(data_columns) == 4:
            d[str(getattr(t, data_columns[0]))][str(getattr(t, data_columns[1]))][
                str(getattr(t, data_columns[2]))
            ][str(getattr(t, data_columns[3]))] = getattr(t, target_column)
        else:
            raise NotImplementedError
        # TODO add case for where len(data_columns) == 5
    except Exception as e:
        print(t)
        print(target_column)
        print(data_columns)
        raise e

    return d


def group_to_json(
    g: pd.DataFrame,
    root_column: Optional[str] = None,
    target_column: str = "value",
    data_columns: Optional[List[str]] = None,
    default_nodes: List[str] = None,
    fill_zero: bool = True,
):
    # non-mutable default
    if data_columns is None:
        data_columns = ["node_id", "commodity", "technology"]

    if default_nodes is not None:
        d = {n: makehash() for n in default_nodes}
    else:
        d = makehash()

    if not fill_zero:
        g = g.loc[g[target_column] != 0]

    if root_column is not None:
        g = g.drop(columns=[root_column])

    for t in g.itertuples():
        _fill_d(d, target_column, data_columns, t)

    # https://github.com/ijl/orjson#opt_non_str_keys
    return orjson.loads(orjson.dumps(d, option=orjson.OPT_NON_STR_KEYS))


def json_dict_to_dataframe(data, prefix=""):
    """Function to convert a JSON dictionary as defined by the group_to_json()
    function into a pandas dataframe with empty column names

    Args:
        data (dict): JSON style data dict
        prefix (str, optional): used to build a prefix for the column names when constructing the
        DataFrame. Defaults to "".

    Returns:
        DataFrame: data in pandas DataFrame format
    """

    if isinstance(data, dict):
        # If data is a dictionary, iterate through its items
        result = pd.DataFrame()
        for key, value in data.items():
            new_prefix = f"{prefix}-{key}" if prefix else key
            df = json_dict_to_dataframe(value, new_prefix)
            result = pd.concat([result, df], axis=1)
        if (
            prefix == ""
        ):  # Execute this step if all iterations complete and final result ready to be returned
            result = result.T
            result = result.reset_index()
            result = pd.concat([result["index"].str.split("-", expand=True), result[0]], axis=1)
            return result
        else:
            return result
    else:
        # If data is not a dictionary, create a single-column DataFrame
        # with empty column name, used in iteration
        return pd.DataFrame({prefix: [data]})


def add_instance_data_to_output_dfs(instance, output_dfs, otoole_stems, root_column=None):
    """Add data from the given class instance to the given output dfs, returning the modified dfs
    If root_column is given, add root_column as a column to the instance data with values of self.id
    (to account for data from multiple instances, e.g. technology, being added to the same df)

    Args:
        instance (cls): Instance of a data class (such as Technology)
        output_dfs (dict{str:df}): dict of {output_csv_name:output_data_dataframe}
        otoole_stems (dict): Dict of mapping otoole names to RunSpec names
        root_column (str, optional): Missing column to add (e.g. TECHNOLOGY). Defaults to None.

    Returns:
        output_dfs (dict{str:df}): output_dfs with additional data added
    """

    # Iterate over otoole style csv names
    for output_file in list(otoole_stems):
        # Get class instance attribute name corresponding to otoole csv name
        sub_attribute = otoole_stems[output_file]["attribute"]

        # Add data from this class instance to the output_dfs
        if getattr(instance, f"{sub_attribute}") is not None:
            if isinstance(getattr(instance, f"{sub_attribute}"), list):
                data = pd.DataFrame({"VALUE": getattr(instance, f"{sub_attribute}")})
            else:
                data = json_dict_to_dataframe(getattr(instance, f"{sub_attribute}").data)

            column_structure = otoole_stems[output_file]["column_structure"][:]
            if root_column is not None:
                column_structure.remove(root_column)
            data.columns = column_structure
            if root_column is not None:
                data[root_column] = instance.id
            data = data[otoole_stems[output_file]["column_structure"]]
            # TODO: add casting to int for YEAR and MODE_OF_OPERATION?
            if not output_dfs[output_file].empty:
                output_dfs[output_file] = pd.concat([output_dfs[output_file], data])
            else:
                output_dfs[output_file] = data

    return output_dfs


def to_df_helper(self):
    """Function to convert Runspec to a dict of dfs, corrsponding to otoole style output CSVs

    Args:
        self: An instance of the Runspec class

    Returns:
        output_dfs (dict{str:df}): a dict of output CSV name and associated df
    """
    # Attribute and root column names
    attributes = {
        "time_definition": {"otoole_stems": self.time_definition.otoole_stems, "root_column": None},
        "other_parameters": {
            "otoole_stems": self.other_parameters.otoole_stems,
            "root_column": None,
        },
        "regions": {"otoole_stems": self.regions[0].otoole_stems, "root_column": "REGION"},
        "commodities": {"otoole_stems": self.commodities[0].otoole_stems, "root_column": "FUEL"},
        "impacts": {"otoole_stems": self.impacts[0].otoole_stems, "root_column": "EMISSION"},
        "technologies": {
            "otoole_stems": self.technologies[0].otoole_stems,
            "root_column": "TECHNOLOGY",
        },
    }
    # Add storage technologies to attributes dict if present
    if self.storage_technologies:
        attributes["storage_technologies"] = {
            "otoole_stems": self.storage_technologies[0].otoole_stems,
            "root_column": "STORAGE",
        }

    output_dfs = {}
    for attribute, values in attributes.items():
        otoole_stems = values["otoole_stems"]
        root_column = values["root_column"]

        # Create output dfs, adding to dict with filename as key
        attribute_dfs = {}
        for file in list(otoole_stems):
            attribute_dfs[file] = pd.DataFrame(columns=otoole_stems[file]["column_structure"])

        # Add data to output dfs iteratively for attributes with multiple instances (eg. impacts)
        if isinstance(getattr(self, f"{attribute}"), list):
            if root_column is None:
                raise ValueError("root_column is required for attributes with multiple instances")
            id_list = []
            for instance in getattr(self, f"{attribute}"):
                id_list.append(instance.id)
                attribute_dfs = add_instance_data_to_output_dfs(
                    instance, attribute_dfs, otoole_stems, root_column
                )
            attribute_dfs[root_column] = pd.DataFrame(id_list, columns=["VALUE"])

        # Add data to output dfs once for single instance attributes (eg. time_definition)
        else:
            attribute_dfs = add_instance_data_to_output_dfs(
                getattr(self, f"{attribute}"), attribute_dfs, otoole_stems
            )

        output_dfs = {**output_dfs, **attribute_dfs}

    return output_dfs


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
