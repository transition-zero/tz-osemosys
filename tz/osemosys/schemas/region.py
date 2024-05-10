from typing import List

from pydantic import ConfigDict, Field, model_validator

from tz.osemosys.schemas.base import OSeMOSYSBase, OSeMOSYSData
from tz.osemosys.schemas.compat.region import OtooleRegion
from tz.osemosys.schemas.validation.region_validation import (
    discount_rate_as_decimals,
    reserve_margin_fully_defined,
)

##########
# REGION #
##########


class Region(OSeMOSYSBase, OtooleRegion):
    """
    # Region

    The Region class contains data related to regions, including trade routes. One Region instance
    is given for each region.

    ## Parameters

    `id` `(str)`: Used to represent the region name.

    `trade_routes` `({region:{commodity:{year:bool}}})` - OSeMOSYS TradeRoute.
      Boolean tag indicating which other regions may trade the specified commodities with the
      current region. Optional, defaults to `None`.

    ## Examples

    A simple example of how a region ("R1") might be defined as able to trade the commodity "COAL"
    with region "R2" is given below, along with how it can be used to create an instance of the
    Region class:

    ```python
    from tz.osemosys.schemas.region import Region

    basic_region = dict(
        id="R1",
        trade_routes={"R2": {"COAL": {"2020": True, "2021": True, "2022": True}}},
    )

    Region(**basic_region)
    ```

    This model can be expressed more simply using the wildcard `*` for dimensions over which data is
    repeated:

    ```python
    basic_region = dict(
        id="R1",
        trade_routes={"R2": {"COAL": {"*": True}}},
    )
    ```
    """

    model_config = ConfigDict(extra="forbid")

    trade_routes: OSeMOSYSData.RCY.Bool | None = Field(default=None)  # R_RCY

    exclude_technologies: List[str] | None = Field(default=None)

    @model_validator(mode="before")
    def validation(cls, values):
        values = reserve_margin_fully_defined(values)
        values = discount_rate_as_decimals(values)
        return values

    def compose(self, **sets):
        # compose root OSeMOSYSData
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
