# RunSpec

The Runspec class contains all data required to run an OSeMOSYS model, spread across subclasses,
with some parameters inherent to the RunSpec object itself.

## Parameters

`id` `(str)`: Used to represent the name of the OSeMOSYS model.
Required parameter.

`time_definition` `(TimeDefinition)` - Single TimeDefinition class instance to contain all
temporal data related to the model. Required parameter.

`regions` `(List[Region])` - List of Region instances to contain region names.
Required parameter.

`commodities` `(List[Commodity])` - List of Commodity instances to contain all data related to
commodities (OSeMOSYS FUEL).
Required parameter.

`impacts` `(List[Impact])` - List of Impact instances to contain all data related to impacts
(OSeMOSYS EMISSION).
Required parameter.

`technologies` `(List[Technology])` - List of Technology instances to contain all data
related to technologies.
Required parameter.

`storage` `(List[Storage])` - List of Storage instances to contain all data related to storage.
Optional parameter, defaults to `None`.

`trade` `(List[Trade])` - List of Trade instances to contain all data related to trade routes.
Optional parameter, defaults to `None`.

`depreciation_method` `({region:str})` - OSeMOSYS DepreciationMethod.
Parameter defining the type of depreciation to be applied, must take values of 'sinking-fund' or
'straight-line'.
Optional parameter, defaults to 'sinking-fund'.

`discount_rate` `({region:float})` - OSeMOSYS DiscountRate.
Region specific value for the discount rate.
Optional parameter, defaults to 0.05.

`cost_of_capital` `({region:{technology:float}})` - OSeMOSYS DiscountRateIdv.
Discount rate specified by region and technology.
Optional parameter, defaults to `None`.

`cost_of_capital_storage` `({region:{storage:float}})` - OSeMOSYS DiscountRateStorage.
Discount rate specified by region and storage.
Optional parameter, defaults to `None`.

`reserve_margin` `({region:{year:float}})` - OSeMOSYS ReserveMargin.
Minimum level of the reserve margin required to be provided for all the tagged commodities, by
the tagged technologies. If no reserve margin is required, the parameter will have value 1; if,
for instance, 20% reserve margin is required, the parameter will have value 1.2.
Optional parameter, defaults to 1.

`renewable_production_target` `({region:{year:float}})` - OSeMOSYS REMinProductionTarget.
Minimum ratio of all renewable commodities tagged in the include_in_joint_renewable_target parameter, to be
produced by the technologies tagged with the include_in_joint_renewable_target parameter.
Optional parameter, defaults to `None`.

## Examples

### From dicts

A simple example of how a Runspec object might be created directly from provided data is below:

```python
from tz.osemosys import (
    Model,
    Technology,
    TimeDefinition,
    Commodity,
    Region,
    Impact,
    OperatingMode,
)

time_definition = TimeDefinition(id="years-only", years=range(2020, 2051))
regions = [Region(id="single-region")]
commodities = [Commodity(id="electricity", demand_annual=25 * 8760)]  # 25GW * 8760hr/yr
impacts = [Impact(id="CO2", penalty=60)]  # 60 $mn/Mtonne
technologies = [
    Technology(
        id="coal-gen",
        operating_life=40,  # years
        capex=800,  # mn$/GW
        # straight-line reduction to 2040
        residual_capacity={
            yr: 25 * max((1 - (yr - 2020) / (2040 - 2020), 0))
            for yr in range(2020, 2051)
        },
        operating_modes=[
            OperatingMode(
                id="generation",
                # $mn20/Mt.coal / 8.14 TWh/Mt coal * 8760 GWh/GW / 0.3 /1000 GWh/TWh (therm eff)
                opex_variable=20 / 8.14 * 8760 / 0.3 / 1000,  # $71/GW/yr
                output_activity_ratio={"electricity": 1.0 * 8760},  # GWh/yr/GW
                emission_activity_ratio={
                    "CO2": 0.354 * 8760 / 1000
                },  # Mtco2/TWh * 8760GWh/Gw/yr /1000 GWh/TWh
            )
        ],
    ),
    Technology(
        id="solar-pv",
        operating_life=25,
        capex=1200,
        capacity_factor=0.3,
        operating_modes=[
            OperatingMode(
                id="generation",
                opex_variable=0,
                output_activity_ratio={"electricity": 1.0 * 8760},  # GWh/yr/GW
            )
        ],
    ),
]

model = Model(
    id="simple-carbon-price",
    time_definition=time_definition,
    regions=regions,
    commodities=commodities,
    impacts=impacts,
    technologies=technologies,
)
```
### From csv

A runspec object can also be created from a set of otoole style CSVs as below, using the class
method from_otoole_csv():

```python
from tz.osemosys.schemas import RunSpec

path_to_csvs = "examples/otoole_compat/input_csv/otoole-full-electricity-complete/"

run_spec_object = RunSpec.from_otoole_csv(root_dir=path_to_csvs)
```

### From yaml

Alternatively, a model can be created from a osemosys style yaml, examples of which can be
found in the tz-osemosys repository.

```python
from tz.osemosys.io.load_model import load_model

path_to_yaml = "examples/utopia/main.yaml"

run_spec_object = load_model(path_to_yaml)
```
