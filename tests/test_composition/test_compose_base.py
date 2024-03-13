import pytest

from tz.osemosys.schemas.base import _check_set_membership
from tz.osemosys.schemas.commodity import Commodity
from tz.osemosys.schemas.impact import Impact
from tz.osemosys.schemas.storage import Storage
from tz.osemosys.schemas.technology import Technology
from tz.osemosys.utils import recursive_keys

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
    most_basic=dict(
        params=dict(
            id="most_basic",
            operating_life=10,
            capex=15,
            opex_fixed=1.5,
            operating_modes=[
                dict(id="mode_1", opex_variable=1.5, input_activity_ratio={"COAL": 1.0})
            ],
        ),
        sets=dict(
            regions=["R1", "R2"],
            years=[2025, 2026, 2027],
            timeslices=["0h", "6h", "12h", "18h"],
            commodities=["COAL"],
        ),
    )
)

PASSING_IMPACTS = dict(
    basic_with_constraint=dict(
        params=dict(
            id="CO2e",
            constraint_annual={"*": {"*": 1}},
            constraint_total={"*": 10},
        ),
        sets=dict(
            regions=["R1", "R2"],
            years=[2025, 2026, 2027],
            timeslices=["0h", "6h", "12h", "18h"],
            commodities=["COAL"],
        ),
    )
)

PASSING_STORAGE = dict(
    basic_wildcard=dict(
        params=dict(
            id="STO",
            capex={"*": {"*": 100}},
            operating_life={"*": 10},
        ),
        sets=dict(
            regions=["R1", "R2"],
            years=[2025, 2026, 2027],
        ),
    ),
    basic_explicit=dict(
        params=dict(
            id="STO",
            capex={"R1": {"2025": 100, "2026": 100}, "R2": {"2025": 100, "2026": 100}},
            operating_life={"R1": 10, "R2": 10},
        ),
        sets=dict(
            regions=["R1", "R2"],
            years=[2025, 2026],
        ),
    ),
)

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

FAILING_TECHNOLOGIES = dict(
    non_matching_commodities=dict(
        params=dict(
            id="most_basic",
            operating_life=10,
            capex=15,
            opex_fixed=1.5,
            operating_modes=[
                dict(id="mode_1", opex_variable=1.5, input_activity_ratio={"COAL": 1.0})
            ],
        ),
        sets=dict(
            regions=["R1", "R2"],
            years=[2025, 2026, 2027],
            timeslices=["0h", "6h", "12h", "18h"],
            commodities=["GAS"],
        ),
    )
)

FAILING_IMPACTS = dict(
    too_deep_nesting=dict(
        params=dict(
            id="CO2e",
            constraint_annual={"*": {"*": {"*": 1}}},
            constraint_total={"*": {"*": 10}},
        ),
        sets=dict(
            regions=["R1", "R2"],
            years=[2025, 2026, 2027],
            timeslices=["0h", "6h", "12h", "18h"],
            commodities=["COAL"],
        ),
    )
)

FAILING_STORAGE = dict(
    too_deep_nesting=dict(
        params=dict(
            id="STO",
            capex={"*": {"*": {"*": 100}}},
            operating_life={"*": {"*": 10}},
        ),
        sets=dict(
            regions=["R1", "R2"],
            years=[2025, 2026, 2027],
        ),
    ),
    non_matching_regions=dict(
        params=dict(
            id="STO",
            capex={"R3": {"*": 100}},
            operating_life={"R3": {"*": 10}},
        ),
        sets=dict(
            regions=["R1", "R2"],
            years=[2025, 2026, 2027],
        ),
    ),
)


def test_compose_dim2():
    _id = ("no-id",)
    data = {
        "R1": {"T1": 1},
        "R2": {"*": 2},
        "*": {"T3": 5},
    }
    sets = {
        "regions": ["R1", "R2", "R3"],
        "technologies": ["T1", "T2", "T3"],
    }

    new_data = _check_set_membership(_id, data, sets)

    assert new_data == {"R1": {"T1": 1}, "R2": {"T1": 2, "T2": 2, "T3": 2}, "R3": {"T3": 5}}


def test_compose_dim3():
    _id = ("no-id",)
    data = {
        "R1": {"T1": {"C2": 1, "*": 6}, "*": {"*": 2}},
        "*": {"*": {"C1": 4, "*": 5}},
    }
    sets = {
        "regions": ["R1", "R2"],
        "technologies": ["T1", "T2", "T3"],
        "commodities": ["C1", "C2"],
    }

    new_data = _check_set_membership(_id, data, sets)

    target = {
        "R1": {"T1": {"C1": 6, "C2": 1}, "T2": {"C1": 2, "C2": 2}, "T3": {"C1": 2, "C2": 2}},
        "R2": {"T1": {"C1": 4, "C2": 5}, "T2": {"C1": 4, "C2": 5}, "T3": {"C1": 4, "C2": 5}},
    }

    assert new_data == target


def test_compose_impact():
    for _name, data in PASSING_IMPACTS.items():
        impact = Impact(**data["params"])
        impact.compose(**data["sets"])

        constraint_annual_keys = [k for k in recursive_keys(impact.constraint_annual.data)]
        for region in data["sets"]["regions"]:
            assert region in [k[0] for k in constraint_annual_keys]
        for year in data["sets"]["years"]:
            assert str(year) in [k[1] for k in constraint_annual_keys]


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
        capex = [k for k in recursive_keys(tech.capex.data)]
        for region in data["sets"]["regions"]:
            assert region in [k[0] for k in capex]
        for year in data["sets"]["years"]:
            assert str(year) in [k[1] for k in capex]

        # check the operating mode
        op_mode_1 = tech.operating_modes[0]
        input_activity_ratio = [k for k in recursive_keys(op_mode_1.input_activity_ratio.data)]
        for region in data["sets"]["regions"]:
            assert region in [k[0] for k in input_activity_ratio]
        for commodity in data["sets"]["commodities"]:
            assert commodity in [k[1] for k in input_activity_ratio]
        for year in data["sets"]["years"]:
            assert str(year) in [k[2] for k in input_activity_ratio]


def test_compose_storage():
    for _name, data in PASSING_STORAGE.items():
        storage = Storage(**data["params"])
        storage.compose(**data["sets"])

        capex_keys = [k for k in recursive_keys(storage.capex.data)]
        for region in data["sets"]["regions"]:
            assert region in [k[0] for k in capex_keys]
        for year in data["sets"]["years"]:
            assert str(year) in [k[1] for k in capex_keys]


def test_failing_commodity():
    for _name, data in FAILING_COMMODITIES.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            commodity = Commodity(**data["params"])
            commodity.compose(**data["sets"])


def test_failing_technology():
    for _name, data in FAILING_TECHNOLOGIES.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            technology = Technology(**data["params"])
            technology.compose(**data["sets"])


def test_failing_impact():
    for _name, data in FAILING_IMPACTS.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            impact = Impact(**data["params"])
            impact.compose(**data["sets"])


def test_failing_storage():
    for _name, data in FAILING_STORAGE.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            storage = Storage(**data["params"])
            storage.compose(**data["sets"])
