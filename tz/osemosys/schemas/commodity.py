from typing import Any

from pydantic import Field, model_validator

from tz.osemosys.schemas.base import OSeMOSYSBase, OSeMOSYSData, cast_osemosysdata_value
from tz.osemosys.schemas.compat.commodity import OtooleCommodity


class Commodity(OSeMOSYSBase, OtooleCommodity):
    """
    # Commodity

    The Commodity class contains all data related to commodities (OSeMOSYS 'FUEL'), including
    demands and tags for whether the commodity is counted as renewable or part of the reserve margin
    . One Commodity instance is given for each commodity.

    Commodities can either be final energy demands, or energy carriers which link technologies
    together, or both.

    ## Parameters

    `id` `(str)`: Used to represent the commodity name.

    `demand_annual` `({region:{year:float}})` - OSeMOSYS AccumulatedAnnualDemand/
    SpecifiedAnnualDemand. Specified for commodities which have an associated
    demand. Optional, defaults to `None`.

    `demand_profile` `({region:{year:{timeslice:float}})` - OSeMOSYS SpecifiedDemandProfile.
    Specified for a demand which varies by
    timeslice. If `demand_annual` is given for a commodity but `demand_profile` is not, the demand
    is treated as having an accumulated demand, which must be met for each year within any
    combination of timeslices. Optional, defaults to `None`.

    `include_in_joint_renewable_target` `({region:{year:bool}})` - OSeMOSYS RETagFuel.
    Boolean tag to mark commodities which are considered
    as renewable for applying renewable generation targets. Optional, defaults to `None`.



    ## Examples

    A simple example of electricity demand data specified by region, years, and timeslices is given
    below, along with how it can be used to create an instance of the Commodity class:

    ```python
    from tz.osemosys.schemas.commodity import Commodity

    basic_demand_profile = dict(
        id="elec",
        demand_annual={"R1": {"2020": 5, "2021": 5, "2022": 5}},
        demand_profile={
            "R1": {
                "2020": {"0h": 0.0, "6h": 0.2, "12h": 0.3, "18h": 0.5},
                "2021": {"0h": 0.0, "6h": 0.2, "12h": 0.3, "18h": 0.5},
                "2022": {"0h": 0.0, "6h": 0.2, "12h": 0.3, "18h": 0.5},
            }
        },
    )

    Commodity(**basic_demand_profile)
    ```

    This model can be expressed more simply using the wildcard `*` for dimensions over which data is
    repeated:

    ```python
    basic_demand_profile = dict(
        id="elec",
        demand_annual={"*": 5},
        demand_profile={"*": {"0h": 0.0, "6h": 0.2, "12h": 0.3, "18h": 0.5}},
    )
    ```

    ## Validation

    `check_demand_exists_if_profile` - This enforces that if `demand_profile` is defined for a
    region and year, `demand_annual` must also be defined.
    """

    demand_annual: OSeMOSYSData.RY | None = Field(None)
    demand_profile: OSeMOSYSData.RYS.SumOne | None = Field(None)
    include_in_joint_renewable_target: OSeMOSYSData.RY.Bool | None = Field(None)

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
