"""
Why?
-> put documentation/descirptions where the action is.
-> consolidate input files
-> do validation early, using pydantic
-> JSONify for IO
-> some renaming to make more explicit
"""

"""
extras:
  - parse basic python expressions (dict+list comps + expressions)
  - use yaml links *&
  - wildcard str classes, e.g. *
  - inequality for year, e.g. >=2030
"""

from typing import Dict, Union

from pydantic import BaseModel

# ####################
# ### BASE CLASSES ###
# ####################


class OSeMOSYSBase(BaseModel):
    id: str
    long_name: str | None
    description: str | None


DataVar = float | int
IdxVar = str | int


class OSeMOSYSData(BaseModel):
    data: Union[
        DataVar,  # {data: 4.}
        Dict[IdxVar, DataVar],
        Dict[IdxVar, Dict[IdxVar, DataVar]],
        Dict[IdxVar, Dict[IdxVar, Dict[IdxVar, DataVar]]],
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
