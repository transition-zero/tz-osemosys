from typing import Any

from pydantic import ConfigDict, Field, conlist, field_serializer, model_validator

from tz.osemosys.defaults import defaults
from tz.osemosys.schemas.base import OSeMOSYSBase, OSeMOSYSData, cast_osemosysdata_value
from tz.osemosys.schemas.compat.technology import OtooleTechnology
from tz.osemosys.schemas.validation.validation_utils import check_min_vals_lower_max


class OperatingMode(OSeMOSYSBase):
    """
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
    Rate of commodity output from a technology, as a ratio of the rate of activity. By convention
    this usually takes a value of 1.0 for technologies producing a commodity, and efficiency is
    added to the model via input_activity_ratio. Optional, defaults to `None`.

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
    """

    @field_serializer
    def osemosysdata_serializer(cls, value: Any, serializer_field):
        if isinstance(value, serializer_field.type_):
            return value.data
        else:
            return value

    model_config = ConfigDict(extra="forbid")

    opex_variable: OSeMOSYSData.RY | None = Field(
        OSeMOSYSData.RY(defaults.technology_opex_variable_cost)
    )
    emission_activity_ratio: OSeMOSYSData.RIY | None = Field(
        None, serializer=osemosysdata_serializer
    )
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
    # Technology

    The Technology class contains data related to technologies and operating modes.
    One Technology instance is given for each technology.

    One parameter of the Technology class is the OperatingMode subclass, which contains all
    technology data which has an operating mode associated with it.

    ## Parameters

    `id` `(str)` - Used to represent the technology name.

    `operating_modes` `(List[OperatingMode])` - A list containing one OperatingMode object for each
    operating mode relevant to the current technology. Each OperatingMode object contains data
    relevant for the corresponding operating mode, ie.e. input/output/emission activity ratios,
    variable costs, tag linking the technology to storage. See the OperatingMode documentation for
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

    `capacity_additional_max_growth_rate` `({region:float})` - New parameter, OSeMOSYS style name
    CapacityAdditionalMaxGrowthRate. Maximum allowed percentage growth in the given technology's
    capacity year on year, expressed as a decimal (e.g. 0.2 for 20%). Optional, defaults to `None`.

    `capacity_additional_max_floor` `({region:float})` - New parameter, OSeMOSYS style name
    CapacityAdditionalMaxFloor. Maximum allowed growth in the given technology's capacity year on
    year, expressed in capacity units. If used in conjunction with
    capacity_additional_max_growth_rate it limits capacity growth to whichever is greater.
    Optional, defaults to `None`.

    `capacity_additional_min` `({region:{year:float}})` - OSeMOSYS TotalAnnualMinCapacityInvestment.
    Minimum capacity investment of a technology, expressed in power units. Optional, defaults to
    `None`.

    `capacity_additional_min_growth_rate` `({region:float})` - New parameter, OSeMOSYS style name
    CapacityAdditionalMinGrowthRate. Minimum allowed percentage growth in the given technology's
    capacity year on year, expressed as a decimal (e.g. 0.2 for 20%). Optional, defaults to `None`.

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
                output_activity_ratio={"electricity": 1.0},
                emission_activity_ratio={
                    "CO2": 0.354 * 8760 / 1000  # Mtco2/TWh * 8760GWh/Gw/yr /1000 GWh/TWh
                },
            )
        ],
    )

    Technology(**basic_technology)
    ```
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
    include_in_joint_renewable_target: OSeMOSYSData.RY.Bool | None = Field(None)

    # NON-REQUIRED CONSTRAINTS
    # -----
    # gross capacity max/min in each year
    capacity_gross_max: OSeMOSYSData.RY | None = Field(None)
    capacity_gross_min: OSeMOSYSData.RY | None = Field(None)

    # additional capacity upper bounds
    capacity_additional_max: OSeMOSYSData.RY | None = Field(None)
    capacity_additional_max_growth_rate: OSeMOSYSData.R | None = Field(None)
    # upper bound floor: if used with growth_rate,
    # limits capacity growth to the floor or growth-rate, whichever is greater
    capacity_additional_max_floor: OSeMOSYSData.R | None = Field(None)

    # additional capacity lower bounds (MUST build)
    capacity_additional_min: OSeMOSYSData.RY | None = Field(None)
    capacity_additional_min_growth_rate: OSeMOSYSData.R | None = Field(None)

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
