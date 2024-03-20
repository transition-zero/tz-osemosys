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

    The Region class contains data related to regions, including neighbours and trade routes.

    ## Parameters

    `id` `(str)`: Used to represent the region name.

    `neighbours` `(List[str])`: Used to represent the impact name. Optional, defaults to
    `None`.

    `trade_routes` `({region:{commodity:{year:bool}}})` - Boolean tag indicating which other regions
    may trade the specified commodities with the current region. Optional, defaults to
    `None`.

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

    neighbours: List[str] | None = Field(default=None)
    trade_routes: OSeMOSYSData.RCY.Bool | None = Field(default=None)  # R_RCY

    exclude_technologies: List[str] | None = Field(default=None)

    @model_validator(mode="before")
    def validation(cls, values):
        values = reserve_margin_fully_defined(values)
        values = discount_rate_as_decimals(values)
        return values

    def compose(self, **kwargs):
        return self
