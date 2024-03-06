import warnings
from copy import deepcopy
from typing import Any, List

from pydantic import Field, model_validator

from feo.osemosys.defaults import defaults
from feo.osemosys.schemas.base import OSeMOSYSBase, OSeMOSYSData, cast_osemosysdata_value
from feo.osemosys.schemas.commodity import Commodity
from feo.osemosys.schemas.compat.model import RunSpecOtoole
from feo.osemosys.schemas.impact import Impact
from feo.osemosys.schemas.region import Region
from feo.osemosys.schemas.technology import Technology
from feo.osemosys.schemas.time_definition import TimeDefinition

# filter this pandas-3 dep warning for now
warnings.filterwarnings("ignore", "\nPyarrow", DeprecationWarning)


class RunSpec(OSeMOSYSBase, RunSpecOtoole):
    # COMPONENTS
    # ----------
    time_definition: TimeDefinition
    regions: List[Region]
    commodities: List[Commodity]
    impacts: List[Impact]
    technologies: List[Technology]  # just production technologies for now
    storage_technologies: List[Technology] | None = Field(default=None)  # TODO for now
    # production_technologies: List[ProductionTechnology] | None = Field(default=None)
    # transmission_technologies: List[TechnologyTransmission] | None = Field(default=None)

    # ASSUMPIONS
    # ----------
    depreciation_method: OSeMOSYSData.R.DM | None = Field(
        OSeMOSYSData.R.DM(defaults.depreciation_method)
    )
    # DiscountRateIdv
    cost_of_capital: OSeMOSYSData.RT | None = Field(None)
    discount_rate: OSeMOSYSData.R | None = Field(OSeMOSYSData.RT(defaults.discount_rate))
    reserve_margin: OSeMOSYSData.RY | None = Field(OSeMOSYSData.RY(defaults.reserve_margin))

    # TARGETS
    # -------
    renewable_production_target: OSeMOSYSData.RY | None = Field(None)

    def maybe_mixin_discount_rate(self, regions, technologies, **sets):
        if self.cost_of_capital is None:
            # if cost_of_capital is not provided, use discount_rate
            return deepcopy(self.discount_rate)
        else:
            # cost-of-capital exists but we may need to mixin
            if isinstance(self.cost_of_capital.data, float):
                # if cost_of_capital is a float, return it, it'll cast on composition
                return self.cost_of_capital
            elif isinstance(self.cost_of_capital.data, dict):
                # first compose to fill any wild vals

                # then mix back in the discount rate or default val
                # jsut for now do this
                return 1

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

        self.commodities = [commodity.compose(**sets) for commodity in self.commodities]
        self.regions = [region.compose(**sets) for region in self.regions]
        self.technologies = [technology.compose(**sets) for technology in self.technologies]
        self.impacts = [impact.compose(**sets) for impact in self.impacts]

        # compose own parameters
        if self.depreciation_method:
            self.depreciation_method = OSeMOSYSData.R.DM(
                self.depreciation_method.compose(self.id, self.depreciation_method.data, **sets)
            )
        if self.discount_rate:
            self.discount_rate = OSeMOSYSData.R(
                self.discount_rate.compose(self.id, self.discount_rate.data, **sets)
            )
        if self.reserve_margin:
            self.reserve_margin = OSeMOSYSData.RY(
                self.reserve_margin.compose(self.id, self.reserve_margin.data, **sets)
            )
        if self.renewable_production_target:
            self.renewable_production_target = OSeMOSYSData.RY(
                self.renewable_production_target.compose(
                    self.id, self.renewable_production_target.data, **sets
                )
            )

        self.cost_of_capital = self.maybe_mixin_discount_rate()

        self.cost_of_capital = OSeMOSYSData.RT(
            self.cost_of_capital.compose(self.id, self.cost_of_capital.data, **sets)
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
