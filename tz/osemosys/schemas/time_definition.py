from typing import Any, Mapping

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    conlist,
    field_validator,
    model_validator,
)

from tz.osemosys.schemas.base import MappingSumOne, OSeMOSYSBase
from tz.osemosys.schemas.compat.time_definition import OtooleTimeDefinition
from tz.osemosys.schemas.validation.timedefinition_validation import (
    build_adjacency,
    build_timeslices_from_parts,
    get_timeslices_from_sets,
    maybe_get_parts_from_timeslice_mappings,
    timeslice_match_timeslice_in_set,
    validate_adjacency_fullyconstrained,
    validate_adjacency_keys,
    validate_parts_from_splits,
)


class TimeAdjacency(BaseModel):
    years: dict[int, int]
    seasons: dict[str, str] | None = Field(default={})  # default no adjacency
    day_types: dict[str, str] | None = Field(default={})
    time_brackets: dict[str, str] | None = Field(default={})
    timeslices: dict[str, str] | None = Field(default={})

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def from_years(cls, years):
        return cls(years=dict(zip(sorted(years)[:-1], sorted(years)[1:])))

    def inv(self):
        return TimeAdjacency(
            years={v: k for k, v in self.years.items()},
            seasons={v: k for k, v in self.seasons.items()} if self.seasons else None,
            day_types=({v: k for k, v in self.day_types.items()} if self.day_types else None),
            time_brackets=(
                {v: k for k, v in self.time_brackets.items()} if self.time_brackets else None
            ),
            timeslices={v: k for k, v in self.timeslices.items()},
        )


def construction_from_timeslices(values: Any):
    """pathway 3: years plus any of timeslices, timeslice_in_timebracket, timeslice_in_daytype,
    timeslice_in_season with optional year_split, day_split, days_in_day_type
    and optional validation on yearparts, daytypes, and dayparts OR adjacency
    - default to seasons
    - build unitary yearparts, daytypes, and dayparts where not specified
    - validating keys on timeslice data and yearpart etc data
    - option if year_split, day_split, days_in_day_type are specified:
      - use specified data, validating keys
      - else: assume equal year, daytype, and day splitting where not specified
    - if option if yearparts, daytypes, dayparts are specified:
      - validate keys against timeslice data AND assume adjacency from ordered parts where given
      - else:
        - if adjacency is not specified, raise error for required parameter
    """
    years = values.get("years")

    # get timeslices from any of timeslice data
    timeslices = get_timeslices_from_sets(values)

    # validate timeslice keys against timeslice_mappings
    timeslice_match_timeslice_in_set(timeslices, values)

    # get parts from any timeslice_mappings and validate keys
    (
        seasons,
        day_types,
        time_brackets,
        timeslice_in_season,
        timeslice_in_daytype,
        timeslice_in_timebracket,
    ) = maybe_get_parts_from_timeslice_mappings(timeslices, values)

    # validate adjacency or check underconstraint
    # if adjacency is given, validate keys
    adj = values.get("adj")
    if adj is not None:
        validate_adjacency_keys(adj, timeslices, years, seasons, day_types, time_brackets)
    # elif adjacency is not given, check for underconstraint then build adjacency
    else:
        # if only timeslices are given, then assume adjacency from timeslice order
        if all([seasons, day_types, time_brackets]):
            adj = dict(
                years=dict(zip(sorted(years)[:-1], sorted(years)[1:])),
                timeslices=dict(zip(timeslices[:-1], timeslices[1:])),
            )
        else:
            # validate adjacency is fully constrained
            validate_adjacency_fullyconstrained(
                timeslices,
                timeslice_in_season,
                timeslice_in_daytype,
                timeslice_in_timebracket,
            )
            adj = build_adjacency(
                years,
                timeslices,
                timeslice_in_season,
                timeslice_in_daytype,
                timeslice_in_timebracket,
                seasons,
                day_types,
                time_brackets,
            )
        values["adj"] = adj

    # validate parts keys against any splits AND/OR get assume equal
    year_split, days_in_day_type, day_split = validate_parts_from_splits(
        timeslices, day_types, time_brackets, values
    )

    values["year_split"] = year_split
    values["day_split"] = day_split
    values["days_in_day_type"] = days_in_day_type
    values["seasons"] = seasons
    values["day_types"] = day_types
    values["daily_time_brackets"] = time_brackets
    values["timeslice_in_season"] = timeslice_in_season
    values["timeslice_in_daytype"] = timeslice_in_daytype
    values["timeslice_in_timebracket"] = timeslice_in_timebracket

    return values


def construction_from_parts(values: Any):
    """pathway 2: years plus any of yearparts, daytypes, and dayparts, daysplit, yearsplit,
    days_in_daytype with optional adjacency
      - validate keys on provided yearparts, daytypes, dayparts, daysplit, yearsplit,
        days_in_daytype
      - build unitary yearparts, daytypes, and dayparts where not specified
      - build assume equal year, daytype, and day splitting where not specified
      - option: if adjacency is specified:
        - use specified adjacency, validating keys
        - else:
          - if ordered yearparts, daytypes, and dayparts given, assume adjacency
          - else: raise error for required parameter
    """
    years = values.get("years")
    seasons = values.get("seasons")
    day_types = values.get("day_types")
    time_brackets = values.get("daily_time_brackets")

    # build timeslices from parts
    timeslices = build_timeslices_from_parts(seasons, day_types, time_brackets)
    values["timeslices"] = timeslices

    # validate keys on splits, if any, or maybe get parts
    year_split, days_in_day_type, day_split = validate_parts_from_splits(
        timeslices, day_types, time_brackets, values
    )
    values["year_split"] = year_split
    values["day_split"] = day_split
    values["days_in_day_type"] = days_in_day_type

    # if adjacency is given, validate keys
    adj = values.get("adj")
    if adj is not None:
        validate_adjacency_keys(adj, timeslices, years, seasons, day_types, time_brackets)
    else:
        adj = TimeAdjacency(
            years=dict(zip(sorted(years)[:-1], sorted(years)[1:])),
            timeslices=dict(zip(timeslices[:-1], timeslices[1:])),
        )
        values["adj"] = adj

    return values


def construction_from_years_only(values: Any):
    """pathway 1: years only
    - build unitary yearparts, daytypes, and dayparts
    - build adjacency from ordered years
    """
    years = values.get("years")

    values["yearparts"] = [1]
    values["day_types"] = [1]
    values["seasons"] = [1]
    values["timeslices"] = [1]
    values["daily_time_brackets"] = [1]
    values["dayparts"] = [1]

    values["year_split"] = {1: 1.0}
    values["day_split"] = {1: 1.0}
    values["days_in_day_type"] = {1: 1.0}

    values["timeslice_in_timebracket"] = {1: 1}
    values["timeslice_in_daytype"] = {1: 1}
    values["timeslice_in_season"] = {1: 1}
    values["adj"] = TimeAdjacency.from_years(years)
    values["adj_inv"] = TimeAdjacency.from_years(years).inv()

    return values


def format_by_max_length(val: int, max):
    if max > 10:
        return f"{val:02}"
    if max >= 100:
        return f"{val:03}"
    return f"{val}"


def construction_from_yrparts_dayparts_int(values: Any):
    """pathway 2: years plus yearparts and dayparts as integers
    - build timeslices from yearparts and dayparts
    - build adjacency from ordered years and timeslices
    """
    years = values.get("years")
    yearparts = values.get("seasons")
    dayparts = values.get("daily_time_brackets")
    yearparts = [("s" + format_by_max_length(ii, yearparts)) for ii in range(1, yearparts + 1)]
    dayparts = [("h" + format_by_max_length(ii, dayparts)) for ii in range(1, dayparts + 1)]

    for key in [
        "timeslices",
        "timeslice_in_timebracket",
        "timeslice_in_daytype",
        "timeslice_in_season",
        "day_types",
        "day_split",
        "days_in_day_type",
        "year_split",
    ]:
        if values.get(key) is not None:
            raise ValueError(
                """If specifying time_definition with a
                             number of yearparts and dayparts, no other
                             time_definition parameters can be specified."""
            )

    timeslices = build_timeslices_from_parts(yearparts, dayparts)
    values["timeslices"] = timeslices

    values["timeslice_in_timebracket"] = {
        timeslice: [time_bracket for time_bracket in dayparts if time_bracket in timeslice]
        for timeslice in timeslices
    }
    values["timeslice_in_season"] = {
        timeslice: [season for season in yearparts if season in timeslice]
        for timeslice in timeslices
    }
    values["year_split"] = {yearpart: 1.0 / len(yearparts) for yearpart in yearparts}
    values["day_split"] = {daypart: 1.0 / len(dayparts) for daypart in dayparts}
    values["day_types"] = [1]
    values["day_split"] = {1: 1.0}
    values["days_in_day_type"] = {1: 1.0}
    values["timeslice_in_daytype"] = {timeslice: [1] for timeslice in timeslices}

    adj = TimeAdjacency(
        years=dict(zip(sorted(years)[:-1], sorted(years)[1:])),
        timeslices=dict(zip(timeslices[:-1], timeslices[1:])),
    )
    values["adj"] = adj
    values["adj_inv"] = adj.inv()

    return values


class TimeDefinition(OSeMOSYSBase, OtooleTimeDefinition):
    """
    Class to contain all temporal defition of the OSeMOSYS model.

    There are several pathways to constructing a TimeDefinition.

    pathway 1:
    years only

    pathway 2:
    years plus yearparts and dayparts as integers

    pathway 3:
    years plus any of yearparts, daytypes, and dayparts, daysplit, yearsplit, days_in_daytype
    with optional adjacency

    pathway 4:
    years plus any of timeslices, timeslice_in_timebracket, timeslice_in_daytype,
    timeslice_in_season with optional year_split, day_split, days_in_day_type
    and optional validation on yearparts, daytypes, and dayparts OR adjacency


    Attributes:
        years:
            List[int]: a list of integer years for the capacity expansion study.
                       Can also be a `range`.
        seasons:
            List[int | str]:
        timeslices:
            List[int | str]:
        day_types:
            List[int | str]:
        daily_time_brackets:
            List[int | str]:
        year_split:
            Mapping:
        day_split:
            Mapping:
        days_in_day_type:
            Mapping:
        timeslice_in_timebracket:
            Mapping:
        timeslice_in_daytype:
            Mapping:
        timeslice_in_season:
            Mapping:
        adj:
            TimeAdjacency:
        adj_inv:
            TimeAdjacency:
        otoole_cfg:
            OtooleCfg | None:

    """

    # TODO: fix yearparts and dayparts then make extra params forbidden again
    # model_config = ConfigDict(extra="forbid")

    # always required
    years: conlist(int, min_length=1)

    # can be constructed
    seasons: conlist(int | str, min_length=1) | int | None
    timeslices: conlist(int | str, min_length=1) | int | None
    day_types: conlist(int | str, min_length=1) | int | None
    daily_time_brackets: conlist(int | str, min_length=1) | int | None
    year_split: MappingSumOne | None
    day_split: Mapping | None
    days_in_day_type: Mapping | None
    timeslice_in_timebracket: Mapping | None
    timeslice_in_daytype: Mapping | None
    timeslice_in_season: Mapping | None

    adj: TimeAdjacency
    adj_inv: TimeAdjacency

    # TODO: post-validation that everything has the right keys and sums,etc.

    @field_validator("years")
    @classmethod
    def convert_from_range(cls, v: Any) -> Any:
        if isinstance(v, range):
            return list(v)
        return v

    @model_validator(mode="before")
    @classmethod
    def construction_validation(cls, values: Any, info: ValidationInfo) -> Any:
        # years is always required
        if values.get("years") is None:
            raise ValueError("'years' is a required parameter")
        if isinstance(values.get("seasons"), int) and isinstance(
            values.get("daily_time_brackets"), int
        ):
            values = construction_from_yrparts_dayparts_int(values)
        elif any(
            [
                values.get("timeslices") is not None,
                values.get("timeslice_in_timebracket") is not None,
                values.get("timeslice_in_daytype") is not None,
                values.get("timeslice_in_season") is not None,
            ]
        ):
            # Validation if timeslice is provided
            values = construction_from_timeslices(values)
        elif any(
            [
                values.get("yearparts") is not None,
                values.get("daily_time_brackets") is not None,
                values.get("daytypes") is not None,
                values.get("year_split") is not None,
                values.get("day_split") is not None,
                values.get("days_in_day_type") is not None,
            ]
        ):
            # Validation if parts or splits are provided
            values = construction_from_parts(values)
        else:
            # just years provided
            values = construction_from_years_only(values)

        # maybe flip adj
        if values.get("adj_inv") is None:
            if isinstance(values.get("adj"), TimeAdjacency):
                values["adj_inv"] = values["adj"].inv()
            elif isinstance(values.get("adj"), dict):
                values["adj_inv"] = TimeAdjacency(**values["adj"]).inv()

        return values

    @model_validator(mode="before")
    @classmethod
    def convert_from_int(cls, values: Any) -> Any:
        for key in ("timeslices", "day_types"):
            if isinstance(values.get(key), int):
                values[key] = [str(ii) for ii in range(1, values[key] + 1)]
        return values
