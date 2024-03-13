import pytest

from tz.osemosys.schemas.storage import Storage

PASSING_TECH_STORAGE_DEFINITIONS = dict(
    only_capex_and_op_life=dict(
        id="STO",
        capex={"*": {"*": 100}},
        operating_life={"*": {"*": 10}},
    ),
    fully_defined=dict(
        id="STO",
        capex={"*": {"*": 100}},
        operating_life={"*": {"*": 10}},
        minimum_charge={"*": {"*": 0}},
        initial_level={"*": 1},
        residual_capacity={"*": {2020: 3, 2021: 2, 2022: 1}},
        max_discharge_rate={"*": 100},
        max_charge_rate={"*": 100},
    ),
)

FAILING_TECH_STORAGE_DEFINITIONS = dict(
    # id must be defined
    no_id=dict(
        capex={"*": {"*": 100}},
        operating_life={"*": {"*": 10}},
    ),
    # capex must be defined
    no_capex=dict(
        id="STO",
        operating_life={"*": {"*": 10}},
    ),
    # operating_life must be defined
    no_op_life=dict(
        id="STO",
        capex={"*": {"*": 100}},
    ),
)


def test_tech_storage_construction():
    for _name, params in PASSING_TECH_STORAGE_DEFINITIONS.items():
        technology = Storage(**params)
        assert isinstance(technology, Storage)


def test_tech_storage_construction_failcases():
    for _name, params in FAILING_TECH_STORAGE_DEFINITIONS.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            Storage(**params)
