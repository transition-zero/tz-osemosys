from typing import Dict, Union

from pydantic import BaseModel

# ####################
# ### BASE CLASSES ###
# ####################


class OSeMOSYSBase(BaseModel):
    """
    This base class forces all objects to have a string id;
    a long, human-readable name; and a description.
    """

    id: str
    long_name: str | None
    description: str | None


DataVar = float | int
IdxVar = str | int


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

    data: Union[
        DataVar,  # {data: 6.}
        Dict[IdxVar, DataVar],
        Dict[IdxVar, Dict[IdxVar, DataVar]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, DataVar]]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, DataVar]]]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, DataVar]]]]],
    ]


# OSeMOSYUSData_sum1= wraps(OSeMOSYSData, validotr)

# @field_validator
# def rnsure_profiles_sum_to_1(cls, valeus):
#    # validate
#    None


class OSeMOSYSDataInt(BaseModel):
    data: Union[
        int,  # {data: 6.}
        Dict[IdxVar, int],
        Dict[IdxVar, Dict[IdxVar, int]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, int]]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, int]]]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, int]]]]],
    ]


class RegionTechnologyYearData(BaseModel):
    # can be expressed as:
    #  - one value
    #  - a dict of year:value OR region:value OR technology:value
    #  - nested technology:{year:value}
    #  - nested region:{technology:{year:value}}
    data: Union[
        float,
        Dict[Union[str, int], float],
        Dict[str, Dict[int, float]],
        Dict[str, Dict[str, Dict[int, float]]],
    ]


class YearData(BaseModel):
    # can be expressed as:
    #  - one value
    #  - a dict of year:value
    data: Union[float, Dict[int, float]]


class RegionData(BaseModel):
    # can be expressed as:
    #  - one value
    #  - a dict of region:value
    data: Union[float, Dict[str, float]]


class StringInt(BaseModel):
    # can be expressed as:
    #  - one integer
    #  - a dict of string:integer
    data: Union[int, Dict[str, int]]


class StringData(BaseModel):
    # can be expressed as:
    #  - a dict of string:float or string:int
    data: Dict[str, Union[float, int]]


class RegionYearData(BaseModel):
    # can be expressed as:
    #  - one value
    #  - a dict of year:value OR region:value
    #  - a dict of region:{year:value}
    data: Union[float, Dict[Union[str, int], float], Dict[str, Dict[int, float]]]


class StringYearData(BaseModel):
    # can be expressed as:
    #  - one value
    #  - a dict of year:value OR region:value
    #  - a dict of region:{year:value}
    data: Union[
        Union[float, int],
        Dict[Union[str, int], Union[float, int]],
        Dict[str, Dict[int, Union[float, int]]],
    ]

    def keys(self):
        return self.data.keys()


class StringStringData(BaseModel):
    # can be expressed as:
    #  - one value
    #  - a dict of year:value OR region:value
    #  - a dict of region:{year:value}
    data: Union[
        float,
        Dict[str, float],
        Dict[str, Dict[str, float]],
    ]


class IntYearData(BaseModel):
    # can be expressed as:
    #  - one integer value
    #  - a dict of year:value OR integer:value
    #  - a dict of int:{year:value}
    data: Union[
        Union[float, int], Dict[int, Union[float, int]], Dict[int, Dict[int, Union[float, int]]]
    ]


class IntIntIntData(BaseModel):
    # can be expressed as:
    #  - integer or float value with 0-3 additional integers
    data: Union[
        Union[int, float],
        Dict[int, Union[int, float]],
        Dict[int, Dict[int, Union[int, float]]],
        Dict[int, Dict[int, Dict[int, Union[int, float]]]],
    ]


class RegionYearTimeData(BaseModel):
    # can be expressed as:
    #  - one value
    #  - a dict of region:value OR timeslice:value
    #  - a dict of region:year:value
    #  - a dict of region:timeslice:value
    #  - a dict of region:{year:{timeslice:value}}
    data: Union[
        float,
        Dict[str, float],  # which one? ambiguous
        Dict[str, Dict[int, float]],
        Dict[str, Dict[str, float]],
        Dict[str, Dict[str, Dict[int, float]]],
    ]


class RegionCommodityYearData(BaseModel):
    # can be expressed as:
    #  - one value
    #  - a dict of year:value OR region:value OR commodity:value
    #  - a dict of region:commodity:value OR region:year:value OR commodtiy:year:value
    #  - nested region:{commodity:{year:value}}
    data: Union[
        float,
        Dict[Union[str, int], float],
        Dict[str, Dict[Union[str, int], float]],
        Dict[str, Dict[str, Dict[int, float]]],
    ]


class RegionModeYearData(BaseModel):
    # Where Mode is mode of operation
    #  can be expressed as:
    #  - one value
    #  - a dict of region:value OR mode:value or year:value
    #  - a dict of region:year:value OR region:mode:value OR mode:year:value
    #  - a dict of region:{mode:{year:value}}
    data: Union[
        float,
        Dict[Union[str, int], float],
        Dict[Union[str, int], Dict[int, float]],
        Dict[str, Dict[int, Dict[int, float]]],
    ]


# TODO temporary class for input/output/emission activity ratio
class StringStringIntIntData(BaseModel):
    data: Union[
        Dict[str, Dict[str, Dict[int, Dict[int, Union[int, float]]]]],
        Dict[str, Dict[str, Dict[int, Union[int, float]]]],
    ]


# TODO temporary class for TradeRoute
class TradeRoute(BaseModel):
    data: Dict[str, Dict[str, Dict[str, Union[int, float]]]]
