from typing import Any

from pydantic import Field, model_validator

from tz.osemosys.defaults import defaults
from tz.osemosys.schemas.base import OSeMOSYSBase, OSeMOSYSData, cast_osemosysdata_value
from tz.osemosys.schemas.compat.storage import OtooleStorage
from tz.osemosys.schemas.validation.storage_validation import storage_validation


class Storage(OSeMOSYSBase, OtooleStorage):
    """
    # Storage

    The Storage class contains data related to storage. One Storage instance is given for each
    storage technology.

    ## Parameters

    `id` `(str)`: Used to represent the storage name.

    `capex` `({region:{year:float}})` - OSeMOSYS CapitalCostStorage.
    Investment costs of storage additions, defined per unit of storage capacity.
    Required parameter, must be specified by user.

    `operating_life` `({region:int})` - OSeMOSYS OperationalLifeStorage.
    Useful lifetime of the storage facility in years.
    Required parameter, must be specified by user.

    `minimum_charge` `({region:{year:float}})` - OSeMOSYS MinStorageCharge.
    It sets a lower bound to the amount of energy stored, as a fraction of the maximum, with a
    number reanging between 0 and 1. The storage facility cannot be emptied below this level.
    Optional, defaults to 0.

    `initial_level` `({region:float})` - OSeMOSYS StorageLevelStart.
    Level of storage at the beginning of first modelled year, in units of activity.
    Optional, defaults to 0.

    `residual_capacity` `({region:{year:float}})` - OSeMOSYS ResidualStorageCapacity.
    Exogenously defined storage capacities.
    Optional, defaults to 0.

    `max_discharge_rate` `({region:float})` - OSeMOSYS StorageMaxDischargeRate.
    Maximum discharging rate for the storage, in units of activity per year.
    Optional, defaults to `None`.

    `max_charge_rate` `({region:float})` - OSeMOSYS StorageMaxChargeRate.
    Maximum charging rate for the storage, in units of activity per year.
    Optional, defaults to `None`.


    ## Examples

    A simple example of how a storage technology "STO" might be defined is shown below,
    along with how it can be used to create an instance of the Storage class:

    ```python
    from tz.osemosys.schemas.storage import Storage

    basic_storage = dict(
        id="STO",
        capex={"*": {"*": 100}},
        operating_life={"*": 10},
        minimum_charge={"*": {"*": 0}},
        initial_level={"*": 1},
        residual_capacity={"*": {2020: 3, 2021: 2, 2022: 1}},
        max_discharge_rate={"*": 100},
        max_charge_rate={"*": 100},
    )

    Storage(**basic_storage)
    ```
    """

    # REQUIRED PARAMETERS
    # -------------------
    capex: OSeMOSYSData.RY
    operating_life: OSeMOSYSData.R.Int

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
