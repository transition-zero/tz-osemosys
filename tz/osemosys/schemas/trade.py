from typing import Any

from pydantic import Field, model_validator

from tz.osemosys.defaults import defaults
from tz.osemosys.schemas.base import OSeMOSYSBase, OSeMOSYSData, cast_osemosysdata_value
from tz.osemosys.schemas.compat.trade import OtooleTrade


class Trade(OSeMOSYSBase, OtooleTrade):
    """
    # Trade


    """

    trade_routes: OSeMOSYSData.RRCY.Bool | None = Field(default=None)
    trade_loss: OSeMOSYSData.RRCY = Field(OSeMOSYSData.RRCY(defaults.trade_loss))
    residual_capacity: OSeMOSYSData.RRCY = Field(
        OSeMOSYSData.RRCY(defaults.trade_residual_capacity)
    )
    capex: OSeMOSYSData.RRCY = Field(OSeMOSYSData.RRCY(defaults.trade_capex))
    capacity_additional_max: OSeMOSYSData.RRCY | None = Field(default=None)
    operational_life: OSeMOSYSData.RRCY.Int = Field(
        OSeMOSYSData.RRCY.Int(defaults.trade_operating_life)
    )

    @model_validator(mode="before")
    @classmethod
    def cast_values(cls, values: Any) -> Any:
        for field, info in cls.model_fields.items():
            field_val = values.get(field)

            if field_val is not None:
                values[field] = cast_osemosysdata_value(field_val, info)

        return values

    def compose(self, **sets):
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
