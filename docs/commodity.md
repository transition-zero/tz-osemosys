# Commodity

The Commodity class contains all data related to commodities (OSeMOSYS 'FUEL'), including
demands and tags for whether the commodity is counted as renewable or part of the reserve margin
. One Commodity instance is given for each commodity.

Commodities can either be final energy demands, or energy carriers which link technologies
together, or both.

## Parameters

`id` `(str)`: Used to represent the commodity name.

`demand_annual` `({region:{year:float}})` - OSeMOSYS AccumulatedAnnualDemand/
SpecifiedAnnualDemand. Specified for commodities which have an associated
demand. Optional, defaults to `None`.

`demand_profile` `({region:{year:{timeslice:float}})` - OSeMOSYS SpecifiedDemandProfile.
Specified for a demand which varies by
timeslice. If `demand_annual` is given for a commodity but `demand_profile` is not, the demand
is treated as having an accumulated demand, which must be met for each year within any
combination of timeslices. Optional, defaults to `None`.

`include_in_joint_renewable_target` `({region:{year:bool}})` - OSeMOSYS RETagFuel.
Boolean tag to mark commodities which are considered
as renewable for applying renewable generation targets. Optional, defaults to `None`.



## Examples

A simple example of electricity demand data specified by region, years, and timeslices is given
below, along with how it can be used to create an instance of the Commodity class:

```python
from tz.osemosys.schemas.commodity import Commodity

basic_demand_profile = dict(
    id="elec",
    demand_annual={"R1": {"2020": 5, "2021": 5, "2022": 5}},
    demand_profile={
        "R1": {
            "2020": {"0h": 0.0, "6h": 0.2, "12h": 0.3, "18h": 0.5},
            "2021": {"0h": 0.0, "6h": 0.2, "12h": 0.3, "18h": 0.5},
            "2022": {"0h": 0.0, "6h": 0.2, "12h": 0.3, "18h": 0.5},
        }
    },
)

Commodity(**basic_demand_profile)
```

This model can be expressed more simply using the wildcard `*` for dimensions over which data is
repeated:

```python
basic_demand_profile = dict(
    id="elec",
    demand_annual={"*": 5},
    demand_profile={"*": {"0h": 0.0, "6h": 0.2, "12h": 0.3, "18h": 0.5}},
)
```

## Validation

`check_demand_exists_if_profile` - This enforces that if `demand_profile` is defined for a
region and year, `demand_annual` must also be defined.
