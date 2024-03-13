import pytest

from tz.osemosys.schemas.commodity import Commodity

PASSING_COMMODITY_DEFINITIONS = dict(
    super_basic_no_demand=dict(id="WATER"),
    super_basic_accumulated_demand=dict(id="COAL", demand_annual=100.0),
    super_basic_demand_profile=dict(id="coal", demand_annual=5, demand_profile=1.0),
    basic_demand_profile=dict(
        id="coal",
        demand_annual=5,
        demand_profile={"*": {"0h": 0.0, "6h": 0.2, "12h": 0.3, "18h": 0.5}},
    ),
)

FAILING_COMMODITY_DEFINITIONS = dict(
    # If demand_profile is defined, demand_annual must also be defined
    demand_profile_no_annual=dict(
        id="coal", demand_profile={"*": {"0h": 0.0, "6h": 0.2, "12h": 0.3, "18h": 0.5}}
    ),
    # Demand profile must sum to one
    demand_profile_equals_one=dict(
        id="coal",
        demand_annual=5,
        demand_profile={"*": {"0h": 0.4, "6h": 0.2, "12h": 0.3, "18h": 0.5}},
    ),
)


def test_commodity_construction():
    for _name, params in PASSING_COMMODITY_DEFINITIONS.items():
        commod = Commodity(**params)
        assert isinstance(commod, Commodity)


def test_commodity_construction_failcases():
    for _name, params in FAILING_COMMODITY_DEFINITIONS.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            Commodity(**params)
