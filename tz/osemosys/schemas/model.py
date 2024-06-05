import warnings
from typing import Any, List

from pydantic import Field, model_validator

from tz.osemosys.defaults import defaults
from tz.osemosys.schemas.base import (
    OSeMOSYSBase,
    OSeMOSYSData,
    _check_set_membership,
    cast_osemosysdata_value,
)
from tz.osemosys.schemas.commodity import Commodity
from tz.osemosys.schemas.compat.model import RunSpecOtoole
from tz.osemosys.schemas.impact import Impact
from tz.osemosys.schemas.region import Region
from tz.osemosys.schemas.storage import Storage
from tz.osemosys.schemas.technology import Technology
from tz.osemosys.schemas.time_definition import TimeDefinition
from tz.osemosys.schemas.trade import Trade
from tz.osemosys.schemas.validation.model_composition import (
    check_tech_consuming_commodity,
    check_tech_linked_to_storage,
    check_tech_producing_commodity,
    check_tech_producing_impact,
)
from tz.osemosys.utils import merge, recursive_keys

# filter this pandas-3 dep warning for now
warnings.filterwarnings("ignore", "\nPyarrow", DeprecationWarning)


class RunSpec(OSeMOSYSBase, RunSpecOtoole):
    """
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
    """

    # COMPONENTS
    # ----------
    time_definition: TimeDefinition
    regions: List[Region]
    commodities: List[Commodity]
    impacts: List[Impact]
    technologies: List[Technology]  # just production technologies for now
    trade: List[Trade] | None = Field(None)
    # production_technologies: List[ProductionTechnology] | None = Field(default=None)
    storage: List[Storage] | None = Field(None)

    # ASSUMPIONS
    # ----------
    depreciation_method: OSeMOSYSData.R.DM = Field(OSeMOSYSData.R.DM(defaults.depreciation_method))
    # DiscountRateIdv
    cost_of_capital: OSeMOSYSData.RT | None = Field(None)
    cost_of_capital_storage: OSeMOSYSData.RO | None = Field(None)
    discount_rate: OSeMOSYSData.R = Field(OSeMOSYSData.R(defaults.discount_rate))
    reserve_margin: OSeMOSYSData.RY = Field(OSeMOSYSData.RY(defaults.reserve_margin))

    # TARGETS
    # -------
    renewable_production_target: OSeMOSYSData.RY | None = Field(None)

    def maybe_mixin_discount_rate_idv(self):
        regions = [region.id for region in self.regions]
        technologies = [technology.id for technology in self.technologies]

        if self.cost_of_capital is None:
            # if cost_of_capital is not provided, use discount_rate
            return OSeMOSYSData.RT(self.discount_rate.data)
        else:
            # cost-of-capital exists but we may need to mixin
            if isinstance(self.cost_of_capital.data, float):
                # if cost_of_capital is a float, return it, it'll cast on composition
                return OSeMOSYSData.RT(self.cost_of_capital.data)
            elif isinstance(self.cost_of_capital.data, dict):
                all_data = {
                    region: {technology: None for technology in technologies} for region in regions
                }

                # first compose to fill any wild vals
                composed_cost_of_capital = _check_set_membership(
                    "cost_of_capital",
                    self.cost_of_capital.data,
                    {"regions": regions, "technologies": technologies},
                )
                all_data = merge(all_data, composed_cost_of_capital)

                # mix back in any discount rates or the default value
                for region, technology in recursive_keys(all_data):
                    if all_data[region][technology] is None:
                        if self.discount_rate.data[region] is not None:
                            all_data[region][technology] = self.discount_rate.data[region]
                        else:
                            all_data[region][technology] = defaults.discount_rate

                return OSeMOSYSData.RT(all_data)

            else:
                raise ValueError(f"Wrong datatype for cost_of_capital: {self.cost_of_capital.data}")

    def maybe_mixin_discount_rate_storage(self):
        regions = [region.id for region in self.regions]
        if self.storage is not None:
            storage_techs = [sto.id for sto in self.storage]

        if self.cost_of_capital_storage is None:
            # if cost_of_capital is not provided, use discount_rate
            return OSeMOSYSData.RO(self.discount_rate.data)
        else:
            # cost-of-capital-storage exists but we may need to mixin
            if isinstance(self.cost_of_capital_storage.data, float):
                # if cost_of_capital is a float, return it, it'll cast on composition
                return OSeMOSYSData.RO(self.cost_of_capital_storage.data)
            elif isinstance(self.cost_of_capital_storage.data, dict):
                all_data = {region: {sto: None for sto in storage_techs} for region in regions}

                # first compose to fill any wild vals
                composed_cost_of_capital_storage = _check_set_membership(
                    "cost_of_capital_storage",
                    self.cost_of_capital_storage.data,
                    {"regions": regions, "storage": storage_techs},
                )
                all_data = merge(all_data, composed_cost_of_capital_storage)

                # mix back in any discount rates or the default value
                for region, sto in recursive_keys(all_data):
                    if all_data[region][sto] is None:
                        if self.discount_rate.data[region] is not None:
                            all_data[region][sto] = self.discount_rate.data[region]
                        else:
                            all_data[region][sto] = defaults.discount_rate

                return OSeMOSYSData.RO(all_data)

            else:
                raise ValueError(
                    f"Wrong datatype for cost_of_capital_storage: "
                    f"{self.cost_of_capital_storage.data}"
                )

    @model_validator(mode="after")
    def compose(self):
        # compose subsidiary objects
        sets = {
            "years": self.time_definition.years,
            "timeslices": self.time_definition.timeslices,
            "commodities": [commodity.id for commodity in self.commodities],
            "regions": [region.id for region in self.regions],
            "technologies": [technology.id for technology in self.technologies],
            "impacts": [impact.id for impact in self.impacts],
        }
        if self.storage:
            sets = {**sets, **{"storage": [storage.id for storage in self.storage]}}

        self.commodities = [commodity.compose(**sets) for commodity in self.commodities]
        self.regions = [region.compose(**sets) for region in self.regions]
        self.technologies = [technology.compose(**sets) for technology in self.technologies]
        self.impacts = [impact.compose(**sets) for impact in self.impacts]
        if self.storage:
            self.storage = [storage.compose(**sets) for storage in self.storage]
        if self.trade:
            self.trade = [trade.compose(**sets) for trade in self.trade]

        # compose own parameters
        if self.depreciation_method:
            self.depreciation_method = self.depreciation_method.compose(
                self.id, self.depreciation_method.data, **sets
            )
        if self.discount_rate:
            self.discount_rate = self.discount_rate.compose(
                self.id, self.discount_rate.data, **sets
            )
        if self.reserve_margin:
            self.reserve_margin = self.reserve_margin.compose(
                self.id, self.reserve_margin.data, **sets
            )
        if self.renewable_production_target:
            self.renewable_production_target = self.renewable_production_target.compose(
                self.id, self.renewable_production_target.data, **sets
            )

        self.cost_of_capital = self.maybe_mixin_discount_rate_idv()
        if self.cost_of_capital:
            self.cost_of_capital = self.cost_of_capital.compose(
                self.id, self.cost_of_capital.data, **sets
            )

        if self.cost_of_capital_storage:
            self.cost_of_capital_storage = self.maybe_mixin_discount_rate_storage()
            self.cost_of_capital_storage = self.cost_of_capital_storage.compose(
                self.id, self.cost_of_capital_storage.data, **sets
            )

        return self

    @model_validator(mode="after")
    def composition_validation(self):
        """
        Do composition checks ensuring all commodities, impacts, and storage are linked to a
        technology
        """
        self = check_tech_producing_commodity(self)
        self = check_tech_producing_impact(self)
        self = check_tech_consuming_commodity(self)
        if self.storage:
            self = check_tech_linked_to_storage(self)
        return self

    @model_validator(mode="before")
    @classmethod
    def cast_values(cls, values: Any) -> Any:
        for field, info in cls.model_fields.items():
            field_val = values.get(field)

            if field_val is not None:
                values[field] = cast_osemosysdata_value(field_val, info)

        return values
