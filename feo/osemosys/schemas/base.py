from typing import Dict, Union

from pydantic import BaseModel

# ####################
# ### BASE CLASSES ###
# ####################


class OSeMOSYSBase(BaseModel):
    id: str
    long_name: str | None
    description: str | None


DataVar = float | int | str
IdxVar = str | int


class OSeMOSYSData(BaseModel):
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
