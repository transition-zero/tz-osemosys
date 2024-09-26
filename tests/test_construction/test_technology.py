import json
from tempfile import NamedTemporaryFile

import pytest

from tz.osemosys.schemas.technology import Technology

PASSING_TECH_DEFINITIONS = dict(
    most_basic=dict(
        id="most_basic",
        operating_life=10,
        capex=15,
        opex_fixed=1.5,
        operating_modes=[dict(id="mode_1")],
    ),
    with_capex=dict(
        id="with_capex",
        operating_life=10,
        capex={2022: 15, 2023: 20},
        opex_fixed=1.5,
        operating_modes=[dict(id="mode_1")],
    ),
)

FAILING_TECH_DEFINITIONS = dict(
    capacity_min_gt_max=dict(
        id="capacity_min_gt_max",
        operating_life=10,
        capex=15,
        opex_fixed=1.5,
        operating_modes=[dict(id="mode_1")],
        capacity_gross_min=2,
        capacity_gross_max={"GLOBAL": {"2020": 1}},
    ),
    # Technology minimum additional capacity limit must be < maximum additional capacity limit
    capacity_additional_min_gt_max=dict(
        id="capacity_additional_min_gt_max",
        operating_life=10,
        capex=15,
        opex_fixed=1.5,
        operating_modes=[dict(id="mode_1")],
        capacity_additional_min=2,
        capacity_additional_max=1,
    ),
    # Technology minimum annual activity limit must be < maximum annual activity limit
    activity_min_gt_max=dict(
        id="activity_min_gt_max",
        operating_life=10,
        capex=15,
        opex_fixed=1.5,
        operating_modes=[dict(id="mode_1")],
        activity_annual_min=2,
        activity_annual_max=1,
    ),
    # Technology minimum total activity limit must be < maximum total activity limit
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


def test_tech_construction():
    for _name, params in PASSING_TECH_DEFINITIONS.items():
        technology = Technology(**params)
        assert isinstance(technology, Technology)


@pytest.mark.skip(reason="Should only be tested for greater than / less than after composition")
def test_tech_construction_failcases():
    for _name, params in FAILING_TECH_DEFINITIONS.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            Technology(**params)


def test_technology_roundtrip():
    tmp = NamedTemporaryFile()
    for _name, params in PASSING_TECH_DEFINITIONS.items():
        tech = Technology(**params)
        json.dump(tech.model_dump(), open(tmp.name, "w"))
        tech_recovered = Technology(**json.load(open(tmp.name)))
        assert tech == tech_recovered
