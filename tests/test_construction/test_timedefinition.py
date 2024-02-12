import pytest

from feo.osemosys.schemas.time_definition import TimeDefinition

PASSING_TIME_DEFINITIONS = dict(
    # nameplate params inherited from key
    years_only=dict(years=range(2020, 2050)),
)

# FAILING_TIME_DEFINITIONS
# TODO


@pytest.mark.skip()
def test_timedefinition_construction():
    for name, params in PASSING_TIME_DEFINITIONS.items():
        td = TimeDefinition(id=name, **params)
        assert isinstance(td, TimeDefinition)
