# Technology

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

`capacity_one_tech_unit` `({region:{year:float}})` - OSeMOSYS CapacityOfOneTechnologyUnit.
Capacity of one new unit of a technology. In case the user sets this parameter, the related
technology will be installed only in batches of the specified capacity and the problem will
turn into a Mixed Integer Linear Problem. Optional, defaults to `None`.

`include_in_joint_renewable_target` `({region:{year:bool}})` - OSeMOSYS RETagTechnology.
Boolean tagging the renewable technologies that must contribute to reaching the indicated
minimum renewable production target. It has value True for thetechnologies contributing,
False otherwise. Optional, defaults to `None`.

`capacity_gross_max` `({region:{year:float}})` - OSeMOSYS TotalAnnualMaxCapacity.
Total maximum existing (residual plus cumulatively installed) capacity allowed for a technology
in a specified year. Optional, defaults to `None`.

`capacity_gross_min` `({region:{year:float}})` - OSeMOSYS TotalAnnualMinCapacity.
Total minimum existing (residual plus cumulatively installed) capacity allowed for a technology
in a specified year. Optional, defaults to `None`.

`capacity_additional_max` `({region:{year:float}})` - OSeMOSYS TotalAnnualMaxCapacityInvestment.
Maximum capacity investment of a technology, expressed in power units. Optional, defaults to
`None`.

`capacity_additional_max_growth_rate` `({region:float})` - New parameter, OSeMOSYS style name CapacityAdditionalMaxGrowthRate. Maximum allowed percentage growth in the given technology's capacity year on year, expressed as a decimal (e.g. 0.2 for 20%). Optional, defaults to `None`.

`capacity_additional_max_floor` `({region:float})` - New parameter, OSeMOSYS style name CapacityAdditionalMaxFloor. Maximum allowed growth in the given technology's capacity year on year, expressed in capacity units. If used in conjunction with capacity_additional_max_growth_rate it limits capacity growth to whichever is greater. Optional, defaults to `None`.

`capacity_additional_min` `({region:{year:float}})` - OSeMOSYS TotalAnnualMinCapacityInvestment.
Minimum capacity investment of a technology, expressed in power units. Optional, defaults to
`None`.

`capacity_additional_min_growth_rate` `({region:float})` - New parameter, OSeMOSYS style name CapacityAdditionalMinGrowthRate. Minimum allowed percentage growth in the given technology's capacity year on year, expressed as a decimal (e.g. 0.2 for 20%). Optional, defaults to `None`.

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
