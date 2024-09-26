import json
from tempfile import NamedTemporaryFile

import pytest

from tz.osemosys.schemas.time_definition import TimeDefinition

PASSING_TIME_DEFINITIONS = dict(
    # nameplate params inherited from key
    # Pathway 1
    years_only=dict(years=range(2020, 2051)),
    # Pathway 3
    timeslices_simple=dict(  # just timeslices - no adjacency
        years=range(2020, 2051), timeslices=["A", "B", "C", "D"]
    ),
    # Pathway 3
    timeslices_adjacency=dict(  # just timeslices - simple adjacency
        years=range(2020, 2051),
        timeslices=["A", "B", "C", "D"],
        adj={
            "years": dict(zip(range(2020, 2050), range(2021, 2051))),
            "timeslices": dict(zip(["A", "B", "C"], ["B", "C", "D"])),
        },
    ),
    # Pathway 3
    timeslices_with_parts_for_adj=dict(  # infer adjacency from 'seasons' and 'day_types'
        years=range(2020, 2051),
        timeslices=["A", "B", "C", "D"],
        timeslice_in_season={
            "A": "winter",
            "B": "winter",
            "C": "summer",
            "D": "summer",
        },
        timeslice_in_daytype={
            "A": "weekday",
            "B": "weekend",
            "C": "weekday",
            "D": "weekend",
        },
        seasons=["winter", "summer"],
        day_types=["weekday", "weekend"],
    ),
    # Pathway 2
    yearparts_dayparts_inferred=dict(  # infer timeslices from yearparts and daily_time_brackets
        years=range(2020, 2051),
        seasons=["winter", "summer"],
        daily_time_brackets=["morning", "day", "evening", "night"],
    ),
    # Pathway 2
    yearparts_dayparts_list_of_int=dict(
        years=range(2020, 2051), seasons=[1, 2], daily_time_brackets=[1, 2]
    ),
    # Pathway 2
    yearparts_dayparts_list_of_str=dict(
        years=range(2020, 2051),
        seasons=["winter", "spring", "summer", "autumn"],
        day_types=["weekday", "weekend"],
    ),
    # # Pathway x
    # yearparts_dayparts_int=dict(years=range(2020, 2051), seasons=12, daily_time_brackets=6),
)

FAILING_TIME_DEFINITIONS = dict(
    missing_season_adj=dict(  # some seasons provided - but there's no adjacency
        years=range(2020, 2051),
        timeslices=["A", "B", "C", "D"],
        timeslice_in_season={
            "A": "winter",
            "B": "winter",
            "C": "summer",
            "D": "summer",
        },
    ),
    timeslices_with_seasons=dict(  # adjacency underconstrained - no dayparts etc.
        years=range(2020, 2051),
        timeslices=["A", "B", "C", "D"],
        timeslice_in_season={
            "A": "winter",
            "B": "winter",
            "C": "summer",
            "D": "summer",
        },
        seasons=["winter", "summer"],
    ),
)


def test_timedefinition_construction():
    for name, params in PASSING_TIME_DEFINITIONS.items():
        td = TimeDefinition(id=name, **params)
        assert isinstance(td, TimeDefinition)


def test_timedefinition_construction_failcases():
    for name, params in FAILING_TIME_DEFINITIONS.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            TimeDefinition(id=name, **params)


def test_timedefinition_roundtrip():
    tmp = NamedTemporaryFile()
    for name, params in PASSING_TIME_DEFINITIONS.items():
        td = TimeDefinition(id=name, **params)
        json.dump(td.model_dump(), open(tmp.name, "w"))
        td_recovered = TimeDefinition(**json.load(open(tmp.name)))

        assert td == td_recovered
