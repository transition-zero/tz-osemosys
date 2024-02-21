import pytest

from feo.osemosys.schemas.impact import Impact

PASSING_IMPACT_DEFINITIONS = dict(
    super_basic_no_constraint=dict(id="CO2e"),
    basic_with_constraint=dict(
        id="CO2e",
        constraint_annual={"*": {"*": 1}},
        constraint_total={"*": 10},
    ),
    penalty_no_constraint=dict(
        id="CO2e",
        penalty={"*": {"*": 5.0}},
    ),
    penalty_with_constraint=dict(
        id="CO2e",
        constraint_annual={"*": {"*": 1}},
        constraint_total={"*": 10},
        penalty={"*": {"*": 5.0}},
    ),
    exogenous_only_with_penalty=dict(
        id="CO2e",
        exogenous_annual={"*": {"*": 1}},
        exogenous_total={"*": 1},
        penalty={"*": {"*": 5.0}},
    ),
)

FAILING_IMPACT_DEFINITIONS = dict(
    exogenous_gt_constraint_ann=dict(
        id="CO2e",
        constraint_annual={"*": {"*": 1}},
        exogenous_annual={"*": {"*": 2}},
    ),
    exogenous_gt_constraint_total=dict(
        id="CO2e",
        constraint_total={"*": 1},
        exogenous_total={"*": 2},
    ),
)


def test_impact_construction():
    for _name, params in PASSING_IMPACT_DEFINITIONS.items():
        impact = Impact(**params)
        assert isinstance(impact, Impact)


def test_impact_construction_failcases():
    for _name, params in FAILING_IMPACT_DEFINITIONS.items():
        print(_name)
        with pytest.raises(ValueError) as e:  # noqa: F841
            Impact(**params)
