import importlib
import os
import re
from collections import defaultdict
from collections.abc import MutableMapping
from itertools import chain
from typing import Any, List, Optional

import orjson
import pandas as pd
from pydantic import BaseModel

from tz.osemosys import exceptions
from tz.osemosys.io.simpleeval import EvalWithCompoundTypes

from datetime import datetime, timedelta  # noqa


def safecast_bool(val):
    if isinstance(val, str):
        if val.lower() in ["true", "t", "1"]:
            return True
        elif val.lower() in ["false", "f", "0"]:
            return False
        else:
            raise ValueError(f"Cannot safely cast {val} to boolean")
    elif isinstance(val, int):
        if val in [1, 0]:
            return bool(val)
        else:
            raise ValueError(f"Cannot safely cast {val} to boolean")
    else:
        raise ValueError(f"Cannot safely cast {val} to boolean")


def isnumeric(val: Any) -> bool:
    """
    Check if a value is numeric.

    Args:
        val (Any): The value to be checked.

    Returns:
        bool: True if the value is numeric, False otherwise.
    """
    try:
        float(val)
        return True
    except TypeError:
        return False
    except ValueError:
        return False
    except Exception as e:
        raise e


def enforce_list(val: Any) -> List:
    """
    Enforce a value to be a list.

    Args:
        val (Any): The value to be enforced.

    Returns:
        List: The value as a list.
    """
    if isinstance(val, list):
        return val
    else:
        return [val]


def merge(d: MutableMapping, v: MutableMapping):
    """
    Merge two dictionaries.

    Merge dict-like `v` into dict-like `d`. In case keys between them
    are the same, merge their sub-dictionaries. Otherwise, values in
    `v` overwrite `d`.
    """
    for key in v:
        if (
            key in d
            and isinstance(d[key], MutableMapping)  # noqa: W503
            and isinstance(v[key], MutableMapping)  # noqa: W503
        ):
            d[key] = merge(d[key], v[key])
        else:
            d[key] = v[key]
    return d


def recursive_items(dictionary, keys=None):
    if keys is None:
        keys = []
    for key, value in dictionary.items():
        if type(value) is dict:
            yield from recursive_items(value, keys + [key])
        else:
            yield (tuple(keys + [key]), value)


def recursive_keys(dictionary, keys=None):
    if keys is None:
        keys = []
    for key, value in dictionary.items():
        if type(value) is dict:
            yield from recursive_keys(value, keys + [key])
        else:
            yield (tuple(keys + [key]))


class BaseResponse(BaseModel):
    status_code: int
    msg: str


def flatten(list_of_lists):
    return list(chain.from_iterable(list_of_lists))


def maybe_flatten(list_of_lists):
    resp = []
    for sublist in list_of_lists:
        if isinstance(sublist, list):
            resp.extend(sublist)
        else:
            resp.append(sublist)
    return resp


def _indirect_cls(path):
    mod_name, _cls_name = path.rsplit(".", 1)
    mod = importlib.import_module(mod_name)
    _cls = getattr(mod, _cls_name)
    return _cls


def maybe_parse_environ(v):
    if isinstance(v, str):
        if "ENVIRON" in v:
            g = re.search(r"\(.*\)", v)
            return os.environ.get(v[g.start() + 1 : g.end() - 1], None)  # noqa
        else:
            return v
    else:
        return v


def nested_dict_get(obj, list_of_attrs, original_list_of_vars):
    if len(list_of_attrs) == 1:
        try:
            obj[list_of_attrs[0]]
        except KeyError:
            raise exceptions.MissingVar(f"Missing var: {'.'.join(original_list_of_vars)}")
        except Exception as e:
            raise e
    else:
        return nested_dict_get(obj, list_of_attrs[1:], original_list_of_vars)


evaluator = EvalWithCompoundTypes(
    functions={"sum": sum, "range": range, "max": max, "min": min, "zip": zip}
)


def maybe_eval_string(expr: Any):
    # if it's not a string, pass it through.
    if not isinstance(expr, str):
        return expr

    expr = expr.strip()

    # check for trigger functions
    for func in ["sum(", "range(", "max(", "min("]:
        if func in expr:
            return evaluator.eval(expr)

    # check if is a dict compr
    if expr[0] == "{" and expr[-1] == "}":
        return evaluator.eval(expr)

    # check if is a list compr
    if expr[0] == "[" and expr[-1] == "]":
        return evaluator.eval(expr)

    # else
    return expr


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
    target_column: str = "VALUE",
    data_columns: Optional[List[str]] = None,
    default_nodes: List[str] = None,
    fill_zero: bool = True,
):
    """
    Converts a DataFrame to a nested JSON-like structure.

    Args:
        g (pd.DataFrame): The input DataFrame to be converted.
        root_column (Optional[str]): The column to be excluded from the structure (eg. TECHNOLOGY).
        target_column (str): The column containing data values to be nested.
        data_columns (Optional[List[str]]): List of columns representing the nested structure.
        default_nodes (List[str]): List of default nodes to initialize the structure.
        fill_zero (bool): Flag to exclude rows with target_column value of 0.

    Returns:
        Dict: A nested JSON-like Dict representing the DataFrame.

    Note:
        If there's no nested structure (data_columns is None and root_column is not None),
        the function returns a single value instead of a dictionary.
    """

    # Return single value rather than dict if there's no nested structure to data
    if data_columns is None and root_column is not None:
        return g["VALUE"].values[0]

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

    # Check if data is not empty
    if isinstance(data, dict) and len(data) > 0:
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
        return pd.json_normalize({prefix: [data]})


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
                data = pd.json_normalize(getattr(instance, f"{sub_attribute}").data)

            columns = otoole_stems[output_file]["columns"][:]
            if root_column is not None:
                columns.remove(root_column)
            data.columns = columns
            if root_column is not None:
                data[root_column] = instance.id
            data = data[otoole_stems[output_file]["columns"]]
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
        "time_definition": {
            "otoole_stems": self.time_definition.otoole_stems,
            "root_column": None,
        },
        "regions": {
            "otoole_stems": self.regions[0].otoole_stems,
            "root_column": "REGION",
        },
        "commodities": {
            "otoole_stems": self.commodities[0].otoole_stems,
            "root_column": "FUEL",
        },
        "impacts": {
            "otoole_stems": self.impacts[0].otoole_stems,
            "root_column": "EMISSION",
        },
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
            attribute_dfs[file] = pd.DataFrame(columns=otoole_stems[file]["columns"])

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
