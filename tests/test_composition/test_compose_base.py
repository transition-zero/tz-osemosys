import pytest

from feo.osemosys.schemas.commodity import Commodity
from feo.osemosys.schemas.technology import Technology
from feo.osemosys.utils import recursive_keys

PASSING_COMMODITIES = dict(
    most_basic=dict(
        params=dict(
            id="coal",
            demand_annual=5,
            demand_profile={"*": {"0h": 0.0, "6h": 0.2, "12h": 0.3, "18h": 0.5}},
        ),
        sets=dict(
            regions=["R1", "R2"],
            years=[2025, 2026, 2027],
            timeslices=["0h", "6h", "12h", "18h"],
        ),
    )
)

PASSING_TECHNOLOGIES = dict(
    # most_basic=dict(
    #     params=dict(
    #         id="most_basic",
    #         operating_life=10,
    #         capex=15,
    #         opex_fixed=1.5,
    #         operating_modes=[dict(
    # id="mode_1",
    # opex_variable=1.5,
    # input_activity_ratio={"COAL": 1.0})],
    #     ),
    #     sets=dict(
    #         regions=["R1", "R2"],
    #         years=[2025, 2026, 2027],
    #         timeslices=["0h", "6h", "12h", "18h"],
    #         commodities=["COAL"],
    #     ),
    # )
)
PASSING_REGIONS = dict()

PASSING_IMPACTS = dict()
PASSING_MODELS = dict()


FAILING_COMMODITIES = dict(
    non_matching_timeslices=dict(
        params=dict(
            id="coal",
            demand_annual=5,
            demand_profile={"*": {"0h": 0.0, "6h": 0.2, "12h": 0.3, "18h": 0.5}},
        ),
        sets=dict(
            regions=["R1", "R2"],
            years=[2025, 2026, 2027],
            timeslices=["0h", "6h", "12h", "19h"],
        ),
    ),
    too_deep_nesting=dict(
        params=dict(
            id="coal",
            demand_annual={"*": {"*": {"*": 5}}},
            demand_profile={"*": {"0h": 0.0, "6h": 0.2, "12h": 0.3, "18h": 0.5}},
        ),
        sets=dict(
            regions=["R1", "R2"],
            years=[2025, 2026, 2027],
            timeslices=["0h", "6h", "12h", "18"],
        ),
    ),
)


def test_compose_commodity():
    for _name, data in PASSING_COMMODITIES.items():
        commodity = Commodity(**data["params"])
        commodity.compose(**data["sets"])

        demand_annual_keys = [k for k in recursive_keys(commodity.demand_annual.data)]
        for region in data["sets"]["regions"]:
            assert region in [k[0] for k in demand_annual_keys]
        for year in data["sets"]["years"]:
            assert str(year) in [k[1] for k in demand_annual_keys]


def test_compose_technology():
    for _name, data in PASSING_TECHNOLOGIES.items():
        tech = Technology(**data["params"])
        tech.compose(**data["sets"])

        # check one param
        demand_annual_keys = [k for k in recursive_keys(tech.demand_annual.data)]
        for region in data["sets"]["regions"]:
            assert region in [k[0] for k in demand_annual_keys]
        for year in data["sets"]["years"]:
            assert str(year) in [k[1] for k in demand_annual_keys]

        # check the operating mode


def test_failing_commodity():
    for _name, data in FAILING_COMMODITIES.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            commodity = Commodity(**data["params"])
            commodity.compose(**data["sets"])
