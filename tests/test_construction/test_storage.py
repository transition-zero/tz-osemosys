import pytest

from feo.osemosys.schemas.storage import Storage

PASSING_TECH_STORAGE_DEFINITIONS = dict()

FAILING_TECH_STORAGE_DEFINITIONS = dict()


def test_tech_storage_construction():
    for _name, params in PASSING_TECH_STORAGE_DEFINITIONS.items():
        technology = Storage(**params)
        assert isinstance(technology, Storage)


def test_tech_storage_construction_failcases():
    for _name, params in FAILING_TECH_STORAGE_DEFINITIONS.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            Storage(**params)
