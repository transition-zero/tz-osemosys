import os
import re
from itertools import product
from pathlib import Path
from typing import ClassVar

import pandas as pd
from pydantic import BaseModel, conlist, root_validator

from feo.osemosys.utils import *

from .base import *


class OtooleCfg(BaseModel):
    """
    Paramters needed to round-trip csvs from otoole
    """

    empty_dfs: List[str] | None


class TimeAdjacency(BaseModel):
    years: dict[str, str]
    seasons: dict[str, str]
    day_types: dict[str, str]
    time_brackets: dict[str, str]


class TimeDefinition(OSeMOSYSBase):
    """
    Class to contain all temporal information, including years and timeslices.
    """

    # always required
    years: conlist(int, min_length=1)

    # can be constructed
    seasons: conlist(int | str, min_length=1)
    timeslices: conlist(int | str, min_length=1)
    day_types: conlist(int | str, min_length=1)
    daily_time_brackets: conlist(int | str, min_length=1)
    year_split: OSeMOSYSData
    day_split: OSeMOSYSData
    days_in_day_type: OSeMOSYSData
    timeslice_in_timebracket: OSeMOSYSData
    timeslice_in_daytype: OSeMOSYSData
    timeslice_in_season: OSeMOSYSData

    adj: TimeAdjacency
    adj_inv: TimeAdjacency

    otoole_cfg: OtooleCfg | None
    otoole_stems: ClassVar[dict[str : dict[str : Union[str, list[str]]]]] = {
        "YEAR": {"attribute": "years", "column_structure": ["VALUE"]},
        "SEASON": {"attribute": "seasons", "column_structure": ["VALUE"]},
        "TIMESLICE": {"attribute": "timeslices", "column_structure": ["VALUE"]},
        "DAYTYPE": {"attribute": "day_types", "column_structure": ["VALUE"]},
        "DAILYTIMEBRACKET": {
            "attribute": "daily_time_brackets",
            "column_structure": ["VALUE"],
        },
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

    @root_validator(pre=True)
    def construct_from_components(cls, values):
        years = values.get("years")
        seasons = values.get("seasons")
        timeslices = values.get("timeslices")
        day_types = values.get("day_types")
        daily_time_brackets = values.get("daily_time_brackets")
        year_split = values.get("year_split")
        day_split = values.get("day_split")
        days_in_day_type = values.get("days_in_day_type")
        timeslice_in_timebracket = values.get("timeslice_in_timebracket")
        timeslice_in_daytype = values.get("timeslice_in_daytype")
        timeslice_in_season = values.get("timeslice_in_season")
        adj = values.get("adj")
        adj_inv = values.get("adj_inv")

        # failed to specify years
        if not years:
            raise ValueError("years (List[int]) must be specified.")

        # maybe get timeslices from 'in' constructs or directly
        if timeslices is not None:
            # make sure it's index matchs the 'in' constructs
            # timebrackets:
            if timeslice_in_timebracket is not None:
                if set(timeslices) != set(timeslice_in_timebracket.keys()):
                    raise ValueError(
                        "provided 'timeslices' do not match keys of 'timeslice_in_timebracket'"
                    )
                if daily_time_brackets is not None:
                    if set(daily_time_brackets) != set(
                        flatten(
                            [
                                list(v.keys())
                                for k, v in timeslice_in_timebracket.items()
                            ]
                        )
                    ):
                        raise ValueError(
                            "provided 'timeslice_in_timebracket' keys do not match 'daily_time_brackets'"
                        )
            else:
                if daily_time_brackets is not None:
                    raise ValueError(
                        "if providing 'timeslices' and 'time_brackets', the joining 'timeslice_in_timebracket' must be provided"
                    )
                # If timeslices defined, but neither daily_time_brackets nor timeslice_in_timebracket is
                else:
                    for item in timeslices:
                        if "H2" in item:
                            raise ValueError(
                                "More than one daily time bracket specified in timeslices, daily_time_brackets and timeslice_in_timebracket must be provided"
                            )
                    # default to a single timebracket
                    daily_time_brackets = [1]
                    timeslice_in_timebracket = pd.DataFrame({"TIMESLICE": timeslices})
                    timeslice_in_timebracket["DAILYTIMEBRACKET"] = 1
                    timeslice_in_timebracket["VALUE"] = 1
                    timeslice_in_timebracket = group_to_json(
                        g=timeslice_in_timebracket,
                        data_columns=["TIMESLICE", "DAILYTIMEBRACKET"],
                        target_column="VALUE",
                    )

            # daytype
            if timeslice_in_daytype is not None:
                if set(timeslices) != set(timeslice_in_daytype.keys()):
                    raise ValueError(
                        "provided 'timeslices' do not match keys of 'timeslice_in_daytype'"
                    )
                if timeslice_in_daytype is not None:
                    if set(day_types) != set(
                        flatten(
                            [list(v.keys()) for k, v in timeslice_in_daytype.items()]
                        )
                    ):
                        raise ValueError(
                            "provided 'timeslice_in_daytype' keys do not match 'day_types'"
                        )
            else:
                if day_types is not None:
                    raise ValueError(
                        "if providing 'timeslices' and 'day_types', the joining 'timeslice_in_daytype' must be provided"
                    )
                # If timeslices defined, but neither day_types nor timeslice_in_daytype is
                else:
                    for item in timeslices:
                        if "D2" in item:
                            raise ValueError(
                                "More than one day type specified in timeslices, day_types and timeslice_in_daytype must be provided"
                            )
                    # default to a single daytype
                    day_types = [1]
                    timeslice_in_daytype = pd.DataFrame({"TIMESLICE": timeslices})
                    timeslice_in_daytype["DAYTYPE"] = 1
                    timeslice_in_daytype["VALUE"] = 1
                    timeslice_in_daytype = group_to_json(
                        g=timeslice_in_daytype,
                        data_columns=["TIMESLICE", "DAYTYPE"],
                        target_column="VALUE",
                    )

            # seasons
            if timeslice_in_season is not None:
                if set(timeslices) != set(timeslice_in_season.keys()):
                    raise ValueError(
                        "provided 'timeslices' do not match keys of 'timeslice_in_season'"
                    )
                if timeslice_in_season is not None:
                    if set(seasons) != set(
                        flatten(
                            [list(v.keys()) for k, v in timeslice_in_season.items()]
                        )
                    ):
                        raise ValueError(
                            "provided 'timeslice_in_season' keys do not match 'seasons'"
                        )
            else:
                if seasons is not None:
                    raise ValueError(
                        "if providing 'timeslices' and 'seasons', the joining 'timeslice_in_season' must be provided"
                    )
                # If timeslices defined, but neither seasons nor timeslice_in_season is
                else:
                    for item in timeslices:
                        if "S2" in item:
                            raise ValueError(
                                "More than one season specified in timeslices, seasons and timeslice_in_season must be provided"
                            )
                    # default to a single season
                    seasons = [1]
                    timeslice_in_season = pd.DataFrame({"TIMESLICE": timeslices})
                    timeslice_in_season["SEASON"] = 1
                    timeslice_in_season["VALUE"] = 1
                    timeslice_in_season = group_to_json(
                        g=timeslice_in_season,
                        data_columns=["TIMESLICE", "SEASON"],
                        target_column="VALUE",
                    )

        else:
            # timeslices not defined

            if timeslice_in_daytype is not None:
                timeslices = timeslice_in_daytype.keys()
                if day_types is not None:
                    if set(day_types) != set(
                        flatten(
                            [list(v.keys()) for k, v in timeslice_in_daytype.items()]
                        )
                    ):
                        raise ValueError(
                            "provided 'timeslice_in_daytype' keys do not match 'day_types'"
                        )
                else:
                    day_types = sorted(
                        flatten(
                            [list(v.keys()) for k, v in timeslice_in_daytype.items()]
                        )
                    )
            else:
                if day_types is None:
                    day_types = [1]

            if timeslice_in_timebracket is not None:
                if timeslices is None:
                    timeslices = timeslice_in_timebracket.keys()
                else:
                    if set(timeslices) != set(timeslice_in_timebracket.keys()):
                        raise ValueError(
                            "provided 'timeslice_in_timebracket' keys do not match other timeslice joins."
                        )
                if daily_time_brackets is not None:
                    if set(daily_time_brackets) != set(
                        flatten(
                            [
                                list(v.keys())
                                for k, v in timeslice_in_timebracket.items()
                            ]
                        )
                    ):
                        raise ValueError(
                            "provided 'timeslice_in_timebracket' keys do not match 'daily_time_brackets'"
                        )
                else:
                    daily_time_brackets = sorted(
                        flatten(
                            [
                                list(v.keys())
                                for k, v in timeslice_in_timebracket.items()
                            ]
                        )
                    )
            else:
                if daily_time_brackets is None:
                    daily_time_brackets = [1]

            if timeslice_in_season is not None:
                if timeslices is None:
                    timeslices = timeslice_in_season.keys()
                else:
                    if set(timeslices) != set(timeslice_in_season.keys()):
                        raise ValueError(
                            "provided 'timeslice_in_season' keys do not match other timeslice joins."
                        )
                if seasons is not None:
                    if set(seasons) != set(
                        flatten(
                            [list(v.keys()) for k, v in timeslice_in_season.items()]
                        )
                    ):
                        raise ValueError(
                            "provided 'timeslice_in_season' keys do not match 'seasons'"
                        )
                else:
                    seasons = sorted(
                        flatten(
                            [list(v.keys()) for k, v in timeslice_in_season.items()]
                        )
                    )
            else:
                if seasons is None:
                    seasons = [1]

        if timeslices is None:
            # timeslices is _still_ None: join our time_brackets, day_types, and SEASON
            # our timeslice_in_<object> constructs are also empty, let's build all

            timeslice_in_season, timeslice_in_daytype, timeslice_in_timebracket = (
                makehash(),
                makehash(),
                makehash(),
            )
            timeslices = []

            for season, day_type, time_bracket in product(
                seasons, day_types, daily_time_brackets
            ):
                timeslices.append(f"S{season}D{day_type}H{time_bracket}")
                timeslice_in_season[f"S{season}D{day_type}H{time_bracket}"][season] = 1
                timeslice_in_daytype[f"S{season}D{day_type}H{time_bracket}"][
                    day_type
                ] = 1
                timeslice_in_timebracket[f"S{season}D{day_type}H{time_bracket}"][
                    time_bracket
                ] = 1

        # For year_split/day_split/days_in_day_type:
        # check that they have the correct keys, or if they're None build from scratch

        ### year_split ###
        if year_split is not None:
            if set(year_split.keys()) != set(timeslices):
                raise ValueError("'year_split' keys do not match timeslices.")
        else:
            # TODO: check sum equals 1

            # Assume each timeslice of same length
            year_split_length = 1 / len(timeslices)

            # Construct data
            year_split_df = pd.DataFrame(
                {
                    "TIMESLICE": pd.Series(dtype="object"),
                    "YEAR": pd.Series(dtype="int32"),
                    "VALUE": pd.Series(dtype="float64"),
                }
            )

            for timeslice in timeslices:
                year_split_df = pd.concat(
                    [
                        year_split_df,
                        pd.DataFrame(
                            {
                                "TIMESLICE": timeslice,
                                "YEAR": years,
                                "VALUE": year_split_length,
                            }
                        ),
                    ]
                )
            year_split = group_to_json(
                g=year_split_df,
                data_columns=["TIMESLICE", "YEAR"],
                target_column="VALUE",
            )

        ### day_split ###
        if day_split is not None:
            if set(day_split.keys()) != set(daily_time_brackets):
                raise ValueError("'day_split' keys do not match daily_time_brackets.")
        else:
            # TODO: check sum equals 1

            # Assume all daily ticket brackets are of equal length
            day_split_length = ((1 / len(daily_time_brackets)) * 24) / (365 * 24)

            # Construct data
            day_split_df = pd.DataFrame(
                {
                    "DAILYTIMEBRACKET": pd.Series(dtype="object"),
                    "YEAR": pd.Series(dtype="int32"),
                    "VALUE": pd.Series(dtype="float64"),
                }
            )
            for bracket in daily_time_brackets:
                day_split_df = pd.concat(
                    [
                        day_split_df,
                        pd.DataFrame(
                            {
                                "DAILYTIMEBRACKET": bracket,
                                "YEAR": years,
                                "VALUE": day_split_length,
                            }
                        ),
                    ]
                )
            day_split = group_to_json(
                g=day_split_df,
                data_columns=["DAILYTIMEBRACKET", "YEAR"],
                target_column="VALUE",
            )

        ### days_in_day_type ###
        if days_in_day_type is not None:
            # Get daytypes from 2nd level of nested keys
            daytype_keys = []
            for level1_key, level2_dict in days_in_day_type.items():
                for level2_key in level2_dict:
                    daytype_keys.append(level2_key)
            if set(daytype_keys) != set(day_types):
                raise ValueError("'days_in_day_type' keys do not match day_types.")
        else:
            # TODO: check sum equals 1
            if day_types is not None:
                if len(day_types) > 1:
                    raise ValueError(
                        "days_in_day_type must be provided if providing more than one daytype"
                    )
            else:
                day_types = [1]

            days_in_day_type_df = pd.DataFrame(
                {
                    "SEASON": pd.Series(dtype="int32"),
                    "DAYTYPE": pd.Series(dtype="int32"),
                    "YEAR": pd.Series(dtype="int32"),
                    "VALUE": pd.Series(dtype="float64"),
                }
            )
            for season in seasons:
                days_in_day_type_df = pd.concat(
                    [
                        days_in_day_type_df,
                        pd.DataFrame(
                            {"SEASON": season, "DAYTYPE": 1, "YEAR": years, "VALUE": 7}
                        ),
                    ]
                )
            days_in_day_type = group_to_json(
                g=days_in_day_type_df,
                data_columns=["SEASON", "DAYTYPE", "YEAR"],
                target_column="VALUE",
            )

        if adj is None or adj_inv is None:
            year_adjacency = dict(zip(sorted(years)[:-1], sorted(years)[1:]))
            year_adjacency_inv = dict(zip(sorted(years)[1:], sorted(years)[:-1]))
            season_adjacency = dict(zip(sorted(seasons)[:-1], sorted(seasons)[1:]))
            season_adjacency_inv = dict(zip(sorted(seasons)[1:], sorted(seasons)[:-1]))
            day_type_adjacency = dict(
                zip(sorted(day_types)[:-1], sorted(day_types)[1:])
            )
            day_type_adjacency_inv = dict(
                zip(sorted(day_types)[1:], sorted(day_types)[:-1])
            )
            time_brackets_adjacency = dict(
                zip(sorted(daily_time_brackets)[:-1], sorted(daily_time_brackets)[1:])
            )
            time_brackets_adjacency_inv = dict(
                zip(sorted(daily_time_brackets)[1:], sorted(daily_time_brackets)[:-1])
            )

            adj = dict(
                years=year_adjacency,
                seasons=season_adjacency,
                day_types=day_type_adjacency,
                time_brackets=time_brackets_adjacency,
            )

            adj_inv = dict(
                years=year_adjacency_inv,
                seasons=season_adjacency_inv,
                day_types=day_type_adjacency_inv,
                time_brackets=time_brackets_adjacency_inv,
            )

        values["year_split"] = OSeMOSYSData(data=year_split)
        values["day_split"] = OSeMOSYSData(data=day_split)
        values["days_in_day_type"] = OSeMOSYSData(data=days_in_day_type)
        values["timeslice_in_timebracket"] = OSeMOSYSData(data=timeslice_in_timebracket)
        values["timeslice_in_daytype"] = OSeMOSYSData(data=timeslice_in_daytype)
        values["timeslice_in_season"] = OSeMOSYSData(data=timeslice_in_season)
        values["seasons"] = seasons
        values["timeslices"] = timeslices
        values["day_types"] = day_types
        values["daily_time_brackets"] = daily_time_brackets
        values["adj"] = adj
        values["adj_inv"] = adj_inv

        return values

    @classmethod
    def from_otoole_csv(cls, root_dir) -> "cls":
        """
        Instantiate a single TimeDefinition object containing all relevant data from otoole-organised csvs.

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
            raise FileNotFoundError(
                "YEAR.csv not read in, likely missing from root_dir"
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
