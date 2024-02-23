import re
from enum import Enum
from typing import Annotated, Any, Dict, Mapping, Union

import numpy as np
import pandas as pd
from pydantic import AfterValidator, BaseModel, create_model, field_validator, model_validator
from pydantic.fields import FieldInfo

from feo.osemosys.defaults import defaults
from feo.osemosys.utils import isnumeric, recursive_keys, rgetattr, rsetattr, safecast_bool

# ####################
# ### BASE CLASSES ###
# ####################


def values_sum_one(values: Mapping) -> bool:
    assert sum(values.values()) == 1.0, "Mapping values must sum to 1.0."
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

    return val


def nested_sum_one(values: Mapping) -> bool:
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
    ), "Nested dictionary must have consistent depth"
    cols = [f"L{ii}" for ii in range(1, max(df.index.str.split(".").str.len()) + 1)]
    df[cols] = pd.DataFrame(df.index.str.split(".").to_list(), index=df.index)

    if not np.allclose(
        df.groupby(cols[:-1])[0].sum(),
        1.0,
        atol=defaults.equals_one_tolerance,
    ):
        raise ValueError("Nested data must sum to 1.0 along the last indexing level.")
    return values


def check_or_cast_int(cls, v):
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
            values["long_name"] = values["id"]
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
                super().__init__(data=data["data"])
            else:
                super().__init__(data=data)

    data: Union[
        DataVar,  # {data: 6.}
        Dict[IdxVar, DataVar],
        Dict[IdxVar, Dict[IdxVar, DataVar]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, DataVar]]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, DataVar]]]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, DataVar]]]]],
    ]


class DepreciationMethod(str, Enum):
    sinking_fund = "sinking-fund"
    straight_line = "straight-line"


def _compose_R(cls, values):
    # Region
    return values


def _compose_RY(cls, values):
    # Region-Year
    return values


def _compose_RT(cls, values):
    # Region-Technology
    return values


def _compose_RYS(cls, values):
    # Region-Year-TimeSlice
    return values


def _compose_RTY(cls, values):
    # Region-Technology-Year
    return values


def _compose_RCY(cls, values):
    # Region-Commodity-Year
    return values


def _null(cls, values):
    # pass-through only, for testing purposes
    return values


for key, func in zip(
    ["R", "RY", "RT", "RYS", "RTY", "RCY", "ANY"],
    [_compose_R, _compose_RY, _compose_RT, _compose_RYS, _compose_RTY, _compose_RCY, _null],
):
    # add a new OSEMOSYSData class for each data cooridinate key
    setattr(OSeMOSYSData, key, create_model("OSeMOSYSData" + f"_{key}", __base__=OSeMOSYSData))

    # add the compose method to each new class
    getattr(OSeMOSYSData, key).compose = func

    # add the datatype constructors
    for _type, validator in zip(
        ["Int", "Bool", "SumOne"], [check_or_cast_int, check_or_cast_bool, nested_sum_one]
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
