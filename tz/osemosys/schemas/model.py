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
from tz.osemosys.schemas.validation.model_composition import check_tech_linked_to_storage
from tz.osemosys.utils import merge, recursive_keys

# filter this pandas-3 dep warning for now
warnings.filterwarnings("ignore", "\nPyarrow", DeprecationWarning)


class RunSpec(OSeMOSYSBase, RunSpecOtoole):
    """
    Class containing all data required to run an OSeMOSYS model, spread across subclasses
    """

    # COMPONENTS
    # ----------
    time_definition: TimeDefinition
    regions: List[Region]
    commodities: List[Commodity]
    impacts: List[Impact]
    technologies: List[Technology]  # just production technologies for now
    # production_technologies: List[ProductionTechnology] | None = Field(default=None)
    # transmission_technologies: List[TechnologyTransmission] | None = Field(default=None)
    storage: List[Storage] | None = Field(None)

    # ASSUMPIONS
    # ----------
    depreciation_method: OSeMOSYSData.R.DM = Field(OSeMOSYSData.R.DM(defaults.depreciation_method))
    # DiscountRateIdv
    cost_of_capital: OSeMOSYSData.RT | None = Field(None)
    discount_rate: OSeMOSYSData.R = Field(OSeMOSYSData.R(defaults.discount_rate))
    reserve_margin: OSeMOSYSData.RY = Field(OSeMOSYSData.RY(defaults.reserve_margin))

    # TARGETS
    # -------
    renewable_production_target: OSeMOSYSData.RY | None = Field(None)

    def maybe_mixin_discount_rate(self):
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

        self.cost_of_capital = self.maybe_mixin_discount_rate()

        self.cost_of_capital = self.cost_of_capital.compose(
            self.id, self.cost_of_capital.data, **sets
        )

        return self

    @model_validator(mode="after")
    def composition_validation(self):
        # self = check_tech_producing_commodity(self)
        # self = check_tech_producing_impact(self)
        # self = check_tech_consuming_commodity(self)
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
