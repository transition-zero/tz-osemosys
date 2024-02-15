from pathlib import Path
from typing import Any, ClassVar, List, Mapping, Union

import pandas as pd
from pydantic import BaseModel, Field, ValidationInfo, conlist, field_validator, model_validator

from feo.osemosys.schemas.validation.timedefinition_validation import (
    build_adjacency,
    get_timeslices_from_sets,
    maybe_get_parts_from_timeslice_mappings,
    timeslice_match_timeslice_in_set,
    validate_adjacency_fullyconstrained,
    validate_adjacency_keys,
    validate_parts_from_splits,
)
from feo.osemosys.utils import group_to_json

from .base import MappingSumOne, OSeMOSYSBase, OSeMOSYSData


class OtooleCfg(BaseModel):
    """
    Paramters needed to round-trip csvs from otoole
    """

    empty_dfs: List[str] | None


class TimeAdjacency(BaseModel):
    years: dict[int, int]
    seasons: dict[str, str] | None = Field(default={})  # default no adjacency
    day_types: dict[str, str] | None = Field(default={})
    time_brackets: dict[str, str] | None = Field(default={})
    timeslices: dict[str, str] | None = Field(default={})

    @classmethod
    def from_years(cls, years):
        return cls(years=dict(zip(sorted(years)[:-1], sorted(years)[1:])))

    def inv(self):
        return TimeAdjacency(
            years={v: k for k, v in self.years.items()},
            seasons={v: k for k, v in self.seasons.items()} if self.seasons else None,
            day_types={v: k for k, v in self.day_types.items()} if self.day_types else None,
            time_brackets={v: k for k, v in self.time_brackets.items()}
            if self.time_brackets
            else None,
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
    print("IMESLICES", timeslices)

    # get parts from any timeslice_mappings and validate keys
    (
        seasons,
        day_types,
        time_brackets,
        timeslice_in_season,
        timeslice_in_daytype,
        timeslice_in_timebracket,
    ) = maybe_get_parts_from_timeslice_mappings(timeslices, values)
    print(f"{seasons=}, {timeslices=}, {day_types=}, {time_brackets=}")

    # validate adjacency or check underconstraint
    # if adjacency is given, validate keys
    adj = values.get("adj")
    if adj is not None:
        print("adj not nonde")
        validate_adjacency_keys(adj, timeslices, years, seasons, day_types, time_brackets)
    # elif adjacency is not given, check for underconstraint then build adjacency
    else:
        print("adj is None")
        # if only timeslices are given, then assume adjacency from timeslice order
        if all([seasons, day_types, time_brackets]):
            adj = dict(
                years=dict(zip(sorted(years)[:-1], sorted(years)[1:])),
                timeslices=dict(zip(timeslices[:-1], timeslices[1:])),
            )
        else:
            print("check and build")
            # validate adjacency is fully constrained
            validate_adjacency_fullyconstrained(
                timeslices, timeslice_in_season, timeslice_in_daytype, timeslice_in_timebracket
            )
            print("valid hellp")
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
        seasons, day_types, time_brackets, values
    )
    print(f"{seasons=}, {timeslices=}, {day_types=}, {time_brackets=}, {adj=}, {day_split=}")

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

    values["timeslice_in_timebracket"] = {1: [1]}
    values["timeslice_in_daytype"] = {1: [1]}
    values["timeslice_in_season"] = {1: [1]}
    values["adj"] = TimeAdjacency.from_years(years)
    values["adj_inv"] = TimeAdjacency.from_years(years).inv()

    return values


class TimeDefinition(OSeMOSYSBase):
    """
    Class to contain all temporal defition of the OSeMOSYS model.

    There are several pathways to constructing a TimeDefinition.

    pathway 1:
    years only

    pathway 2:
    years plus any of yearparts, daytypes, and dayparts, daysplit, yearsplit, days_in_daytype
    with optional adjacency

    pathway 3:
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

    # always required
    years: conlist(int, min_length=1)

    # can be constructed
    seasons: conlist(int | str, min_length=1) | int | None
    timeslices: conlist(int | str, min_length=1) | int | None
    day_types: conlist(int | str, min_length=1) | int | None
    daily_time_brackets: conlist(int | str, min_length=1) | int | None
    year_split: MappingSumOne | None
    day_split: MappingSumOne | None
    days_in_day_type: Mapping | None
    timeslice_in_timebracket: Mapping | None
    timeslice_in_daytype: Mapping | None
    timeslice_in_season: Mapping | None

    adj: TimeAdjacency
    adj_inv: TimeAdjacency

    otoole_cfg: OtooleCfg | None = Field(default=None)
    otoole_stems: ClassVar[dict[str : dict[str : Union[str, list[str]]]]] = {
        "YEAR": {"attribute": "years", "column_structure": ["VALUE"]},
        "SEASON": {"attribute": "seasons", "column_structure": ["VALUE"]},
        "TIMESLICE": {"attribute": "timeslices", "column_structure": ["VALUE"]},
        "DAYTYPE": {"attribute": "day_types", "column_structure": ["VALUE"]},
        "DAILYTIMEBRACKET": {"attribute": "daily_time_brackets", "column_structure": ["VALUE"]},
        "MODE_OF_OPERATION": {"attribute": "mode_of_operation", "column_structure": ["VALUE"]},
        "YearSplit": {
            "attribute": "year_split",
            "column_structure": ["TIMESLICE", "YEAR", "VALUE"],
        },
        "DaySplit": {
            "attribute": "day_split",
            "column_structure": ["DAILYTIMEBRACKET", "YEAR", "VALUE"],
        },
        "DaysInDayType": {
            "attribute": "days_in_day_type",
            "column_structure": ["SEASON", "DAYTYPE", "YEAR", "VALUE"],
        },
        "Conversionlh": {
            "attribute": "timeslice_in_timebracket",
            "column_structure": ["TIMESLICE", "DAILYTIMEBRACKET", "VALUE"],
        },
        "Conversionld": {
            "attribute": "timeslice_in_daytype",
            "column_structure": ["TIMESLICE", "DAYTYPE", "VALUE"],
        },
        "Conversionls": {
            "attribute": "timeslice_in_season",
            "column_structure": ["TIMESLICE", "SEASON", "VALUE"],
        },
    }

    # TODO: post-validation that everything has the right keys and sums,etc.

    @field_validator("years")
    @classmethod
    def convert_from_range(cls, v: Any) -> Any:
        if isinstance(v, range):
            return list(v)
        return v

    @field_validator("seasons", "timeslices", "day_types", "daily_time_brackets")
    @classmethod
    def convert_from_int(cls, v: Any) -> Any:
        if isinstance(v, int):
            return list(range(1, v + 1))
        return v

    @model_validator(mode="before")
    @classmethod
    def construction_validation(cls, values: Any, info: ValidationInfo) -> Any:
        # years is always required
        if values.get("years") is None:
            raise ValueError("'years' is a required parameter")
        if any(
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

    # @field_validator('adj_inv')
    # @classmethod
    # def convert_from_range(cls, v: Any, info: ValidationInfo) -> Any:
    #     print ('ADJ_INV validator',v)
    #     if v is None:
    #         if isinstance(info.data.adj, TimeAdjacency):
    #             return info.data.adj.inv()
    #         elif isinstance(info.data.adj, dict):
    #             return TimeAdjacency(**info.data.adj).inv()
    #     return v

    # @root_validator(pre=True)
    # def validation(cls, values):
    #     # Validation if timeslice is provided
    #     values = timeslice_match_timeslice_in_set(values)
    #     values = timeslice_in_set_match_set(values)
    #     values = timeslice_in_set_provided(values)
    #     values = construct_timebracket(values)
    #     values = construct_daytype(values)
    #     values = construct_season(values)
    #     # Validation if timeslice is not provided
    #     values = construct_daytypes_no_timeslice(values)
    #     values = construct_dailytimebracket_no_timeslice(values)
    #     values = construct_season_no_timeslice(values)
    #     values = construct_timeslice(values)
    #     # Validation/construction for year_split/day_split/days_in_day_type
    #     values = validate_construct_year_split(values)
    #     values = validate_construct_day_split(values)
    #     values = validate_construct_days_in_day_type(values)
    #     # Construction of adjaceny matrices
    #     values = construct_adjacency_matrices(values)

    #     # TODO: determine why this final assigning of values is required to avoid
    #     validation errors
    #     year_split = values.get("year_split")
    #     day_split = values.get("day_split")
    #     days_in_day_type = values.get("days_in_day_type")
    #     timeslice_in_timebracket = values.get("timeslice_in_timebracket")
    #     timeslice_in_daytype = values.get("timeslice_in_daytype")
    #     timeslice_in_season = values.get("timeslice_in_season")
    #     values["year_split"] = OSeMOSYSData(data=year_split)
    #     values["day_split"] = OSeMOSYSData(data=day_split)
    #     values["days_in_day_type"] = OSeMOSYSData(data=days_in_day_type)
    #     values["timeslice_in_timebracket"] = OSeMOSYSData(data=timeslice_in_timebracket)
    #     values["timeslice_in_daytype"] = OSeMOSYSData(data=timeslice_in_daytype)
    #     values["timeslice_in_season"] = OSeMOSYSData(data=timeslice_in_season)

    #     return values

    @classmethod
    def from_otoole_csv(cls, root_dir) -> "TimeDefinition":
        """
        Instantiate a single TimeDefinition object containing all relevant data from
        otoole-organised csvs.

        Parameters
        ----------
        root_dir: str
            Path to the root of the otoole csv directory

        Returns
        -------
        TimeDefinition
            A single TimeDefinition instance that can be used downstream or dumped to json/yaml
        """

        # ###########
        # Load Data #
        # ###########
        dfs = {}
        otoole_cfg = OtooleCfg(empty_dfs=[])
        for key in list(cls.otoole_stems):
            try:
                dfs[key] = pd.read_csv(Path(root_dir) / f"{key}.csv")
                if dfs[key].empty:
                    otoole_cfg.empty_dfs.append(key)
            except FileNotFoundError:
                otoole_cfg.empty_dfs.append(key)

        # ###################
        # Basic Data Checks #
        #####################

        # Assert days in day type values <=7
        assert (
            dfs["DaysInDayType"]["VALUE"].isin([1, 2, 3, 4, 5, 6, 7]).all()
        ), "Days in day type can only take values from 1-7"

        if "YEAR" in dfs:
            years = dfs["YEAR"]["VALUE"].astype(str).values.tolist()
        else:
            raise FileNotFoundError("YEAR.csv not read in, likely missing from root_dir")
        if "MODE_OF_OPERATION" in dfs:
            mode_of_operation = dfs["MODE_OF_OPERATION"]["VALUE"].astype(str).values.tolist()
        else:
            raise FileNotFoundError(
                "MODE_OF_OPERATION.csv not read in, likely missing from root_dir"
            )
        seasons = (
            dfs["SEASON"]["VALUE"].astype(str).values.tolist()
            if "SEASON" not in otoole_cfg.empty_dfs
            else None
        )
        day_types = (
            dfs["DAYTYPE"]["VALUE"].astype(str).values.tolist()
            if "DAYTYPE" not in otoole_cfg.empty_dfs
            else None
        )
        daily_time_brackets = (
            dfs["DAILYTIMEBRACKET"]["VALUE"].astype(str).values.tolist()
            if "DAILYTIMEBRACKET" not in otoole_cfg.empty_dfs
            else None
        )
        timeslices = (
            dfs["TIMESLICE"]["VALUE"].values.tolist()
            if "TIMESLICE" not in otoole_cfg.empty_dfs
            else None
        )

        return cls(
            id="TimeDefinition",
            long_name=None,
            description=None,
            years=years,
            seasons=seasons,
            timeslices=timeslices,
            day_types=day_types,
            otoole_cfg=otoole_cfg,
            daily_time_brackets=daily_time_brackets,
            mode_of_operation=mode_of_operation,
            year_split=(
                OSeMOSYSData(
                    data=group_to_json(
                        g=dfs["YearSplit"],
                        data_columns=["TIMESLICE", "YEAR"],
                        target_column="VALUE",
                    )
                ).model_dump()["data"]
                if "YearSplit" not in otoole_cfg.empty_dfs
                else None
            ),
            day_split=(
                OSeMOSYSData(
                    data=group_to_json(
                        g=dfs["DaySplit"],
                        data_columns=["DAILYTIMEBRACKET", "YEAR"],
                        target_column="VALUE",
                    )
                ).model_dump()["data"]
                if "DaySplit" not in otoole_cfg.empty_dfs
                else None
            ),
            days_in_day_type=(
                OSeMOSYSData(
                    data=group_to_json(
                        g=dfs["DaysInDayType"],
                        data_columns=["SEASON", "DAYTYPE", "YEAR"],
                        target_column="VALUE",
                    )
                ).model_dump()["data"]
                if "DaysInDayType" not in otoole_cfg.empty_dfs
                else None
            ),
            timeslice_in_daytype=(
                OSeMOSYSData(
                    data=group_to_json(
                        g=dfs["Conversionld"],
                        data_columns=["TIMESLICE", "DAYTYPE"],
                        target_column="VALUE",
                    )
                ).model_dump()["data"]
                if "Conversionld" not in otoole_cfg.empty_dfs
                else None
            ),
            timeslice_in_timebracket=(
                OSeMOSYSData(
                    data=group_to_json(
                        g=dfs["Conversionlh"],
                        data_columns=["TIMESLICE", "DAILYTIMEBRACKET"],
                        target_column="VALUE",
                    )
                ).model_dump()["data"]
                if "Conversionlh" not in otoole_cfg.empty_dfs
                else None
            ),
            timeslice_in_season=(
                OSeMOSYSData(
                    data=group_to_json(
                        g=dfs["Conversionls"],
                        data_columns=["TIMESLICE", "SEASON"],
                        target_column="VALUE",
                    )
                ).model_dump()["data"]
                if "Conversionls" not in otoole_cfg.empty_dfs
                else None
            ),
        )
