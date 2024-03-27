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
