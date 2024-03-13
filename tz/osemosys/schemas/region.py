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
    Class to contain all information pertaining to regions and trade routes including:
    - discount rates
    - reserve margins
    - renewable production targets
    - depreciation method
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
