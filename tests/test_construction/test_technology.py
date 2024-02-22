import pytest

from feo.osemosys.schemas.technology import Technology, TechnologyStorage

PASSING_TECH_DEFINITIONS = dict(
    most_basic=dict(
        id="most_basic",
        operating_life=10,
        capex=15,
        opex_fixed=1.5,
        operating_modes=[dict(id="mode_1")],
    )
)

FAILING_TECH_DEFINITIONS = dict(
    capacity_min_gt_max=dict(
        id="capacity_min_gt_max",
        operating_life=10,
        capex=15,
        opex_fixed=1.5,
        operating_modes=[dict(id="mode_1")],
        capacity_gross_min=2,
        capacity_gross_max=1,
    ),
    capacity_additional_min_gt_max=dict(
        id="capacity_additional_min_gt_max",
        operating_life=10,
        capex=15,
        opex_fixed=1.5,
        operating_modes=[dict(id="mode_1")],
        capacity_additional_min=2,
        capacity_additional_max=1,
    ),
    activity_min_gt_max=dict(
        id="activity_min_gt_max",
        operating_life=10,
        capex=15,
        opex_fixed=1.5,
        operating_modes=[dict(id="mode_1")],
        activity_annual_min=2,
        activity_annual_max=1,
    ),
    activity_total_min_gt_max=dict(
        id="activity_total_min_gt_max",
        operating_life=10,
        capex=15,
        opex_fixed=1.5,
        operating_modes=[dict(id="mode_1")],
        activity_total_min=2,
        activity_total_max=1,
    ),
)

PASSING_TECH_STORAGE_DEFINITIONS = dict()

FAILING_TECH_STORAGE_DEFINITIONS = dict()


def test_tech_construction():
    for _name, params in PASSING_TECH_DEFINITIONS.items():
        technology = Technology(**params)
        assert isinstance(technology, Technology)


def test_tech_construction_failcases():
    for _name, params in FAILING_TECH_DEFINITIONS.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            Technology(**params)


def test_tech_storage_construction():
    for _name, params in PASSING_TECH_STORAGE_DEFINITIONS.items():
        technology = TechnologyStorage(**params)
        assert isinstance(technology, TechnologyStorage)


def test_tech_storage_construction_failcases():
    for _name, params in FAILING_TECH_STORAGE_DEFINITIONS.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            TechnologyStorage(**params)
