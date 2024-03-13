from typing import Any

from pydantic import Field, model_validator

from tz.osemosys.defaults import defaults
from tz.osemosys.schemas.base import OSeMOSYSBase, OSeMOSYSData, cast_osemosysdata_value
from tz.osemosys.schemas.compat.storage import OtooleStorage
from tz.osemosys.schemas.validation.storage_validation import storage_validation


class Storage(OSeMOSYSBase, OtooleStorage):
    """
    Class to contain all information pertaining to storage technologies
    # Lower bound to the amount of energy stored, as a fraction of the maximum, (0-1)
    # Level of storage at the beginning of first modelled year, in units of activity
    # Maximum discharging rate for the storage, in units of activity per year
    # Maximum charging rate for the storage, in units of activity per year
    """

    # REQUIRED PARAMETERS
    # -------------------
    capex: OSeMOSYSData.RY
    operating_life: OSeMOSYSData.RY.Int

    # NON-REQUIRED PARAMETERS
    # -----------------------
    minimum_charge: OSeMOSYSData.RY = Field(
        OSeMOSYSData.RY(defaults.technology_storage_minimum_charge)
    )
    initial_level: OSeMOSYSData.R = Field(OSeMOSYSData.R(defaults.technology_storage_initial_level))
    residual_capacity: OSeMOSYSData.RY = Field(
        OSeMOSYSData.RY(defaults.technology_storage_residual_capacity)
    )
    max_discharge_rate: OSeMOSYSData.R | None = Field(None)
    max_charge_rate: OSeMOSYSData.R | None = Field(None)

    @model_validator(mode="before")
    @classmethod
    def cast_values(cls, values: Any) -> Any:
        for field, info in cls.model_fields.items():
            field_val = values.get(field)
            if field_val is not None:
                values[field] = cast_osemosysdata_value(field_val, info)

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

    @model_validator(mode="before")
    def validator(cls, values):
        values = storage_validation(values)
        return values
