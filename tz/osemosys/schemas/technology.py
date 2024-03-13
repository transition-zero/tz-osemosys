from typing import Any

from pydantic import ConfigDict, Field, conlist, model_validator

from tz.osemosys.defaults import defaults
from tz.osemosys.schemas.base import OSeMOSYSBase, OSeMOSYSData, cast_osemosysdata_value
from tz.osemosys.schemas.compat.technology import OtooleTechnology
from tz.osemosys.schemas.validation.validation_utils import check_min_vals_lower_max


class OperatingMode(OSeMOSYSBase):
    """
    Class for a single operating mode
    # Technology emission activity ratio by mode of operation
    # Technology fuel input activity ratio by mode of operation
    # Technology fuel output activity ratio by mode of operation
    # Binary parameter linking a technology to the storage facility it charges (1 linked)
    # Binary parameter linking a storage facility to the technology it feeds (1 linked)
    """

    model_config = ConfigDict(extra="forbid")

    opex_variable: OSeMOSYSData.RY | None = Field(
        OSeMOSYSData.RY(defaults.technology_opex_variable_cost)
    )
    emission_activity_ratio: OSeMOSYSData.RIY | None = Field(None)
    input_activity_ratio: OSeMOSYSData.RCY | None = Field(None)
    output_activity_ratio: OSeMOSYSData.RCY | None = Field(None)
    to_storage: OSeMOSYSData.RO.Bool | None = Field(None)
    from_storage: OSeMOSYSData.RO.Bool | None = Field(None)

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

    @model_validator(mode="before")
    @classmethod
    def cast_values(cls, values: Any) -> Any:
        for field, info in cls.model_fields.items():
            field_val = values.get(field)

            if field_val is not None:
                values[field] = cast_osemosysdata_value(field_val, info)

        return values


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

    model_config = ConfigDict(extra="forbid")

    # REQUIRED PARAMETERS
    # -----
    operating_life: OSeMOSYSData.R.Int = Field(
        OSeMOSYSData.R.Int(defaults.technology_operating_life)
    )

    operating_modes: conlist(OperatingMode, min_length=1)

    # REQUIRED PARAMETERS WITH DEFAULTS
    # -----
    capex: OSeMOSYSData.RY = Field(OSeMOSYSData.RY(defaults.technology_capex))
    opex_fixed: OSeMOSYSData.RY = Field(OSeMOSYSData.RY(defaults.technology_opex_fixed_cost))
    residual_capacity: OSeMOSYSData.RY = Field(
        OSeMOSYSData.RY(defaults.technology_residual_capacity)
    )
    capacity_activity_unit_ratio: OSeMOSYSData.R = Field(
        OSeMOSYSData.R(defaults.technology_capacity_activity_unit_ratio)
    )
    availability_factor: OSeMOSYSData.RY = Field(
        OSeMOSYSData.RY(defaults.technology_availability_factor)
    )
    capacity_factor: OSeMOSYSData.RYS = Field(OSeMOSYSData.RYS(defaults.technology_capacity_factor))

    # NON-REQUIRED PARAMETERS

    capacity_one_tech_unit: OSeMOSYSData.RY | None = Field(None)
    is_renewable: OSeMOSYSData.RY.Bool | None = Field(None)

    # NON-REQUIRED CONSTRAINTS
    # -----
    # capacity
    capacity_gross_max: OSeMOSYSData.RY | None = Field(None)
    capacity_gross_min: OSeMOSYSData.RY | None = Field(None)
    capacity_additional_max: OSeMOSYSData.RY | None = Field(None)
    capacity_additional_min: OSeMOSYSData.RY | None = Field(None)

    # growth rate # TO BE IMPLEMENTED
    # capacity_additional_max_growth_rate: OSeMOSYSData | None  = Field(None)
    # capacity_additional_max_ceil: OSeMOSYSData | None = Field(None)
    # capacity_additional_max_floor: RegionYearData | None = Field(None)
    # capacity_additional_min_growth_rate: RegionYearData | None  = Field(None)

    # activity
    activity_annual_max: OSeMOSYSData.RY | None = Field(None)
    activity_annual_min: OSeMOSYSData.RY | None = Field(None)
    activity_total_max: OSeMOSYSData.R | None = Field(None)
    activity_total_min: OSeMOSYSData.R | None = Field(None)

    # include this technology in joint reserve margin and renewables targets
    include_in_joint_reserve_margin: OSeMOSYSData.RY.Bool | None = Field(None)
    include_in_joint_renewable_target: OSeMOSYSData.RY.Bool | None = Field(None)

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

        # compose operating modes
        self.operating_modes = [
            operating_mode.compose(**sets) for operating_mode in self.operating_modes
        ]

        return self

    @model_validator(mode="before")
    @classmethod
    def cast_values(cls, values: Any) -> Any:
        for field, info in cls.model_fields.items():
            field_val = values.get(field)

            if field_val is not None:
                values[field] = cast_osemosysdata_value(field_val, info)

        return values

    @model_validator(mode="after")
    def validate_min_lt_max(self):
        # # Broken for now
        # if self.capacity_gross_min is not None and self.capacity_gross_max is not None:
        #     if not check_min_vals_lower_max(
        #         self.capacity_gross_min,
        #         self.capacity_gross_max,
        #         ["REGION", "YEAR", "VALUE"],
        #     ):
        #         raise ValueError(
        #           "Minimum gross capacity is not less than maximum gross capacity.")

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

        return self
