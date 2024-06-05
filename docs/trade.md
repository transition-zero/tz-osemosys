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
