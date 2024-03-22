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
    # Impact

    The Impact class contains all data related to impacts, i.e. externalities (OSeMOSYS 'EMISSION'),
    including constraints, exogenous impacts, and penalties. One Impact instance is given for each
    impact.

    ## Parameters

    `id` `(str)`: Used to represent the impact name.

    `constraint_annual` `({region:{year:float}})` - OSeMOSYS AnnualEmissionLimit.
      Annual impact constraint. Optional, defaults to `None`.

    `constraint_total` `({region:float})` - OSeMOSYS ModelPeriodEmissionLimit.
      Total modelling period impact constraint. Optional, defaults to `None`.

    `exogenous_annual` `({region:{year:float}})` - OSeMOSYS AnnualExogenousEmission.
      Annual exogenous impact. Optional, defaults to `None`.

    `exogenous_total` `({region:float})` - OSeMOSYS ModelPeriodExogenousEmission.
      Total modelling period exogenous impact. Optional, defaults to `None`.

    `penalty` `({region:{year:float}})` - OSeMOSYS EmissionsPenalty.
      Financial penalty for each unit impact. Optional, defaults to `None`.


    ## Examples

    A simple example of how an impact might be defined is given
    below, along with how it can be used to create an instance of the Impact class:

    ```python
    from tz.osemosys.schemas.impact import Impact

    basic_impact = dict(
        id="CO2e",
        constraint_annual={"R1": {"2020": 2.0, "2021": 2.0, "2022": 2.0}},
        constraint_total={"R1": 5.0},
        exogenous_annual={"R1": {"2020": 1.0, "2021": 1.0, "2022": 1.0}},
        exogenous_total={"R1": 1.0},
        penalty={"R1": {"2020": 1.0, "2021": 1.0, "2022": 1.0}},
    )

    Impact(**basic_impact)
    ```

    This model can be expressed more simply using the wildcard `*` for dimensions over which data is
    repeated:

    ```python
    basic_impact = dict(
        id="CO2e",
        constraint_annual={"R1": {"*": 2.0}},
        constraint_total={"R1": 5.0},
        exogenous_annual={"R1": {"*": 1.0}},
        exogenous_total={"R1": 1.0},
        penalty={"R1": {"*": 1.0}},
    )
    ```

    ## Validation

    `validate_exogenous_lt_constraint` - This enforces that if `exogenous_annual` should be lower
    than `constraint_annual`, and `exogenous_total` should be lower than `constraint_total`, for
    the relevant regions and years.
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
