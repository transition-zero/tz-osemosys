# **MODEL**

The Model class contains all data required to run a TZ-OSeMOSYS model, spread across subclasses,
along with class methods for loading/constructing and solving a model.

The parameters associated with each subclass are listed in the subsequent documentation pages (e.g.
see [Technologies](https://docs.feo.transitionzero.org/docs/tz-osemosys/technology/)).

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

`cost_of_capital_trade` `({region:{region:{commodity:float}}})` - Parameter additional to
OSeMOSYS base variables. Discount rate specified for trade (transmission) technologies.
Optional parameter, defaults to `None`.

`reserve_margin` `({region:{year:float}})` - OSeMOSYS ReserveMargin.
Minimum level of the reserve margin required to be provided for all the tagged commodities, by
the tagged technologies. If no reserve margin is required, the parameter will have value 1; if,
for instance, 20% reserve margin is required, the parameter will have value 1.2.
Optional parameter, defaults to 1.

`renewable_production_target` `({region:{year:float}})` - OSeMOSYS REMinProductionTarget.
Minimum ratio of all renewable commodities tagged in the
include_in_joint_renewable_target parameter, to be
produced by the technologies tagged with the include_in_joint_renewable_target parameter.
Optional parameter, defaults to `None`.

## Loading/constructing a model

### From dicts

A simple example of how a Model object might be created directly from provided data is below:

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

A Model object can also be created from a set of otoole style CSVs as below, using the class
method from_otoole_csv():

```python
from tz.osemosys import Model

path_to_csvs = "examples/otoole_compat/input_csv/otoole-full-electricity-complete/"

model = Model.from_otoole_csv(root_dir=path_to_csvs)
```

### From yaml

Alternatively, a model can be created from a TZ-OSeMOSYS yaml or set of yamls, examples of
which can be found in the tz-osemosys repository.

```python
from tz.osemosys import Model

path_to_yaml = "examples/utopia/main.yaml"

model = Model.from_yaml(path_to_yaml)
```

## Solving a model

Once a model object has been constructed or loaded via one of the above methods, it can be
solved by calling the solve() method.

```python
from tz.osemosys import Model

path_to_yaml = "examples/utopia/main.yaml"

model = Model.from_yaml(path_to_yaml)

model.solve()
```

By default, the model will be solved using the first available solver in the list of available
solvers. To specify a solver, pass the name of the solver as a string to the solve() method for
the argument `solver` (e.g. `model.solve(solver="highs")`).

### Viewing the model solution

Once the model has been solved, the solution can be accessed via the `solution` attribute of the
model object, which returns an [Xarray](https://xarray.dev/) [Dataset](https://docs.xarray.dev/en/stable/generated/xarray.Dataset.html).

To display all available solution [DataArrays](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.html) within the solution Dataset, run:
```python
model.solution.data_vars
```

To view the values of a specific DataArray, such as NewCapacity, run:
```python
model.solution["NewCapacity"]
```

This can be converted to a more easily readible format by converting to a [pandas](https://pandas.pydata.org/) [DataFrame](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html), which mimicks the structure of an excel file (the pandas package may need to be installed with the command 'pip install pandas'):
```python
model.solution["NewCapacity"].to_dataframe().reset_index()
```

Each DataArray has its own set of [coordinates](https://docs.xarray.dev/en/latest/generated/xarray.Coordinates.html).
These coordinates show the relevant dimensions over which the selected solution DataArray applies.
For example, NewCapacity has dimensions of "REGION", "TECHNOLOGY", and "YEAR".
The coordinates for each of these dimensions then correspond to the possible values, given how the model is set up.
A model with 1 region, 5 technologies, and 10 years, would give a DataArray for NewCapacity of size 1 by 5 by 10; with the named technologies etc. forming the cooordinates.

### Writing the model solution to excel

Writing a specfic DataArray (NewCapacity) to an excel file can be done by running the following:
```python
model.solution["NewCapacity"].to_dataframe().reset_index().to_excel(
    "NewCapacity.xlsx", index=False
)
```

All DataArrays in the model solution can be written to excel files by running the following:
```python
for array in model.solution:
    model.solution[array].to_dataframe().reset_index().to_excel(
        f"{array}.xlsx", index=False
    )
```
# **TECHNOLOGY**

The Technology class contains data related to technologies and operating modes.
One Technology instance is given for each technology.

One parameter of the Technology class is the OperatingMode subclass, which contains all
technology data which has an operating mode associated with it. See the "Operating modes"
documentation for a more detailed description.

## Parameters

`id` `(str)` - Used to represent the technology name.

`operating_modes` `(List[OperatingMode])` - A list containing one OperatingMode object for each
operating mode relevant to the current technology. Each OperatingMode object contains data
relevant for the corresponding operating mode, ie.e. input/output/emission activity ratios,
variable costs, tag linking the technology to storage. See the "Operating modes" documentation for
a more detailed description.

`operating_life` `({region:int})` - OSeMOSYS OperationalLife. Integer value of operating life
in years for the given technology class. Optional, defaults to 1.

`capex` `({region:{year:float}})` - OSeMOSYS CapitalCost. Overnight investment cost per
capacity unit. Optional, defaults to 0.00001.

`opex_fixed` `({region:{year:float}})` - OSeMOSYS FixedCost. Fixed annual operating costs per
capacity unit. Optional, defaults to 0.00001.

`residual_capacity` `({region:{year:float}})` - OSeMOSYS ResidualCapcity.
Optional, defaults to 0.

`capacity_activity_unit_ratio` `({region:float})` - OSeMOSYS CapacityToActivityUnit.
Conversion factor relating the energy that would be produced when one unit of capacity is
fully used in one year. Optional, defaults to 1.

`availability_factor` `({region:{year:float}})` - OSeMOSYS AvailabilityFactor.
Maximum time a technology can run in the whole year, as a fraction of the year ranging from 0
to 1. It gives the possibility to account for planned outages.
Optional, defaults to 1.

`capacity_factor` `({region:{year:{timeslice:float}}})` - OSeMOSYS CapacityFactor.
Capacity available per each timeslice, expressed as a fraction of the total installed capacity,
with values ranging from 0 to 1. It gives the possibility to account for forced outages.
Optional, defaults to 1.

`capacity_factor_annual_min` `({region:{year:float}})` - OSeMOSYS style name
TotalAnnualMinCapacityFactor. Must run capacity constraint at annual level expressed as a
fraction of the total installed capacity, with values ranging from 0 to 1. Optional, defaults
to `None`.

`capacity_one_tech_unit` `({region:{year:float}})` - OSeMOSYS CapacityOfOneTechnologyUnit.
Capacity of one new unit of a technology. In case the user sets this parameter, the related
technology will be installed only in batches of the specified capacity and the problem will
turn into a Mixed Integer Linear Problem. Optional, defaults to `None`.

`include_in_joint_renewable_target` `({region:{year:bool}})` - OSeMOSYS RETagTechnology.
Boolean tagging the renewable technologies that must contribute to reaching the indicated
minimum renewable production target. It has value True for the technologies contributing,
False otherwise. Optional, defaults to `None`.

`include_in_joint_reserve_margin` `({region:{year:bool}})` - OSeMOSYS
ReserveMarginTagTechnology. Boolean tagging the technologies that can contribute to reaching the
    indicated reserve margin. It has value True for the technologies contributing, False otherwise.
    Optional, defaults to `None`.

`capacity_gross_max` `({region:{year:float}})` - OSeMOSYS TotalAnnualMaxCapacity.
Total maximum existing (residual plus cumulatively installed) capacity allowed for a technology
in a specified year. Optional, defaults to `None`.

`capacity_gross_min` `({region:{year:float}})` - OSeMOSYS TotalAnnualMinCapacity.
Total minimum existing (residual plus cumulatively installed) capacity allowed for a technology
in a specified year. Optional, defaults to `None`.

`capacity_additional_max` `({region:{year:float}})` - OSeMOSYS TotalAnnualMaxCapacityInvestment.
Maximum capacity investment of a technology, expressed in power units. Optional, defaults to
`None`.

`capacity_additional_max_growth_rate` `({region:{year:float}})` - New parameter, OSeMOSYS style name CapacityAdditionalMaxGrowthRate. Maximum allowed annual percentage growth in the given technology's capacity, expressed as a decimal (e.g. 0.2 for 20%). Optional, defaults to `None`.

`capacity_additional_max_floor` `({region:{year:float}})` - New parameter, OSeMOSYS style name
    CapacityAdditionalMaxFloor. If used in conjunction with capacity_additional_max_growth_rate,
     the model may build new capacity at this floor value, in addition to the previous year's
     capacity * growth rate. This can act as a 'seed' value where no or minimal capacity exists
     for the technology to which a growth rate is applied. Optional, defaults to `None`.

`capacity_additional_min` `({region:{year:float}})` - OSeMOSYS TotalAnnualMinCapacityInvestment.
Minimum capacity investment of a technology, expressed in power units. Optional, defaults to
`None`.

`capacity_additional_min_growth_rate` `(({region:{year:float}}))` - New parameter, OSeMOSYS style name CapacityAdditionalMinGrowthRate. Minimum allowed annual percentage growth in the given technology's capacity, expressed as a decimal (e.g. 0.2 for 20%). Optional, defaults to `None`.

`activity_annual_max` `({region:{year:float}})` - OSeMOSYS
TotalTechnologyAnnualActivityUpperLimit.
Total maximum level of activity allowed for a technology in one year.
Optional, defaults to `None`.

`activity_annual_min` `({region:{year:float}})` - OSeMOSYS
TotalTechnologyAnnualActivityLowerLimit.
Total minimum level of activity allowed for a technology in one year.
Optional, defaults to `None`.

`activity_total_max` `({region:float})` - OSeMOSYS TotalTechnologyModelPeriodActivityUpperLimit.
Total maximum level of activity allowed for a technology in the entire modelled period.
Optional, defaults to `None`.

`activity_total_min` `({region:float})` - OSeMOSYS TotalTechnologyModelPeriodActivityLowerLimit.
Total minimum level of activity allowed for a technology in the entire modelled period.
Optional, defaults to `None`.


## Examples

A simple example of how a Technology could be defined is given below, along with how it can be
used to create an instance of the Technology class (the OperatingMode class needs to be
imported along with the Technology Class):

```python
from tz.osemosys.schemas.technology import Technology, OperatingMode

basic_technology = dict(
    id="coal-gen",
    operating_life=40,  # years
    capex=800,  # mn$/GW
    # straight-line reduction to 2040
    residual_capacity={
        yr: 25 * max((1 - (yr - 2020) / (2040 - 2020), 0)) for yr in range(2020, 2051)
    },
    operating_modes=[
        OperatingMode(
            id="generation",
            # $mn20/Mt.coal / 8.14 TWh/Mt coal * 8760 GWh/GW / 0.3 /1000 GWh/TWh (therm eff)
            opex_variable=20 / 8.14 * 8760 / 0.3 / 1000,  # $71/GW/yr
            output_activity_ratio={"electricity": 1.0 * 8760},  # GWh/yr/GW
            emission_activity_ratio={
                "CO2": 0.354 * 8760 / 1000  # Mtco2/TWh * 8760GWh/Gw/yr /1000 GWh/TWh
            },
        )
    ],
)

Technology(**basic_technology)
```
# **OPERATING MODE**

The OperatingMode class contains data related to one specific operating mode and one specific
technology. Any instance of the OperatingMode class is always a parameter of a Technology class.

## Parameters

`id` `(str)`: Used to represent the operating mode name. Equivalent to the OSeMOSYS set
MODE_OF_OPERATION.

`opex_variable` `({region:{year:float}})` - OSeMOSYS VariableCost.
Cost of a technology for a given mode of operation (Variable O&M cost), per unit of activity.
Optional, defaults to `None`.

`emission_activity_ratio` `({region:{impact:{year:float}}})` - OSeMOSYS EmissionActivityRatio.
Emission factor of a technology per unit of activity.
Optional, defaults to `None`.

`input_activity_ratio` `({region:{commodity:{year:float}}})` - OSeMOSYS InputActivityRatio.
Rate of use of a commodity by a technology, as a ratio of the rate of activity.
Optional, defaults to `None`.

`output_activity_ratio` `({region:{commodity:{year:float}}})` - OSeMOSYS OutputActivityRatio.
Rate of commodity output from a technology, as a ratio of the rate of activity. By convention this
usually takes a value of 1.0 for technologies producing a commodity, and efficiency is added to the model via input_activity_ratio. Optional, defaults to `None`.

`to_storage` `({region:{storage:bool}})` - OSeMOSYS TechnologyToStorage.
Boolean parameter linking a technology to the storage facility it charges. It has value True if
the technology and the storage facility are linked, False otherwise.
Optional, defaults to `None`.

`from_storage` `({region:{storage:bool}})` - OSeMOSYS TechnologyFromStorage.
Boolean parameter linking a storage facility to the technology it feeds. It has value True if
the technology and the storage facility are linked, False otherwise.
Optional, defaults to `None`.

## Examples

Below is the OperatingMode example taken from Technology class example for a coal powerplant.

```python
from tz.osemosys.schemas.technology import OperatingMode

basic_operating_mode = dict(
    id="generation",
    # $mn20/Mt.coal / 8.14 TWh/Mt coal * 8760 GWh/GW / 0.3 /1000 GWh/TWh (therm eff)
    opex_variable=20 / 8.14 * 8760 / 0.3 / 1000,  # $71/GW/yr
    output_activity_ratio={"electricity": 1.0},
    emission_activity_ratio={
        "CO2": 0.354 * 8760 / 1000  # Mtco2/TWh * 8760GWh/Gw/yr /1000 GWh/TWh
    },
)

OperatingMode(**basic_operating_mode)
```
# **REGION**

The Region class contains data related to regions. One Region instance
is given for each region.

## Parameters

`id` `(str)`: Used to represent the region name.

## Examples

A simple example of how a region ("R1") might be defined is given below, along with how it can
be used to create an instance of the Region class:

```python
from tz.osemosys.schemas.region import Region

basic_region = dict(
    id="R1",
)

Region(**basic_region)
```
# **TIME DEFINITION**

The TimeDefinition class contains all temporal data needed for an OSeMOSYS model. There are
multiple pathways to creating a TimeDefinition object, where any missing information is
inferred from the data provided.

Only a single instance of TimeDefinition is needed to run a model and, as a minimum, only
`years` need to be provided to create a TimeDefinition object.

The other parameters corresponding to the OSeMOSYS time related sets (`seasons`, `timeslices`,
`day_types`, `daily_time_brackets`) can be provided as lists or ranges.

One parameter additional to those correponsding to OSeMOSYS parameters is used , `adj`,
which specified the adjency matrices for `years`, `seasons`, `day_types`,
`daily_time_brackets`, `timeslices`. If not providing values for `adj`, it is assumed that
the other variables are provided in order from first to last. If providing the values directly,
these can be provided as a dict, an example of which for years and timeslices is below:

```python
adj = {
    "years": dict(zip(range(2020, 2050), range(2021, 2051))),
    "timeslices": {"A": "B", "B": "C", "C": "D"},
}
```

### Pathway 1 - Construction from years only

If only `years` are provided, the remaining necessary temporal parameters (`seasons`,
`day_types`, `daily_time_brackets`) are assumed to be singular.

### Pathway 2 - Construction from parts

If no timeslice data is provided, but any of the below is, it is used to construct timeslices:
    - seasons
    - daily_time_brackets
    - day_types
    - year_split
    - day_split
    - days_in_day_type

### Pathway 3 - Construction from timeslices

If timeslices are provided via any of the below parameters, this is used to construct the
TimeDefinition object:
    - timeslices
    - timeslice_in_timebracket
    - timeslice_in_daytype
    - timeslice_in_season


## Parameters

`id` `(str)`: Any value may be provided for the single TimeDefintion instance.
Required parameter.

`years` `(List[int] | range(int)) | int`: OSeMOSYS YEARS. Required parameter.

`seasons` `(List[int | str]) | int`: OSeMOSYS SEASONS.
Optional, constructed if not provided.

`timeslices` `(List[int | str]) | int`: OSeMOSYS TIMESLICES.
Optional, constructed if not provided.

`day_types` `(List[int | str]) | int`: OSeMOSYS DAYTYPES.
Optional, constructed if not provided.

`daily_time_brackets` `(List[int | str])`: OSeMOSYS DAILYTIMEBRACKETS.
Optional, constructed if not provided.

`year_split` `({timeslice:{year:float}})`: OSeMOSYS YearSplit.
Optional, constructed if not provided.

`day_split` `({daily_time_bracket:{year:float}})`: OSeMOSYS DaySplit.
Optional, constructed if not provided.

`days_in_day_type` `({season:{day_type:{year:int}}})`: OSeMOSYS DaysInDayType.
Optional, constructed if not provided.

`timeslice_in_timebracket` `({timeslice:daily_time_bracket})`: OSeMOSYS Conversionlh.
Optional, constructed if not provided.

`timeslice_in_daytype` `({timeslice:day_type})`: OSeMOSYS Conversionld.
Optional, constructed if not provided.

`timeslice_in_season` `({timeslice:season})`: OSeMOSYS Conversionls.
Optional, constructed if not provided.

`adj` `({str:dict})`: Parameter to manually define adjanecy for `years`, `seasons`,
`day_types`, `daily_time_brackets`, and `timeslices`. Optional, if not providing values for
`adj`, it is assumed that the other variables are provided in order from first to last.

## Examples

Examples are given below of how a TimeDefinition object might be created using the different
pathways.

### Pathway 1 - Construction from years only

```python
from tz.osemosys.schemas.time_definition import TimeDefinition

basic_time_definition = dict(
    id="pathway_1",
    years=[2021, 2022, 2023],
)

TimeDefinition(**basic_time_definition)
```

### Pathway 2 - Construction from parts

```python
from tz.osemosys.schemas.time_definition import TimeDefinition

basic_time_definition = dict(
    id="pathway_2",
    years=range(2020, 2051),
    seasons=["winter", "summer"],
    daily_time_brackets=["morning", "day", "evening", "night"],
)

TimeDefinition(**basic_time_definition)
```

### Pathway 3 - Construction from timeslices

```python
from tz.osemosys.schemas.time_definition import TimeDefinition

basic_time_definition = dict(
    id="pathway_3",
    years=range(2020, 2051),
    timeslices=["A", "B", "C", "D"],
    adj={
        "years": dict(zip(range(2020, 2050), range(2021, 2051))),
        "timeslices": dict(zip(["A", "B", "C"], ["B", "C", "D"])),
    },
)

TimeDefinition(**basic_time_definition)
```
# **COMMODITY**

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

`include_in_joint_reserve_margin` `({region:{year:bool}})` - OSeMOSYS
ReserveMarginTagFuel. Boolean tagging the commodities that can contribute to reaching the
    indicated reserve margin. It has value True for the commodities contributing, False otherwise.
    Optional, defaults to `None`.



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
# **IMPACT**

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
# **STORAGE**

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

`storage_balance_day` `({region:bool})` - OSeMOSYS style name StorageBalanceDay.
Boolean parameter tagging storage technologies which must balance daily, i.e. charge must equal
    discharge over each day, using daily time brackets.
Optional, defaults to `False`.

`storage_balance_year` `({region:bool})` - OSeMOSYS style name StorageBalanceYear.
Boolean parameter tagging storage technologies which must balance anually, i.e. charge must
equal discharge over each year.
Optional, defaults to `False`.


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
# **TRADE**

The Trade class contains all data related to trade routes (OSeMOSYS 'TradeRoute'). One Trade
instance is given for each commodity (OSeMOSYS 'FUEL') that can be traded. The Trade class
contains parameters additional to those found in base OSeMOSYS related to trade. These are based
on the new parameters introduced in the below paper:

https://www.sciencedirect.com/science/article/abs/pii/S0360544224000021

These new parameters allow trade to be modelled in a way which is more similar to technologies,
with capacities, capital costs, and maximum allowable investments.

## Parameters

`id` `(str)` - Used to describe the type of trade, e.g. electricity transmission, LNG trade.
Required parameter.

`commodity` `(str)` - The commodity which can be traded. Must match the commodities in the
commodities classes. Required parameter.

`trade_routes` `({region:{region:{year:bool}}})` - Boolean linking the regions which may trade
the given commodity. By default is a unidirectional link, so that the link must be specified in
both directions to allow bilateral trade. Required parameter, defaults to False for links not
specified.

`trade_loss` `({region:{region:{year:float}}})` - Percentage of a commodity which is lost when
traded between regions (given as a decimal). Optional, defaults to 0.

`residual_capacity` `({region:{region:{year:float}}})` - Residual trade capacity, given in
capacity units. Note that any residual capacities will only work unidirectionally. Optional,
defaults to 0.

`capex` `({region:{region:{year:float}}})` - Overnight investment cost per trade capacity unit.
Optional, defaults to 0.00001.

`capacity_additional_max` `({region:{region:{year:float}}})` - Maximum capacity investment of
the given trade route. Optional, defaults to `None`.

`operating_life` `({region:{region:{year:int}}})` - Integer value of operating life in years
for the given trade route. Optional, defaults to 1.

`cost_of_capital` `({region:region})` - Cost of capital (discount rate) for investments in the
given trade route. Optional, defaults to 0.1.

`capacity_activity_unit_ratio` `({region:float})` - OSeMOSYS style TradeCapacityToActivityUnit.
Conversion factor relating the energy that would be traded when one unit of capacity is
fully used in one year. Optional, defaults to 1.

`construct_region_pairs` `(bool)` - Boolean parameter which, is set as True, will take the given
    input data and duplicate it for the opposite region:region direction if not already provided.
    E.g. providing trade_routes = {"R1": {"R2": {"COMMODITY": {"2020": True}}}} and setting the
    construct_region_pairs parameter to True will then construct trade_routes as:
    trade_routes = {
                "R1": {"R2": {"COMMODITY": {"2020": True}}},
                "R2": {"R1": {"COMMODITY": {"2020": True}}},
                }


## Examples

A simple example of a trade route for commodity 'electricity' is shown below. It includes 2
regions, with electricity being marked as tradable in either direction between the 2 using the
construct_region_pairs parameter:

```python
from tz.osemosys.schemas.trade import Trade

basic_trade = dict(
    id="electricity trade",
    commodity="electricity",
    trade_routes={"R1": {"R2": {"*": True}}},
    capex={"R1": {"R2": {"*": 100}}},
    operating_life={"R1": {"R2": {"*": 5}}},
    trade_loss={"R1": {"R2": {"*": 0.1}}},
    construct_region_pairs=True,
)

Trade(**basic_trade)
```
