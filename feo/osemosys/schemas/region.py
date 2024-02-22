from typing import List

from pydantic import Field, model_validator

from feo.osemosys.schemas.base import OSeMOSYSBase, OSeMOSYSData
from feo.osemosys.schemas.compat.region import OtooleRegion
from feo.osemosys.schemas.validation.region_validation import (
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

    neighbours: List[str] | None = Field(default=None)
    trade_routes: OSeMOSYSData | None = Field(default=None)

    # composable params
    # reserve_margin: OSeMOSYSData | None = Field(default=None)
    # renewable_production_target: OSeMOSYSData | None = Field(default=None)
    # discount_rate: OSeMOSYSData | None  = Field(default=None)

    # discount_rate_idv: OSeMOSYSData | None  = Field(default=None)
    # discount_rate_storage: OSeMOSYSData | None  = Field(default=None)

    @model_validator(mode="before")
    def validation(cls, values):
        values = reserve_margin_fully_defined(values)
        values = discount_rate_as_decimals(values)
        return values
