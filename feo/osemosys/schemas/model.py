import warnings
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
    # production_technologies: List[ProductionTechnology] | None = Field(default=None)
    # transmission_technologies: List[TechnologyTransmission] | None = Field(default=None)
    # storage_technologies: List[TechnologyStorage] | None = Field(None)

    # ASSUMPIONS
    # ----------
    depreciation_method: OSeMOSYSData.R.DM | None = Field(
        OSeMOSYSData.R.DM(defaults.depreciation_method)
    )
    discount_rate: OSeMOSYSData.RT | None = Field(OSeMOSYSData(defaults.discount_rate))
    reserve_margin: OSeMOSYSData.RY | None = Field(OSeMOSYSData(defaults.reserve_margin))

    # TARGETS
    # -------
    renewable_production_target: OSeMOSYSData.RY | None = Field(None)

    @model_validator(mode="after")
    def compose(self):
        # compose
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

        return self

    @model_validator(mode="before")
    @classmethod
    def cast_values(cls, values: Any) -> Any:
        for field, info in cls.model_fields.items():
            field_val = values.get(field)

            if field_val is not None:
                values[field] = cast_osemosysdata_value(field_val, info)

        return values
