from typing import Annotated, Dict, Mapping, Union

from pydantic import AfterValidator, BaseModel, model_validator

# ####################
# ### BASE CLASSES ###
# ####################


def values_sum_one(values: Mapping) -> bool:
    assert sum(values.values()) == 1.0, "Mapping values must sum to 1.0."
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
        super().__init__(data=args[0] if args else data)

    data: Union[
        DataVar,  # {data: 6.}
        Dict[IdxVar, DataVar],
        Dict[IdxVar, Dict[IdxVar, DataVar]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, DataVar]]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, DataVar]]]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, DataVar]]]]],
    ]


class OSeMOSYSDataInt(BaseModel):
    data: Union[
        int,  # {data: 6.}
        Dict[IdxVar, int],
        Dict[IdxVar, Dict[IdxVar, int]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, int]]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, int]]]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, int]]]]],
    ]
