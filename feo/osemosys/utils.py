import functools
import importlib
import os
import re
from collections import defaultdict
from typing import List, Optional

import orjson
import pandas as pd
from osemosys.simpleeval import EvalWithCompoundTypes

from datetime import datetime, timedelta  # noqa


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
    """
    Function to convert a JSON dictionary as defined by the group_to_json()
    function into a pandas dataframe with empty column names
    """
    if isinstance(data, dict):
        # If data is a dictionary, iterate through its items
        result = pd.DataFrame()
        for key, value in data.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            df = json_dict_to_dataframe(value, new_prefix)
            result = pd.concat([result, df], axis=1)
        if (
            prefix == ""
        ):  # Execute this step if all iterations complete and final result ready to be returned
            result = result.T
            result = result.reset_index()
            result = pd.concat([result["index"].str.split(".", expand=True), result[0]], axis=1)
            return result
        else:
            return result
    else:
        # If data is not a dictionary, create a single-column DataFrame
        # with empty column name, used in iteration
        return pd.DataFrame({prefix: [data]})


# TODO
def to_csv_iterative(data, commodity, column_structure, id_column, csv_name):
    pass
