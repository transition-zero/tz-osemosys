import pytest

from feo.osemosys.schemas.model import RunSpec

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
    )
)

FAILING_RUNSPEC_DEFINITIONS = dict()


def test_tech_construction():
    for name, params in PASSING_RUNSPEC_DEFINITIONS.items():
        spec = RunSpec(id=name, **params)
        assert isinstance(spec, RunSpec)


def test_tech_construction_failcases():
    for _name, params in FAILING_RUNSPEC_DEFINITIONS.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            RunSpec(**params)
