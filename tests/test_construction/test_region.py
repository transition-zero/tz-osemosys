import pytest

from tz.osemosys.schemas.region import Region

PASSING_REGION_DEFINITIONS = dict(
    super_basic=dict(id="GB"),
)

FAILING_REGION_DEFINITIONS = dict()


def test_region_construction():
    for _name, params in PASSING_REGION_DEFINITIONS.items():
        region = Region(**params)
        assert isinstance(region, Region)


def test_region_construction_failcases():
    for _name, params in FAILING_REGION_DEFINITIONS.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            Region(**params)
