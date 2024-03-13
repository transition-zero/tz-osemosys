from typing import Any

from pydantic import ConfigDict, Field, model_validator

from tz.osemosys.schemas.base import OSeMOSYSBase, OSeMOSYSData, cast_osemosysdata_value
from tz.osemosys.schemas.compat.impact import OtooleImpact
from tz.osemosys.schemas.validation.impact_validation import (
    exogenous_annual_within_constraint,
    exogenous_total_within_constraint,
)


class Impact(OSeMOSYSBase, OtooleImpact):
    """
    Class to contain all information pertaining to Impacts (osemosys 'EMISSION') including:
    - restrictions
    - penalties
    """

    model_config = ConfigDict(extra="forbid")

    # Annual emissions constraint per region, year, and emission type
    constraint_annual: OSeMOSYSData.RY | None = Field(None)
    # Total modelled period emissions constraint per region and emission type
    constraint_total: OSeMOSYSData.R | None = Field(None)
    # Annual exogenous emission per region, year, and emission type
    # I.e. emissions from non-modelled sources
    exogenous_annual: OSeMOSYSData.RY | None = Field(None)
    # Total modelled period exogenous emission per region and emission type
    # I.e. emissions from non-modelled sources
    exogenous_total: OSeMOSYSData.R | None = Field(None)
    # Financial penalty for each unit of eimssion per region, year, and emission type
    # E.g. used to model carbon prices
    penalty: OSeMOSYSData.RY | None = Field(None)

    @model_validator(mode="before")
    @classmethod
    def cast_values(cls, values: Any) -> Any:
        for field, info in cls.model_fields.items():
            field_val = values.get(field)
            if field_val is not None:
                values[field] = cast_osemosysdata_value(field_val, info)

        return values

    @model_validator(mode="after")
    def validate_exogenous_lt_constraint(self):
        if self.constraint_annual is not None and self.exogenous_annual is not None:
            exogenous_annual_within_constraint(
                self.id, self.constraint_annual, self.exogenous_annual
            )
        if self.constraint_total is not None and self.exogenous_total is not None:
            exogenous_total_within_constraint(self.id, self.constraint_total, self.exogenous_total)
        return self

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
