import warnings
from typing import Any, List

from pydantic import Field, model_validator

from feo.osemosys.defaults import defaults
from feo.osemosys.schemas.base import (
    OSeMOSYSBase,
    OSeMOSYSData,
    OSeMOSYSData_DepreciationMethod,
    OSeMOSYSData_Int,
)
from feo.osemosys.schemas.commodity import Commodity
from feo.osemosys.schemas.compat.model import RunSpecOtoole
from feo.osemosys.schemas.impact import Impact
from feo.osemosys.schemas.region import Region
from feo.osemosys.schemas.technology import Technology, TechnologyStorage
from feo.osemosys.schemas.time_definition import TimeDefinition
from feo.osemosys.utils import isnumeric

# filter this pandas-3 dep warning for now
warnings.filterwarnings("ignore", "\nPyarrow", DeprecationWarning)


class RunSpec(OSeMOSYSBase, RunSpecOtoole):
    # COMPONENTS
    # ----------
    time_definition: TimeDefinition
    regions: List[Region]
    commodities: List[Commodity]
    impacts: List[Impact]
    technologies: List[Technology]
    storage_technologies: List[TechnologyStorage] | None = Field(None)
    # TODO
    # production_technologies: List[TechnologyProduction]
    # transmission_technologies: List[TechnologyTransmission]

    # ASSUMPIONS
    # ----------
    depreciation_method: OSeMOSYSData_DepreciationMethod | None = Field(
        OSeMOSYSData_DepreciationMethod(defaults.depreciation_method)
    )
    discount_rate: OSeMOSYSData | None = Field(OSeMOSYSData(defaults.discount_rate))
    reserve_margin: OSeMOSYSData | None = Field(OSeMOSYSData(defaults.reserve_margin))

    # TARGETS
    # -------
    renewable_production_target: OSeMOSYSData | None = Field(None)

    @model_validator(mode="before")
    @classmethod
    def cast_values(cls, values: Any) -> Any:
        for field, info in cls.model_fields.items():
            field_val = values.get(field)

            if all(
                [
                    field_val is not None,
                    isinstance(field_val, int),
                    "OSeMOSYSData_Int" in str(info.annotation),
                ]
            ):
                values[field] = OSeMOSYSData_Int(field_val)
            elif all(
                [
                    field_val is not None,
                    isinstance(field_val, str),
                    "OSeMOSYSData_DepreciationMethod" in str(info.annotation),
                ]
            ):
                values[field] = OSeMOSYSData_DepreciationMethod(field_val)
            elif all(
                [
                    field_val is not None,
                    isnumeric(field_val),
                    "OSeMOSYSData" in str(info.annotation),
                ]
            ):
                values[field] = OSeMOSYSData(field_val)

        return values
