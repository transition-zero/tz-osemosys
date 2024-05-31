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
    cost_of_capital: OSeMOSYSData.RRC = Field(OSeMOSYSData.RRC(defaults.discount_rate))

    @model_validator(mode="before")
    @classmethod
    def cast_values(cls, values: Any) -> Any:
        for field, info in cls.model_fields.items():
            field_val = values.get(field)

            if field_val is not None:
                values[field] = cast_osemosysdata_value(field_val, info)

        return values

    def construct_region_pairs(self, param):
        """
        This function constructs region pairs if one direction is defined but not the opposite.

        e.g. trade_routes = {"R1": {"R2": {"COMMODITY": {"2020": True}}}} requires the opposite
        direction to also be defined.
        i.e. trade_routes = {
                            "R1": {"R2": {"COMMODITY": {"2020": True}}},
                            "R2": {"R1": {"COMMODITY": {"2020": True}}},
                            }

        This construction must be done after composing/broadcasting
        """

        for region in param.data.keys():
            for linked_region in param.data[region].keys():
                # linked region not defined at all eg:
                # trade_routes={"R1": {"R2": {"COMMODITY": {"2020": True}}}}
                if linked_region not in param.data.keys():
                    param.data = {
                        **param.data,
                        **{linked_region: {region: param.data[region][linked_region]}},
                    }
                # linked region defined but not with matching link to first region eg:
                # trade_routes={"R1": {"R2": {"COMMODITY": {"2020": True}}},
                #               "R2": {"R3": {"COMMODITY": {"2020": True}}}}
                elif linked_region in param.data.keys():
                    if region not in param.data[linked_region].keys():
                        param.data = {
                            **param.data,
                            **{
                                linked_region: {
                                    **param.data[linked_region],
                                    **{region: param.data[region][linked_region]},
                                }
                            },
                        }

        return self

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

        # Construct region pairs where required
        if self.trade_routes is not None:
            self.construct_region_pairs(self.trade_routes)

        if self.trade_loss is not None:
            self.construct_region_pairs(self.trade_loss)

        if self.residual_capacity is not None:
            self.construct_region_pairs(self.residual_capacity)

        if self.capex is not None:
            self.construct_region_pairs(self.capex)

        if self.capacity_additional_max is not None:
            self.construct_region_pairs(self.capacity_additional_max)

        if self.operational_life is not None:
            self.construct_region_pairs(self.operational_life)

        if self.cost_of_capital is not None:
            self.construct_region_pairs(self.cost_of_capital)

        return self
