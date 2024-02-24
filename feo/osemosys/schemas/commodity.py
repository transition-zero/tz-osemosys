from typing import Any

from pydantic import Field, model_validator

from feo.osemosys.schemas.base import OSeMOSYSBase, OSeMOSYSData, cast_osemosysdata_value
from feo.osemosys.schemas.compat.commodity import OtooleCommodity


class Commodity(OSeMOSYSBase, OtooleCommodity):
    """
    Commodity class

    """

    demand_annual: OSeMOSYSData.RY | None = Field(None)
    demand_profile: OSeMOSYSData.RYS.SumOne | None = Field(None)
    is_renewable: OSeMOSYSData.RY.Bool | None = Field(None)

    # include this technology in joint reserve margin and renewables targets
    include_in_joint_reserve_margin: OSeMOSYSData.RY.Bool | None = Field(None)
    include_in_joint_renewable_target: OSeMOSYSData.RY.Bool | None = Field(None)

    @model_validator(mode="before")
    @classmethod
    def cast_values(cls, values: Any) -> Any:
        for field, info in cls.model_fields.items():
            field_val = values.get(field)

            if field_val is not None:
                values[field] = cast_osemosysdata_value(field_val, info)

        return values

    @model_validator(mode="before")
    @classmethod
    def check_demand_exists_if_profile(cls, values):
        if values.get("demand_profile") is not None and values.get("demand_annual") is None:
            raise ValueError("If demand_profile is defined, demand_annual must also be defined.")
        return values

    def compose(self, regions, years, timeslices, **kwargs):
        if self.demand_annual is not None:
            self.demand_annual = OSeMOSYSData.RY(
                self.demand_annual.compose(self.id, regions, years, self.demand_annual.data)
            )
        if self.demand_profile is not None:
            self.demand_profile = OSeMOSYSData.RYS.SumOne(
                self.demand_profile.compose(
                    self.id, regions, years, timeslices, self.demand_profile.data
                )
            )
        if self.is_renewable is not None:
            self.is_renewable = OSeMOSYSData.RY.Bool(
                self.is_renewable.compose(self.id, regions, years, self.is_renewable.data)
            )
        if self.include_in_joint_reserve_margin is not None:
            self.include_in_joint_reserve_margin = OSeMOSYSData.RY.Bool(
                self.include_in_joint_reserve_margin.compose(
                    self.id, regions, years, self.include_in_joint_reserve_margin.data
                )
            )
        if self.include_in_joint_renewable_target is not None:
            self.include_in_joint_renewable_target = OSeMOSYSData.RY.Bool(
                self.include_in_joint_renewable_target.compose(
                    self.id, regions, years, self.include_in_joint_renewable_target.data
                )
            )

        return self
