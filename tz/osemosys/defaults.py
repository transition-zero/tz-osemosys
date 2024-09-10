from typing import Dict

from pydantic import Field
from pydantic_settings import BaseSettings


class Defaults(BaseSettings):
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


class DefaultsLinopy(BaseSettings):
    """
    Class to contain hard coded default values, for use with xarray/Linopy
    """

    otoole_name_defaults: Dict = Field(
        default={
            "AvailabilityFactor": 1,
            "CapacityFactor": 1,
            "CapacityToActivityUnit": 1,
            "DepreciationMethod": "straight-line",
            "DiscountRate": 0.1,
            "ResidualCapacity": 0,
            "SpecifiedAnnualDemand": 0,
            "TradeRoute": False,
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
