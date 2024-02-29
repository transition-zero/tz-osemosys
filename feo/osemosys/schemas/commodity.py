from typing import Any

from pydantic import Field, field_validator, model_validator

from feo.osemosys.schemas.base import (
    OSeMOSYSBase,
    OSeMOSYSData,
    OSeMOSYSData_Bool,
    OSeMOSYSData_SumOne,
)
from feo.osemosys.schemas.compat.commodity import OtooleCommodity
from feo.osemosys.utils import isnumeric


class Commodity(OSeMOSYSBase, OtooleCommodity):
    """
    Commodity class

    """

    demand_annual: OSeMOSYSData | None = Field(None)
    demand_profile: OSeMOSYSData_SumOne | None = Field(None)
    is_renewable: OSeMOSYSData_Bool | None = Field(None)

    # include this technology in joint reserve margin and renewables targets
    include_in_joint_reserve_margin: OSeMOSYSData_Bool | None = Field(None)
    include_in_joint_renewable_target: OSeMOSYSData_Bool | None = Field(None)

    @field_validator("demand_annual", mode="before")
    @classmethod
    def passthrough_float(cls, v: Any) -> OSeMOSYSData:
        if isnumeric(v):
            return OSeMOSYSData(float(v))
        return v

    @field_validator("demand_profile", mode="before")
    @classmethod
    def passthrough_sumone(cls, v: Any) -> OSeMOSYSData_SumOne:
        if isnumeric(v):
            return OSeMOSYSData_SumOne(float(v))
        return v

    @field_validator("is_renewable", mode="before")
    @classmethod
    def passthrough_bool(cls, v: Any) -> OSeMOSYSData_Bool:
        if isinstance(v, bool):
            return OSeMOSYSData_Bool(v)
        return v

    @model_validator(mode="before")
    @classmethod
    def check_demand_exists_if_profile(cls, values):
        if values.get("demand_profile") is not None and values.get("demand_annual") is None:
            raise ValueError("If demand_profile is defined, demand_annual must also be defined.")
        return values
