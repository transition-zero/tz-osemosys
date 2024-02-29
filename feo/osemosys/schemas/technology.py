from typing import Any

from pydantic import Field, conlist, model_validator

from feo.osemosys.defaults import defaults
from feo.osemosys.schemas.base import OSeMOSYSBase, OSeMOSYSData, OSeMOSYSData_Int
from feo.osemosys.schemas.compat.technology import OtooleTechnology
from feo.osemosys.schemas.validation.technology_validation import technology_storage_validation
from feo.osemosys.schemas.validation.validation_utils import check_min_vals_lower_max
from feo.osemosys.utils import isnumeric

# ##################
# ### TECHNOLOGY ###
# ##################


class OperatingMode(OSeMOSYSBase):
    """
    Class for a single operating mode
    # Technology emission activity ratio by mode of operation
    # Technology fuel input activity ratio by mode of operation
    # Technology fuel output activity ratio by mode of operation
    # Binary parameter linking a technology to the storage facility it charges (1 linked)
    # Binary parameter linking a storage facility to the technology it feeds (1 linked)
    """

    opex_variable: OSeMOSYSData | None = Field(None)
    emission_activity_ratio: OSeMOSYSData | None = Field(None)
    input_activity_ratio: OSeMOSYSData | None = Field(None)
    output_activity_ratio: OSeMOSYSData | None = Field(None)
    to_storage: OSeMOSYSData_Int | None = Field(None)
    from_storage: OSeMOSYSData_Int | None = Field(None)


class Technology(OSeMOSYSBase, OtooleTechnology):
    """
    Class to contain all information pertaining to technologies (excluding storage technologies)

    # Capacity unit to activity unit conversion:
    #   Conversion factor relating the energy that would be produced when one unit of capacity is
    #   fully used in one year.
    # Capacity of one new unit of a technology
    # If specified the problem will turn into a Mixed Integer Linear Problem
    # Capacity factor and availability availability
    # -----
    # Maximum time a technology can run in the whole year, as a fraction from 0 to 1
    #     Maximum technology capacity (installed + residual) per year
    # Minimum technology capacity (installed + residual) per year
    # Maximum technology capacity additions per year
    # Minimum technology capacity additions per year
    # Maximum technology activity per year
    # Minimum technology activity per year
        # Maximum technology activity across whole modelled period
    # Minimum technology activity across whole modelled period
    # growth rate (<1.)
    Absolute value (ceil relative to growth rate)
    """

    # REQUIRED PARAMETERS
    # -----
    operating_life: OSeMOSYSData_Int | None
    capex: OSeMOSYSData | None
    opex_fixed: OSeMOSYSData | None

    operating_modes: conlist(OperatingMode, min_length=1)

    # NON-REQUIRED PARAMETERS
    # -----
    residual_capacity: OSeMOSYSData | None = Field(
        OSeMOSYSData(defaults.technology_residual_capacity)
    )
    capacity_activity_unit_ratio: OSeMOSYSData | None = Field(
        OSeMOSYSData(defaults.technology_capacity_activity_unit_ratio)
    )
    capacity_one_tech_unit: OSeMOSYSData | None = Field(None)
    availability_factor: OSeMOSYSData | None = Field(
        OSeMOSYSData(defaults.technology_availability_factor)
    )
    capacity_factor: OSeMOSYSData | None = Field(OSeMOSYSData(defaults.technology_capacity_factor))
    is_renewable: OSeMOSYSData | None = Field(None)

    # NON-REQUIRED CONSTRAINTS
    # -----
    # capacity
    capacity_gross_max: OSeMOSYSData | None = Field(None)
    capacity_gross_min: OSeMOSYSData | None = Field(None)
    capacity_additional_max: OSeMOSYSData | None = Field(None)
    capacity_additional_min: OSeMOSYSData | None = Field(None)

    # growth rate # TO BE IMPLEMENTED
    # additional_capacity_max_growth_rate: OSeMOSYSData | None  = Field(None)
    # additional_capacity_max_ceil: OSeMOSYSData | None = Field(None)
    # additional_capacity_max_floor: RegionYearData | None = Field(None)
    # additional_capacity_min_growth_rate: RegionYearData | None  = Field(None)

    # activity
    activity_annual_max: OSeMOSYSData | None = Field(None)
    activity_annual_min: OSeMOSYSData | None = Field(None)
    activity_total_max: OSeMOSYSData | None = Field(None)
    activity_total_min: OSeMOSYSData | None = Field(None)

    @model_validator(mode="before")
    @classmethod
    def cast_values(cls, values: Any) -> Any:
        for field, info in cls.model_fields.items():
            field_val = values.get(field)

            if all(
                [
                    field_val is not None,
                    isinstance(field_val, int),
                    "OSeMOSYSData_Int" in str(info.annotation),
                ]
            ):
                values[field] = OSeMOSYSData_Int(field_val)
            elif all(
                [
                    field_val is not None,
                    isnumeric(field_val),
                    "OSeMOSYSData" in str(info.annotation),
                ]
            ):
                values[field] = OSeMOSYSData(field_val)

        return values

    @model_validator(mode="after")
    def validate_min_lt_max(self):
        if self.capacity_gross_min is not None and self.capacity_gross_max is not None:
            if not check_min_vals_lower_max(
                self.capacity_gross_min,
                self.capacity_gross_max,
                ["REGION", "YEAR", "VALUE"],
            ):
                raise ValueError("Minimum gross capacity is not less than maximum gross capacity.")

        if self.capacity_additional_min is not None and self.capacity_additional_max is not None:
            if not check_min_vals_lower_max(
                self.capacity_additional_min,
                self.capacity_additional_max,
                ["REGION", "YEAR", "VALUE"],
            ):
                raise ValueError("Minimum gross capacity is not less than maximum gross capacity.")

        if self.activity_annual_min is not None and self.activity_annual_max is not None:
            if not check_min_vals_lower_max(
                self.activity_annual_min,
                self.activity_annual_max,
                ["REGION", "YEAR", "VALUE"],
            ):
                raise ValueError(
                    "Minimum annual activity is not less than maximum annual activity."
                )

        if self.activity_total_min is not None and self.activity_total_max is not None:
            if not check_min_vals_lower_max(
                self.activity_total_min,
                self.activity_total_max,
                ["REGION", "VALUE"],
            ):
                raise ValueError("Minimum total activity is not less than maximum total activity.")

        return True


class TechnologyStorage(OSeMOSYSBase):
    """
    Class to contain all information pertaining to storage technologies
    """

    capex: OSeMOSYSData | None
    operating_life: OSeMOSYSData_Int | None
    # Lower bound to the amount of energy stored, as a fraction of the maximum, (0-1)
    # Level of storage at the beginning of first modelled year, in units of activity
    # Maximum discharging rate for the storage, in units of activity per year
    # Maximum charging rate for the storage, in units of activity per year

    # REQUIRED PARAMETERS
    # -------------------
    capex: OSeMOSYSData
    operating_life: OSeMOSYSData_Int

    # NON-REQUIRED PARAMETERS
    # -----------------------
    minimum_charge: OSeMOSYSData = Field(OSeMOSYSData(defaults.technology_storage_minimum_charge))
    initial_level: OSeMOSYSData = Field(OSeMOSYSData(defaults.technology_storage_initial_level))
    residual_capacity: OSeMOSYSData = Field(
        OSeMOSYSData(defaults.technology_storage_residual_capacity)
    )
    max_discharge_rate: OSeMOSYSData | None = Field(None)
    max_charge_rate: OSeMOSYSData | None = Field(None)

    @model_validator(mode="before")
    def validator(cls, values):
        values = technology_storage_validation(values)
        return values
