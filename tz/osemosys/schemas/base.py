import re
from enum import Enum
from typing import Annotated, Any, Dict, List, Mapping, Union

import numpy as np
import pandas as pd
from pydantic import (
    AfterValidator,
    BaseModel,
    ValidationInfo,
    create_model,
    field_validator,
    model_validator,
)
from pydantic.fields import FieldInfo

from tz.osemosys.defaults import defaults
from tz.osemosys.utils import (
    group_to_json,
    isnumeric,
    recursive_keys,
    rgetattr,
    rsetattr,
    safecast_bool,
)

# ####################
# ### BASE CLASSES ###
# ####################


def values_sum_one(values: Mapping) -> bool:
    """
    Check that provided values sum to one, within the specified tolerance
    """
    assert np.allclose(
        sum(values.values()), 1.0, atol=defaults.equals_one_tolerance
    ), "Mapping values must sum to 1.0."
    return values


def cast_osemosysdata_value(val: Any, info: FieldInfo):
    field_type_str = str(info.annotation)

    pat = r"""OSeMOSYSData_[a-zA-Z]*_?[a-zA-Z]*"""
    match = re.search(pat, field_type_str)

    if match is not None:
        span = match.group()
        coords = span.split("_")[1]
        try:
            validator = span.split("_")[2]
        except IndexError:
            validator = None

        if isinstance(val, int) and validator == "Int":
            return getattr(OSeMOSYSData, coords).Int(data=val)
        elif isinstance(val, bool) and validator == "Bool":
            return getattr(OSeMOSYSData, coords).Bool(data=val)
        elif isinstance(val, str) and validator == "DM":
            return getattr(OSeMOSYSData, coords).DM(data=val)
        elif isnumeric(val) and validator == "SumOne":
            return getattr(OSeMOSYSData, coords).SumOne(data=val)
        elif isnumeric(val):
            return getattr(OSeMOSYSData, coords)(data=val)
        elif isinstance(val, dict):
            if validator == "Int":
                return getattr(OSeMOSYSData, coords).Int(data={str(k): v for k, v in val.items()})
            elif validator == "Bool":
                return getattr(OSeMOSYSData, coords).Bool(data={str(k): v for k, v in val.items()})
            elif validator == "DM":
                return getattr(OSeMOSYSData, coords).DM(data={str(k): v for k, v in val.items()})
            elif validator == "SumOne":
                return getattr(OSeMOSYSData, coords).SumOne(
                    data={str(k): v for k, v in val.items()}
                )
            else:
                return getattr(OSeMOSYSData, coords)(data={str(k): v for k, v in val.items()})

    return val


def nested_sum_one(values: Mapping, info: ValidationInfo) -> bool:
    """
    Check that provided nested values sum to one, within the specified tolerance
    """
    if isinstance(values, OSeMOSYSData):
        data = values.data
    elif isinstance(values, dict):
        data = values
    else:
        data = values

    if data is None:
        return values

    # check for single value
    if isnumeric(data):
        if float(data) == 1.0:
            return values

    # else use pandas json_normalize to make flat dataframe of nested dictionary
    df = pd.json_normalize(data).T
    assert (
        df.index.str.split(".").str.len().unique().size == 1
    ), f"{info.field_name}: Nested dictionary must have consistent depth"
    cols = [f"L{ii}" for ii in range(1, max(df.index.str.split(".").str.len()) + 1)]
    df[cols] = pd.DataFrame(df.index.str.split(".").to_list(), index=df.index)

    if len(cols[:-1]) >= 1:
        if not np.allclose(
            df.groupby(cols[:-1]).sum()[0],
            1.0,
            atol=defaults.equals_one_tolerance,
        ):
            raise ValueError("Nested data must sum to 1.0 along the last indexing level.")
    else:
        if not np.allclose(
            df[0].sum(),
            1.0,
            atol=defaults.equals_one_tolerance,
        ):
            raise ValueError("Nested data must sum to 1.0 along the last indexing level.")

    return values


def check_or_cast_int(cls, v):
    """
    Cast values to int
    """
    if isinstance(v, int):
        return v
    elif isinstance(v, dict):
        # check or try to cast
        keys = [k for k in recursive_keys(v)]
        for keytup in keys:
            if not isinstance(rgetattr(v, list(keytup)), int):
                try:
                    rsetattr(v, list(keytup), int(rgetattr(v, list(keytup))))
                except ValueError:
                    raise ValueError("Data must be an integer or a dict with integer values.")
        return v
    else:
        try:
            return int(v)
        except ValueError:
            raise ValueError("Data must be an integer or a dict with integer values.")


def check_or_cast_bool(cls, v):
    """
    Cast values to bool
    """
    if isinstance(v, bool):
        return v
    elif isinstance(v, dict):
        # check or try to cast
        keys = [k for k in recursive_keys(v)]
        for keytup in keys:
            if not isinstance(rgetattr(v, list(keytup)), bool):
                try:
                    rsetattr(v, list(keytup), safecast_bool(rgetattr(v, list(keytup))))
                except ValueError:
                    raise ValueError("Data must be a boolean or a dict with boolean values.")
        return v
    else:
        try:
            return safecast_bool(v)
        except ValueError:
            raise ValueError("Data must be a boolean or a dict with boolean values.")


def check_or_cast_dm(cls, v):
    """
    Cast values to one of the two DepreciationMethod types, 'sinking-fund' or 'straight-line'
    """
    if isinstance(v, DepreciationMethod):
        return v
    elif isinstance(v, dict):
        # check or try to cast
        keys = [k for k in recursive_keys(v)]
        for keytup in keys:
            if not isinstance(rgetattr(v, list(keytup)), DepreciationMethod):
                try:
                    rsetattr(v, list(keytup), DepreciationMethod(rgetattr(v, list(keytup))))
                except ValueError:
                    raise ValueError("Data must be one of 'sinking-fund' or 'straight-line'.")
        return v
    else:
        try:
            return DepreciationMethod(v)
        except ValueError:
            raise ValueError("Data must be one of 'sinking-fund' or 'straight-line'.")


MappingSumOne = Annotated[Mapping, AfterValidator(values_sum_one)]
DataVar = float | int | str | bool
IdxVar = str | int


class OSeMOSYSBase(BaseModel):
    """
    This base class forces all objects to have a string id;
    a long, human-readable name; and a description.
    """

    id: str
    long_name: str
    description: str

    @model_validator(mode="before")
    @classmethod
    def backfill_missing(cls, values):
        if "long_name" not in values:
            try:
                values["long_name"] = values["id"]
            except KeyError:
                raise ValueError(f"{cls.__name__} must be provided with an 'id'.")
        if "description" not in values:
            values["description"] = "No description provided."
        return values


class OSeMOSYSData(BaseModel):
    """
    This class wraps all data being used in a model.

    ## Wildcards

    Where data must be specified for an entire SET, a wildcard "*" can be used
    to denote the data is applicable to all set members.

        demand_profile:
          "*":
            0h: 0.
            6h: 0.2
            12h: 0.3
            18h: 0.5

    Any additionally specified set members over-write the wildcard data.

        demand_annual:
          "*": 20
          region_a: 30

    ## Automatic nesting

    Sometimes a model should be defined in extensive detail, with data being
    defined for every member of every set. Usually, however, model parameters
    are repeated across regions, commodities, time definitions, etc.
    This class allows data to be expressed in the maximally-concise (and readable) way.

    For example, to define a demand for gas of 5 units at all regions and all timeslices:

        gas:
          demand: 5

    To define different demands based on region, but identical across timeslices:

        gas:
          demand:
            region_a: 5
            region_b: 10

    To define different

    """

    def __init__(self, *args, **data):
        if args:
            if len(args) > 1:
                raise ValueError(f"Expected 1 positional argument, got {len(args)}.")
            if isinstance(args[0], dict):
                if "data" in args[0].keys() and len(args[0].keys()) == 1:
                    super().__init__(**args[0])
                elif "data" in args[0].keys() and len(args[0].keys()) > 1:
                    raise ValueError(
                        "If initialising via a dict keyed by 'data', 'data' must be the only key."
                    )
                else:
                    # 'data' not in args[0].keys()
                    super().__init__(data=args[0])
            else:
                super().__init__(data=args[0])
        else:
            if "data" in data.keys() and len(data.keys()) > 1:
                raise ValueError(
                    "If initialising via a dict keyed by 'data', 'data' must be the only key."
                )
            elif "data" in data.keys():
                if isinstance(data["data"], dict):
                    if "data" in data["data"].keys():
                        super().__init__(**data["data"])
                    else:
                        super().__init__(**data)
                else:
                    super().__init__(**data)
            else:
                super().__init__(data=data)

    is_composed: bool = False
    data: Union[
        DataVar,  # {data: 6.}
        Dict[IdxVar, DataVar],
        Dict[IdxVar, Dict[IdxVar, DataVar]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, DataVar]]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, DataVar]]]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, DataVar]]]]],
    ]

    def __getitem__(self, key: Any):
        return self.data[key]

    def __setitem__(self, key: Any, value: Any):
        self.data[key] = value


class DepreciationMethod(str, Enum):
    sinking_fund = "sinking-fund"
    straight_line = "straight-line"


def _check_nesting_depth(obj_id: str, data: Any, max_depth: int):
    if isinstance(data, dict):
        keys = recursive_keys(data)
        if max([len(k) for k in keys]) > max_depth:
            raise ValueError(
                f"Data for {obj_id} must not have a nesting depth greater than {max_depth}."
            )
    return True


def _check_set_membership(obj_id: str, data: Any, sets: Dict[str, List[str]]):
    # cast 'years' to str
    if "years" in sets.keys():
        sets["years"] = [str(yr) for yr in sets["years"]]

    if not isinstance(data, dict):
        data = {"*": data}

    # cast to dataframe
    df = pd.json_normalize(data).T
    cols = [f"L{ii}" for ii in list(range(max(df.index.str.split(".").str.len())))]
    df[cols] = pd.DataFrame(df.index.str.split(".").to_list(), index=df.index)
    df = df.rename(columns={0: "value"})

    # assign each column to a set
    assign_sets = list(sets.keys())

    for col in cols:
        col_vals = df.loc[df[col] != "*", col].values.tolist()
        if col_vals:
            renamed = False
            for set_name, set_vals in sets.items():
                # assign set if it has not been assigned and all the vals are in the set
                if (set_name in assign_sets) and (len(set(col_vals) - set(set_vals)) == 0):
                    assign_sets.remove(set_name)
                    df = df.rename(columns={col: set_name})
                    renamed = True
                    break
            if not renamed:
                # there were values in a column that did not match any set
                raise ValueError(
                    f"Data for {obj_id} contains set values {col_vals} that do not match any set."
                )

    unassigned_cols = [c for c in df.columns if c not in sets.keys() if c != "value"]
    if len(unassigned_cols) > len(assign_sets):
        raise ValueError(
            f"Data for {obj_id} contains more unassigned columns that there are unassigned sets."
        )

    # assign any un-assigned wildcard columns to a un-assigned sets
    df = df.rename(
        columns=dict(
            zip(
                df.columns[(df == "*").all()].values,
                [set_name for set_name in assign_sets[: (df == "*").all().sum()]],
            )
        )
    )

    # if any un-assigned set remain, expand the dataframe
    for set_name in assign_sets:
        if set_name not in df.columns:
            df[set_name] = "*"

    # explode wildcards - need to do each set separately within group
    ordered_columns = [c for c in df.columns if c in sets.keys()]

    for col_idx in reversed(range(len(ordered_columns))):
        group_columns = ordered_columns[:col_idx]
        if group_columns:
            explode_col = ordered_columns[col_idx]

            # explode wildcards
            recombine_groups = []
            for _idx, g in df.groupby(group_columns):
                explode_vals = [
                    val for val in sets[explode_col] if val not in g[explode_col].values.tolist()
                ]
                g.loc[g[explode_col] == "*", explode_col] = g.loc[
                    g[explode_col] == "*", explode_col
                ].apply(
                    lambda x: explode_vals  # noqa: B023
                )
                g = g.explode(explode_col)
                recombine_groups.append(g)

            df = pd.concat(recombine_groups)

    # then do the root column
    root_col = ordered_columns[0]
    explode_vals = [val for val in sets[root_col] if val not in df[root_col].values.tolist()]
    df.loc[df[root_col] == "*", root_col] = df.loc[df[root_col] == "*", root_col].apply(
        lambda x: explode_vals  # noqa: B023
    )
    df = df.explode(root_col)

    # re-json
    data = group_to_json(df, data_columns=list(sets.keys()), target_column="value")

    return data


def _compose_R(self, obj_id, data, regions, **sets):
    # Region
    _check_nesting_depth(obj_id, data, 1)
    self.data = _check_set_membership(obj_id, data, {"regions": regions})
    self.is_composed = True

    return self


def _compose_RY(self, obj_id, data, regions, years, **sets):
    # Region-Year

    _check_nesting_depth(obj_id, data, 2)
    self.data = _check_set_membership(obj_id, data, {"regions": regions, "years": years})
    self.is_composed = True

    return self


def _compose_RT(self, obj_id, data, regions, technologies, **sets):
    # Region-Technology

    _check_nesting_depth(obj_id, data, 2)
    self.data = _check_set_membership(
        obj_id, data, {"regions": regions, "technologies": technologies}
    )
    self.is_composed = True

    return self


def _compose_RYS(self, obj_id, data, regions, years, timeslices, **sets):
    # Region-Year-TimeSlice

    _check_nesting_depth(obj_id, data, 3)
    self.data = _check_set_membership(
        obj_id, data, {"regions": regions, "years": years, "timeslices": timeslices}
    )
    self.is_composed = True

    return self


def _compose_RTY(self, obj_id, data, regions, technologies, years, **sets):
    # Region-Technology-Year

    _check_nesting_depth(obj_id, data, 3)
    self.data = _check_set_membership(
        obj_id, data, {"regions": regions, "technologies": technologies, "years": years}
    )
    self.is_composed = True

    return self


def _compose_RCY(self, obj_id, data, regions, commodities, years, **sets):
    # Region-Commodity-Year
    _check_nesting_depth(obj_id, data, 3)
    self.data = _check_set_membership(
        obj_id, data, {"regions": regions, "commodities": commodities, "years": years}
    )
    self.is_composed = True

    return self


def _compose_RIY(self, obj_id, data, regions, impacts, years, **sets):
    # Region-Impact-Year
    _check_nesting_depth(obj_id, data, 3)
    self.data = _check_set_membership(
        obj_id, data, {"regions": regions, "impacts": impacts, "years": years}
    )
    self.is_composed = True

    return self


def _compose_RO(self, obj_id, data, regions, storage, **sets):
    # Region-stOrage
    _check_nesting_depth(obj_id, data, 2)
    self.data = _check_set_membership(obj_id, data, {"regions": regions, "storage": storage})
    self.is_composed = True

    return self


def _compose_RRY(self, obj_id, data, regions, years, **sets):
    # Region-Commodity-Year
    _check_nesting_depth(obj_id, data, 3)
    self.data = _check_set_membership(obj_id, data, {"R1": regions, "R2": regions, "years": years})
    self.is_composed = True

    return self


def _compose_RR(self, obj_id, data, regions, **sets):
    # Region-Commodity-Year
    _check_nesting_depth(obj_id, data, 2)
    self.data = _check_set_membership(obj_id, data, {"R1": regions, "R2": regions})
    self.is_composed = True

    return self


def _null(self, values):
    # pass-through only, for testing purposes
    return values


for key, func in zip(
    ["R", "RY", "RT", "RYS", "RTY", "RCY", "RIY", "RO", "RRY", "RR", "ANY"],
    [
        _compose_R,
        _compose_RY,
        _compose_RT,
        _compose_RYS,
        _compose_RTY,
        _compose_RCY,
        _compose_RIY,
        _compose_RO,
        _compose_RRY,
        _compose_RR,
        _null,
    ],
):
    # add a new OSEMOSYSData class for each data cooridinate key
    setattr(
        OSeMOSYSData,
        key,
        create_model("OSeMOSYSData" + f"_{key}", __base__=OSeMOSYSData),
    )

    # add the compose method to each new class
    getattr(OSeMOSYSData, key).compose = func

    # add the datatype constructors
    for _type, validator in zip(
        ["Int", "Bool", "SumOne"],
        [check_or_cast_int, check_or_cast_bool, nested_sum_one],
    ):
        setattr(
            getattr(OSeMOSYSData, key),
            _type,
            create_model(
                f"OSeMOSYSData_{key}_{_type}",
                __base__=getattr(OSeMOSYSData, key),
                __validators__={
                    f"check_or_cast_{_type.lower()}": field_validator("data")(validator)
                },
            ),
        )

OSeMOSYSData.R.DM = create_model(
    "OSeMOSYSData_R_DM",
    __base__=OSeMOSYSData.R,
    __validators__={"check_or_cast_dm": field_validator("data")(check_or_cast_dm)},
)
