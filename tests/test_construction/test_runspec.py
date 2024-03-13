import pytest

from tz.osemosys.schemas.model import RunSpec

PASSING_RUNSPEC_DEFINITIONS = dict(
    most_basic=dict(
        time_definition=dict(id="years-only", years=range(2020, 2051)),
        regions=[dict(id="GB")],
        commodities=[dict(id="WATER")],
        impacts=[dict(id="CO2e")],
        technologies=[
            dict(
                id="most_basic",
                operating_life=10,
                capex=15,
                opex_fixed=1.5,
                operating_modes=[dict(id="mode_1")],
            )
        ],
    ),
    most_basic_with_storage=dict(
        time_definition=dict(id="years-only", years=range(2020, 2051)),
        regions=[dict(id="GB")],
        commodities=[dict(id="WATER")],
        impacts=[dict(id="CO2e")],
        technologies=[
            dict(
                id="most_basic",
                operating_life=10,
                capex=15,
                opex_fixed=1.5,
                operating_modes=[
                    dict(id="mode_1", to_storage={"*": {"STO": 1}}, from_storage={"*": {"STO": 1}})
                ],
            )
        ],
        storage=[
            dict(
                id="STO",
                capex={"*": {"*": 100}},
                operating_life={"*": {"*": 10}},
            )
        ],
    ),
)

FAILING_RUNSPEC_DEFINITIONS = dict(
    missing_time_definition=dict(
        regions=[dict(id="GB")],
        commodities=[dict(id="WATER")],
        impacts=[dict(id="CO2e")],
        technologies=[
            dict(
                id="most_basic",
                operating_life=10,
                capex=15,
                opex_fixed=1.5,
                operating_modes=[dict(id="mode_1")],
            )
        ],
    ),
    missing_regions=dict(
        time_definition=dict(id="years-only", years=range(2020, 2051)),
        commodities=[dict(id="WATER")],
        impacts=[dict(id="CO2e")],
        technologies=[
            dict(
                id="most_basic",
                operating_life=10,
                capex=15,
                opex_fixed=1.5,
                operating_modes=[dict(id="mode_1")],
            )
        ],
    ),
    missing_commodities=dict(
        time_definition=dict(id="years-only", years=range(2020, 2051)),
        regions=[dict(id="GB")],
        impacts=[dict(id="CO2e")],
        technologies=[
            dict(
                id="most_basic",
                operating_life=10,
                capex=15,
                opex_fixed=1.5,
                operating_modes=[dict(id="mode_1")],
            )
        ],
    ),
    missing_impacts=dict(
        time_definition=dict(id="years-only", years=range(2020, 2051)),
        regions=[dict(id="GB")],
        commodities=[dict(id="WATER")],
        technologies=[
            dict(
                id="most_basic",
                operating_life=10,
                capex=15,
                opex_fixed=1.5,
                operating_modes=[dict(id="mode_1")],
            )
        ],
    ),
    missing_technologies=dict(
        time_definition=dict(id="years-only", years=range(2020, 2051)),
        regions=[dict(id="GB")],
        commodities=[dict(id="WATER")],
        impacts=[dict(id="CO2e")],
    ),
    missing_from_storage=dict(
        time_definition=dict(id="years-only", years=range(2020, 2051)),
        regions=[dict(id="GB")],
        commodities=[dict(id="WATER")],
        impacts=[dict(id="CO2e")],
        technologies=[
            dict(
                id="most_basic",
                operating_life=10,
                capex=15,
                opex_fixed=1.5,
                operating_modes=[dict(id="mode_1", to_storage={"*": {"STO": 1}})],
            )
        ],
        storage=[
            dict(
                id="STO",
                capex={"*": {"*": 100}},
                operating_life={"*": {"*": 10}},
            )
        ],
    ),
    missing_to_storage=dict(
        time_definition=dict(id="years-only", years=range(2020, 2051)),
        regions=[dict(id="GB")],
        commodities=[dict(id="WATER")],
        impacts=[dict(id="CO2e")],
        technologies=[
            dict(
                id="most_basic",
                operating_life=10,
                capex=15,
                opex_fixed=1.5,
                operating_modes=[dict(id="mode_1", from_storage={"*": {"STO": 1}})],
            )
        ],
        storage=[
            dict(
                id="STO",
                capex={"*": {"*": 100}},
                operating_life={"*": {"*": 10}},
            )
        ],
    ),
)


def test_tech_construction():
    for name, params in PASSING_RUNSPEC_DEFINITIONS.items():
        spec = RunSpec(id=name, **params)
        assert isinstance(spec, RunSpec)


def test_tech_construction_failcases():
    for name, params in FAILING_RUNSPEC_DEFINITIONS.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            RunSpec(id=name, **params)
