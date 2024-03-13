from typing import Any

from pydantic import Field, model_validator

from tz.osemosys.schemas.base import OSeMOSYSBase, OSeMOSYSData, cast_osemosysdata_value
from tz.osemosys.schemas.compat.commodity import OtooleCommodity


class Commodity(OSeMOSYSBase, OtooleCommodity):
    """
    Class to contain all data related to commodities (osemosys 'FUEL'), including:
    - Demand
    - Renewable fuel tag
    - Reserve margin tag
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

    def compose(self, **sets):
        for field, _info in self.model_fields.items():
            field_val = getattr(self, field)

            if field_val is not None:
                if isinstance(field_val, OSeMOSYSData):
                    setattr(
                        self,
                        field,
                        field_val.compose(self.id, field_val.data, **sets),
                    )

        return self
