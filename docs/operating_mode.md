# OperatingMode

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
