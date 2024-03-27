# Impact

The Impact class contains all data related to impacts, i.e. externalities (OSeMOSYS 'EMISSION'),
including constraints, exogenous impacts, and penalties. One Impact instance is given for each
impact.

## Parameters

`id` `(str)`: Used to represent the impact name.

`constraint_annual` `({region:{year:float}})` - OSeMOSYS AnnualEmissionLimit.
    Annual impact constraint. Optional, defaults to `None`.

`constraint_total` `({region:float})` - OSeMOSYS ModelPeriodEmissionLimit.
    Total modelling period impact constraint. Optional, defaults to `None`.

`exogenous_annual` `({region:{year:float}})` - OSeMOSYS AnnualExogenousEmission.
    Annual exogenous impact. Optional, defaults to `None`.

`exogenous_total` `({region:float})` - OSeMOSYS ModelPeriodExogenousEmission.
    Total modelling period exogenous impact. Optional, defaults to `None`.

`penalty` `({region:{year:float}})` - OSeMOSYS EmissionsPenalty.
    Financial penalty for each unit impact. Optional, defaults to `None`.


## Examples

A simple example of how an impact might be defined is given
below, along with how it can be used to create an instance of the Impact class:

```python
from tz.osemosys.schemas.impact import Impact

basic_impact = dict(
    id="CO2e",
    constraint_annual={"R1": {"2020": 2.0, "2021": 2.0, "2022": 2.0}},
    constraint_total={"R1": 5.0},
    exogenous_annual={"R1": {"2020": 1.0, "2021": 1.0, "2022": 1.0}},
    exogenous_total={"R1": 1.0},
    penalty={"R1": {"2020": 1.0, "2021": 1.0, "2022": 1.0}},
)

Impact(**basic_impact)
```

This model can be expressed more simply using the wildcard `*` for dimensions over which data is
repeated:

```python
basic_impact = dict(
    id="CO2e",
    constraint_annual={"R1": {"*": 2.0}},
    constraint_total={"R1": 5.0},
    exogenous_annual={"R1": {"*": 1.0}},
    exogenous_total={"R1": 1.0},
    penalty={"R1": {"*": 1.0}},
)
```

## Validation

`validate_exogenous_lt_constraint` - This enforces that if `exogenous_annual` should be lower
than `constraint_annual`, and `exogenous_total` should be lower than `constraint_total`, for
the relevant regions and years.
