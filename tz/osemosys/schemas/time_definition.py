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
            seasons={v: k for k, v in self.seasons.items()} if self.seasons is not None else None,
            day_types=(
                {v: k for k, v in self.day_types.items()} if self.day_types is not None else None
            ),
            time_brackets=(
                {v: k for k, v in self.time_brackets.items()}
                if self.time_brackets is not None
                else None
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

    def _first_part_in_timeslice(parts, timeslice):
        for part in parts:
            if part in timeslice:
                return part
        raise ValueError(f"None of {parts} are in {timeslices}")

    # Convert list of int to list of str
    for key in values.keys():
        if isinstance(values[key], list):
            values[key] = [str(item) if isinstance(item, int) else item for item in values[key]]

    years = values.get("years")
    seasons = values.get("seasons")
    day_types = values.get("day_types")
    time_brackets = values.get("daily_time_brackets")

    # build timeslices from parts
    timeslices = build_timeslices_from_parts(seasons, day_types, time_brackets)
    values["timeslices"] = timeslices

    # build time_brackets/seasons/day_types and link to timeslice if necessary
    if time_brackets:
        values["timeslice_in_timebracket"] = {
            timeslice: _first_part_in_timeslice(time_brackets, timeslice)
            for timeslice in timeslices
        }
    else:
        values["daily_time_brackets"] = ["1"]
        values["timeslice_in_timebracket"] = {timeslice: "1" for timeslice in timeslices}
    if seasons:
        values["timeslice_in_season"] = {
            timeslice: _first_part_in_timeslice(seasons, timeslice) for timeslice in timeslices
        }
    else:
        values["seasons"] = ["1"]
        values["timeslice_in_season"] = {timeslice: "1" for timeslice in timeslices}
    if day_types:
        values["timeslice_in_daytype"] = {
            timeslice: _first_part_in_timeslice(day_types, timeslice) for timeslice in timeslices
        }
    else:
        values["day_types"] = ["1"]
        values["timeslice_in_daytype"] = {timeslice: "1" for timeslice in timeslices}

    # validate keys on splits, if any, or maybe get parts
    year_split, days_in_day_type, day_split = validate_parts_from_splits(
        timeslices,
        day_types or values["day_types"],
        time_brackets or values["daily_time_brackets"],
        values,
    )
    values["year_split"] = year_split
    values["day_split"] = day_split
    values["days_in_day_type"] = days_in_day_type

    # if adjacency is given, validate keys
    adj = values.get("adj")
    if adj is not None:
        validate_adjacency_keys(adj, timeslices, years, seasons, day_types, time_brackets)
    else:
        build_adj = dict(
            years=dict(zip(sorted(years)[:-1], sorted(years)[1:])),
            timeslices=dict(zip(timeslices[:-1], timeslices[1:])),
        )
        if seasons is not None:
            build_adj["seasons"] = (
                dict(zip(seasons[:-1], seasons[1:])) if len(seasons) > 1 else None
            )
        if day_types is not None:
            build_adj["day_types"] = (
                dict(zip(day_types[:-1], day_types[1:])) if len(day_types) > 1 else None
            )
        if time_brackets is not None:
            build_adj["time_brackets"] = (
                dict(zip(time_brackets[:-1], time_brackets[1:])) if len(time_brackets) > 1 else None
            )

        adj = TimeAdjacency(**build_adj)
        values["adj"] = adj

    return values


def construction_from_years_only(values: Any):
    """pathway 1: years only
    - build unitary yearparts, daytypes, and dayparts
    - build adjacency from ordered years
    """
    years = values.get("years")

    values["yearparts"] = ["1"]
    values["day_types"] = ["1"]
    values["seasons"] = ["1"]
    values["timeslices"] = ["1"]
    values["daily_time_brackets"] = ["1"]
    values["dayparts"] = ["1"]

    values["year_split"] = {"1": 1.0}
    values["day_split"] = {"1": 1.0}
    values["days_in_day_type"] = {"1": 1.0}

    values["timeslice_in_timebracket"] = {"1": "1"}
    values["timeslice_in_daytype"] = {"1": "1"}
    values["timeslice_in_season"] = {"1": "1"}
    values["adj"] = TimeAdjacency(
        years=dict(zip(sorted(years)[:-1], sorted(years)[1:])),
    )
    values["adj_inv"] = values["adj"].inv()

    return values


def format_by_max_length(val: int, max):
    if max > 10:
        return f"{val:02}"
    if max >= 100:
        return f"{val:03}"
    return f"{val}"


class TimeDefinition(OSeMOSYSBase, OtooleTimeDefinition):
    """
    # TimeDefinition

    The TimeDefinition class contains all temporal data needed for an OSeMOSYS model. There are
    multiple pathways to creating a TimeDefinition object, where any missing information is
    inferred from the data provided.

    Only a single instance of TimeDefinition is needed to run a model and, as a minimum, only
    `years` need to be provided to create a TimeDefinition object.

    The other parameters corresponding to the OSeMOSYS time related sets (`seasons`, `timeslices`,
    `day_types`, `daily_time_brackets`) can be provided as lists or ranges.

    One parameter additional to those correponsding to OSeMOSYS parameters is used , `adj`,
    which specified the adjency matrices for `years`, `seasons`, `day_types`,
    `daily_time_brackets`, `timeslices`. If not providing values for `adj`, it is assumed that
    the other variables are provided in order from first to last. If providing the values directly,
    these can be provided as a dict, an example of which for years and timeslices is below:

    ```python
    adj = {
        "years": dict(zip(range(2020, 2050), range(2021, 2051))),
        "timeslices": {"A": "B", "B": "C", "C": "D"},
    }
    ```

    ### Pathway 1 - Construction from years only

    If only `years` are provided, the remaining necessary temporal parameters (`seasons`,
    `day_types`, `daily_time_brackets`) are assumed to be singular.

    ### Pathway 2 - Construction from parts

    If no timeslice data is provided, but any of the below is, it is used to construct timeslices:
        - seasons
        - daily_time_brackets
        - day_types
        - year_split
        - day_split
        - days_in_day_type

    ### Pathway 3 - Construction from timeslices

    If timeslices are provided via any of the below parameters, this is used to construct the
    TimeDefinition object:
        - timeslices
        - timeslice_in_timebracket
        - timeslice_in_daytype
        - timeslice_in_season


    ## Parameters

    `id` `(str)`: Any value may be provided for the single TimeDefintion instance.
    Required parameter.

    `years` `(List[int] | range(int)) | int`: OSeMOSYS YEARS. Required parameter.

    `seasons` `(List[int | str]) | int`: OSeMOSYS SEASONS.
    Optional, constructed if not provided.

    `timeslices` `(List[int | str]) | int`: OSeMOSYS TIMESLICES.
    Optional, constructed if not provided.

    `day_types` `(List[int | str]) | int`: OSeMOSYS DAYTYPES.
    Optional, constructed if not provided.

    `daily_time_brackets` `(List[int | str])`: OSeMOSYS DAILYTIMEBRACKETS.
    Optional, constructed if not provided.

    `year_split` `({timeslice:{year:float}})`: OSeMOSYS YearSplit.
    Optional, constructed if not provided.

    `day_split` `({daily_time_bracket:{year:float}})`: OSeMOSYS DaySplit.
    Optional, constructed if not provided.

    `days_in_day_type` `({season:{day_type:{year:int}}})`: OSeMOSYS DaysInDayType.
    Optional, constructed if not provided.

    `timeslice_in_timebracket` `({timeslice:daily_time_bracket})`: OSeMOSYS Conversionlh.
    Optional, constructed if not provided.

    `timeslice_in_daytype` `({timeslice:day_type})`: OSeMOSYS Conversionld.
    Optional, constructed if not provided.

    `timeslice_in_season` `({timeslice:season})`: OSeMOSYS Conversionls.
    Optional, constructed if not provided.

    `adj` `({str:dict})`: Parameter to manually define adjanecy for `years`, `seasons`,
    `day_types`, `daily_time_brackets`, and `timeslices`. Optional, if not providing values for
    `adj`, it is assumed that the other variables are provided in order from first to last.

    ## Examples

    Examples are given below of how a TimeDefinition object might be created using the different
    pathways.

    ### Pathway 1 - Construction from years only

    ```python
    from tz.osemosys.schemas.time_definition import TimeDefinition

    basic_time_definition = dict(
        id="pathway_1",
        years=[2021, 2022, 2023],
    )

    TimeDefinition(**basic_time_definition)
    ```

    ### Pathway 2 - Construction from parts

    ```python
    from tz.osemosys.schemas.time_definition import TimeDefinition

    basic_time_definition = dict(
        id="pathway_2",
        years=range(2020, 2051),
        seasons=["winter", "summer"],
        daily_time_brackets=["morning", "day", "evening", "night"],
    )

    TimeDefinition(**basic_time_definition)
    ```

    ### Pathway 3 - Construction from timeslices

    ```python
    from tz.osemosys.schemas.time_definition import TimeDefinition

    basic_time_definition = dict(
        id="pathway_3",
        years=range(2020, 2051),
        timeslices=["A", "B", "C", "D"],
        adj={
            "years": dict(zip(range(2020, 2050), range(2021, 2051))),
            "timeslices": dict(zip(["A", "B", "C"], ["B", "C", "D"])),
        },
    )

    TimeDefinition(**basic_time_definition)
    ```

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

        # # Pathway x
        # if isinstance(values.get("seasons"), int) and isinstance(
        #     values.get("daily_time_brackets"), int
        # ):
        #     values = construction_from_yrparts_dayparts_int(values)

        # Pathway 3
        if any(
            [
                values.get("timeslices") is not None,
                values.get("timeslice_in_timebracket") is not None,
                values.get("timeslice_in_daytype") is not None,
                values.get("timeslice_in_season") is not None,
            ]
        ):
            values = construction_from_timeslices(values)
        # Pathway 2
        elif any(
            [
                values.get("seasons") is not None,
                values.get("daily_time_brackets") is not None,
                values.get("day_types") is not None,
                values.get("year_split") is not None,
                values.get("day_split") is not None,
                values.get("days_in_day_type") is not None,
            ]
        ):
            values = construction_from_parts(values)
        # Pathway 1
        else:
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
