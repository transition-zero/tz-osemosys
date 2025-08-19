from typing import Dict

from pydantic import Field
from pydantic_settings import BaseSettings


class Defaults(BaseSettings):
    """
    Class to contain default values used for when constructing a model directly with tz-osemosys,
    rather than through the otoole compatibility route.
    """

    equals_one_tolerance: float = Field(0.01)
    technology_capacity_activity_unit_ratio: float = Field(1.0)
    technology_capacity_factor: float = Field(1.0)
    technology_availability_factor: float = Field(1.0)
    technology_residual_capacity: float = Field(0.0)
    technology_storage_residual_capacity: float = Field(0.0)
    technology_storage_minimum_charge: float = Field(0.0)
    technology_storage_initial_level: float = Field(0.0)
    technology_capex: float = Field(0.00001)
    technology_opex_variable_cost: float = Field(0.00001)
    technology_opex_fixed_cost: float = Field(0.0)
    technology_operating_life: int = Field(1)
    depreciation_method: str = "sinking-fund"
    discount_rate: float = Field(0.05)
    reserve_margin: float = Field(1.0)
    trade_route: bool = Field(False)
    trade_loss: float = Field(0.00001)
    trade_residual_capacity: float = Field(0.0)
    trade_capex: float = Field(0.00001)
    trade_operating_life: int = Field(1)
    trade_capacity_activity_unit_ratio: float = Field(1.0)
    include_in_region_group: bool = Field(False)


class DefaultsLinopy(BaseSettings):
    """
    Class to contain hard coded default values, for use with xarray/Linopy.

    These will be included in the constructed linopy model regardless of how the tz-osemosys model
    was constructed (either in tz-osemosys directly or through otoole compatibility).
    """

    otoole_name_defaults: Dict = Field(
        default={
            "AvailabilityFactor": 1,
            "CapacityFactor": 1,
            "CapacityToActivityUnit": 1,
            "TradeCapacityToActivityUnit": 1,
            "DepreciationMethod": "straight-line",
            "DiscountRate": 0.1,
            "ResidualCapacity": 0,
            "SpecifiedAnnualDemand": 0,
            "RegionGroupTagRegion": int(False),  # boolean is invalid netcdf
            "TradeRoute": int(False),  # boolean is invalid netcdf
            "CapacityAdditionalMaxFloor": 0,
        }
    )

    otoole_name_storage_defaults: Dict = Field(
        default={
            "DiscountRateStorage": 0.1,
            "ResidualStorageCapacity": 0,
            "StorageLevelStart": 0,
        }
    )


defaults = Defaults()
defaults_linopy = DefaultsLinopy()
