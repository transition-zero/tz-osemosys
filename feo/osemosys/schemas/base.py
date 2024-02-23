from typing import Annotated, Dict, Mapping, Union

import numpy as np
import pandas as pd
from pydantic import AfterValidator, BaseModel, BeforeValidator, model_validator

from feo.osemosys.defaults import defaults
from feo.osemosys.utils import isnumeric

# ####################
# ### BASE CLASSES ###
# ####################


def values_sum_one(values: Mapping) -> bool:
    assert sum(values.values()) == 1.0, "Mapping values must sum to 1.0."
    return values


def nested_sum_one(values: Mapping) -> bool:
    # breakpoint()
    if isinstance(values, OSeMOSYSData):
        data = values.data
    elif isinstance(values, dict):
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


MappingSumOne = Annotated[Mapping, AfterValidator(values_sum_one)]
DataVar = float | int | str
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


OSeMOSYSData_SumOne = Annotated[OSeMOSYSData, BeforeValidator(nested_sum_one)]


class OSeMOSYSData_Int(BaseModel):
    data: Union[
        int,  # {data: 6.}
        Dict[IdxVar, int],
        Dict[IdxVar, Dict[IdxVar, int]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, int]]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, int]]]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, int]]]]],
    ]


class OSeMOSYSData_Bool(BaseModel):
    data: Union[
        bool,  # {data: 6.}
        Dict[IdxVar, bool],
        Dict[IdxVar, Dict[IdxVar, bool]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, bool]]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, bool]]]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, bool]]]]],
    ]
