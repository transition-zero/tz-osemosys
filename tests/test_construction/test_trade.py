import pytest

from tz.osemosys.schemas.trade import Trade

PASSING_TRADE_DEFINITIONS = dict(
    basic=dict(
        id="electricity trade",
        commodity="electricity",
        trade_routes={"R1": {"R2": {"*": True}}},
        capex={"R1": {"R2": {"*": 100}}},
        operational_life={"R1": {"R2": {"*": 2}}},
        trade_loss={"*": {"*": {"*": 0.1}}},
        residual_capacity={"R1": {"R2": {"*": 5}}},
        capacity_additional_max={"R1": {"R2": {"*": 5}}},
        cost_of_capital={"R1": {"R2": 0.1}},
        construct_region_pairs=True,
    ),
)

FAILING_TRADE_DEFINITIONS = dict(
    # The relevant commodity must be provided
    no_commodity=dict(
        id="electricity trade",
        trade_routes={"R1": {"R2": {"*": True}}, "R2": {"R1": {"*": False}}},
        capex={"R1": {"R2": {"*": 100}}},
        operational_life={"R1": {"R2": {"*": 2}}},
        trade_loss={"*": {"*": {"*": 0.1}}},
        residual_capacity={"R1": {"R2": {"*": 5}}},
        capacity_additional_max={"R1": {"R2": {"*": 5}}},
        cost_of_capital={"R1": {"R2": 0.1}},
        construct_region_pairs=True,
    ),
)


def test_trade_construction():
    for _name, params in PASSING_TRADE_DEFINITIONS.items():
        trade = Trade(**params)
        assert isinstance(trade, Trade)


def test_trade_construction_failcases():
    for _name, params in FAILING_TRADE_DEFINITIONS.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            Trade(**params)
