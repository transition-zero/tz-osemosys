from typing import Any

from pydantic import Field, model_validator

from tz.osemosys.defaults import defaults
from tz.osemosys.schemas.base import OSeMOSYSBase, OSeMOSYSData, cast_osemosysdata_value
from tz.osemosys.schemas.compat.trade import OtooleTrade


class Trade(OSeMOSYSBase, OtooleTrade):
    """
    # Trade

    The Trade class contains all data related to trade routes (OSeMOSYS 'TradeRoute'). One Trade
    instance is given for each commodity (OSeMOSYS 'FUEL') that can be traded. The Trade class
    contains parameters additional to those found in base OSeMOSYS related to trade. These are based
     on the new parameters introduced in the below paper:
    https://www.sciencedirect.com/science/article/abs/pii/S0360544224000021

    These new parameters allow trade to be modelled in a way which is more similar to technologies,
    with capacities, capital costs, and maximum allowable investments.

    ## Parameters

    `id` `(str)` - Used to describe the type of trade, e.g. electricity transmission, LNG trade.
    Required parameter.

    `commodity` `(str)` - The commodity which can be traded. Must match the commodities in the
    commodities classes. Required parameter.

    `trade_routes` `({region:{region:{year:bool}}})` - Boolean linking the regions which may trade
    the given commodity. By default is a unidirectional link, so that the link must be specified in
    both directions to allow bilateral trade. Required parameter, defaults to False for links not
    specified.

    `trade_loss` `({region:{region:{year:float}}})` - Percentage of a commodity which is lost when
    traded between regions (given as a decimal). Optional, defaults to 0.

    `residual_capacity` `({region:{region:{year:float}}})` - Residual trade capacity, given in
    capacity units. Note that any residual capacities will only work unidirectionally. Optional,
    defaults to 0.

    `capex` `({region:{region:{year:float}}})` - Overnight investment cost per trade capacity unit.
    Optional, defaults to 0.00001.

    `capacity_additional_max` `({region:{region:{year:float}}})` - Maximum capacity investment of
    the given trade route. Optional, defaults to `None`.

    `operational_life` `({region:{region:{year:int}}})` - Integer value of operating life in years
    for the given trade route. Optional, defaults to 1.

    `cost_of_capital` `({region:region})` - Cost of capital (discount rate) for investments in the
    given trade route. Optional, defaults to 0.1.

    `construct_region_pairs` `(bool)` - Boolean parameter which, is set as True, will take the given
     input data and duplicate it for the opposite region:region direction if not already provided.
     E.g. providing trade_routes = {"R1": {"R2": {"COMMODITY": {"2020": True}}}} and setting the
     construct_region_pairs parameter to True will then construct trade_routes as:
     trade_routes = {
                    "R1": {"R2": {"COMMODITY": {"2020": True}}},
                    "R2": {"R1": {"COMMODITY": {"2020": True}}},
                    }


    ## Examples

    A simple example of a trade route for commodity 'electricity' is shown below. It includes 2
    regions, with electricity being marked as tradable in either direction between the 2 using the
    construct_region_pairs parameter:

    ```python
    from tz.osemosys.schemas.trade import Trade

    basic_trade = dict(
        id="electricity trade",
        commodity="electricity",
        trade_routes={"R1": {"R2": {"*": True}}},
        capex={"R1": {"R2": {"*": 100}}},
        operational_life={"R1": {"R2": {"*": 5}}},
        trade_loss={"R1": {"R2": {"*": 0.1}}},
        construct_region_pairs=True,
    )

    Trade(**basic_trade)
    ```
    """

    commodity: str
    trade_routes: OSeMOSYSData.RRY.Bool = Field(OSeMOSYSData.RRY(defaults.trade_route))
    trade_loss: OSeMOSYSData.RRY | None = Field(OSeMOSYSData.RRY(defaults.trade_loss))
    residual_capacity: OSeMOSYSData.RRY = Field(OSeMOSYSData.RRY(defaults.trade_residual_capacity))
    capex: OSeMOSYSData.RRY = Field(OSeMOSYSData.RRY(defaults.trade_capex))
    capacity_additional_max: OSeMOSYSData.RRY | None = Field(default=None)
    operational_life: OSeMOSYSData.RRY.Int = Field(
        OSeMOSYSData.RRY.Int(defaults.trade_operating_life)
    )
    cost_of_capital: OSeMOSYSData.RR | None = Field(OSeMOSYSData.RR(defaults.discount_rate))
    construct_region_pairs: bool | None = Field(False)

    @model_validator(mode="before")
    @classmethod
    def cast_values(cls, values: Any) -> Any:
        for field, info in cls.model_fields.items():
            field_val = values.get(field)

            if field_val is not None:
                values[field] = cast_osemosysdata_value(field_val, info)

        return values

    def construct_pairs(self, param):
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

        # Check trade commodity matches those in commodity set
        if self.commodity not in sets["commodities"]:
            raise ValueError(
                f"Commodity '{self.commodity}' for trade instance '{self.id}'"
                f" does not match any commodity instance"
            )

        # Construct region pairs if requested where required
        if self.construct_region_pairs:
            if self.trade_routes is not None:
                self.construct_pairs(self.trade_routes)

            if self.trade_loss is not None:
                self.construct_pairs(self.trade_loss)

            if self.residual_capacity is not None:
                self.construct_pairs(self.residual_capacity)

            if self.capex is not None:
                self.construct_pairs(self.capex)

            if self.capacity_additional_max is not None:
                self.construct_pairs(self.capacity_additional_max)

            if self.operational_life is not None:
                self.construct_pairs(self.operational_life)

            if self.cost_of_capital is not None:
                self.construct_pairs(self.cost_of_capital)

        return self
