from typing import Any

from pydantic import Field, field_validator, model_validator

from feo.osemosys.schemas.base import OSeMOSYSBase, OSeMOSYSData
from feo.osemosys.schemas.compat.impact import OtooleImpact
from feo.osemosys.schemas.validation.impact_validation import (
    exogenous_annual_within_constraint,
    exogenous_total_within_constraint,
)
from feo.osemosys.utils import isnumeric


class Impact(OSeMOSYSBase, OtooleImpact):
    """
    Class to contain all information pertaining to emissions restrictions and penalties
    (independant of technology).
    """

    # Annual emissions constraint per region, year, and emission type
    constraint_annual: OSeMOSYSData | None = Field(None)
    # Total modelled period emissions constraint per region and emission type
    constraint_total: OSeMOSYSData | None = Field(None)
    # Annual exogenous emission per region, year, and emission type
    # I.e. emissions from non-modelled sources
    exogenous_annual: OSeMOSYSData | None = Field(None)
    # Total modelled period exogenous emission per region and emission type
    # I.e. emissions from non-modelled sources
    exogenous_total: OSeMOSYSData | None = Field(None)
    # Financial penalty for each unit of eimssion per region, year, and emission type
    # E.g. used to model carbon prices
    penalty: OSeMOSYSData | None = Field(None)

    @field_validator("*", mode="before")
    @classmethod
    def passthrough_float(cls, v: Any) -> OSeMOSYSData:
        if isnumeric(v):
            return OSeMOSYSData(float(v))
        return v

    @model_validator(mode="after")
    def validate_exogenous_lt_constraint(self):
        if self.constraint_annual is not None and self.exogenous_annual is not None:
            exogenous_annual_within_constraint(self.constraint_annual, self.exogenous_annual)
        if self.constraint_total is not None and self.exogenous_total is not None:
            exogenous_total_within_constraint(self.constraint_total, self.exogenous_total)
        return self
