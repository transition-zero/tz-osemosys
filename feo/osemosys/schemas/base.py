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


# ####################
# ### BASE CLASSES ###
# ####################

class OSeMOSYSBase(BaseModel)
    id: str
    long_name: str | None
    description: str | None

class RegionTechnologyYearData(BaseModel):
    # can be expressed as:
    #  - one value
    #  - a dict of year:value OR region:value OR technology:value
    #  - nested technology:{year:value}
    #  - nested region:{technology:{year:value}}
    data: Union[
        float, 
        Dict[Union[str,int],float], 
        Dict[str,Dict[int,float]], 
        Dict[str,Dict[str,Dict[int,float]]]
    ]

class YearData(BaseModel):
    # can be expressed as:
    #  - one value
    #  - a dict of year:value
    data: Union[
        float,
        Dict[int,float]
    ]

class RegionData(BaseModel):
    # can be expressed as:
    #  - one value
    #  - a dict of region:value
    data: Union[
        float,
        Dict[str, float]
    ]

class RegionYearData(BaseModel):
    # can be expressed as:
    #  - one value
    #  - a dict of year:value OR region:value
    #  - a dict of region:{year:value}
    data: Union[
        float,
        Dict[Union[str,int], float],
        Dict[str,Dict[int,float]]
    ]

class RegionYearTimeData(BaseModel):
    # can be expressed as:
    #  - one value
    #  - a dict of region:value
    #  - a dict of timeslice:value
    #  - a dict of region:year:value
    #  - a dict of region:timeslice:value
    #  - a dict of region:{year:{timeslice:value}}
    data: Union[
        float, 
        Dict[str, float], # which one? ambiguous
        Dict[str, Dict[int, float]]
        Dict[str, Dict[str, float]],
        Dict[str, Dict[int, Dict[str, float]]]
    ]
class RegionCommodityYearData(BaseModel):
    # can be expressed as:
    #  - one value
    #  - a dict of year:value OR region:value OR commodity:value
    #  - a dict of region:commodity:value OR region:year:value OR commodtiy:year:value
    #  - nested region:{commodity:{year:value}}
    data: Union[
        float,
        Dict[Union[str,int], float],
        Dict[str,Dict[Union[str,int],float]],
        Dict[str,Dict[str,Dict[int,float]]]

    ]