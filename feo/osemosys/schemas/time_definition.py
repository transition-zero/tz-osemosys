import os
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
    timeslices: conlist(int | str, min_length=1)
    seasons: conlist(int, min_length=1)
    day_types: conlist(int, min_length=1)
    daily_time_brackets: conlist(int, min_length=1)
    year_split: OSeMOSYSData
    day_split: OSeMOSYSData
    days_in_day_type: OSeMOSYSData
    timeslice_in_timebracket: OSeMOSYSData
    timeslice_in_daytype: OSeMOSYSData
    timeslice_in_season: OSeMOSYSData

    adj: TimeAdjacency
    adj_inv: TimeAdjacency

    otoole_cfg: OtooleCfg | None
    otoole_stems: ClassVar[list[str]] = [
        "YEAR",
        "SEASON",
        "TIMESLICE",
        "DAYTYPE",
        "DAILYTIMEBRACKET",
        "YearSplit",
        "DaySplit",
        "DaysInDayType",
        "Conversionld",
        "Conversionlh",
        "Conversionls",
    ]

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
            raise ValueError("Years (List[int]) must be specified.")

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
                        flatten([list(v.keys()) for k, v in timeslice_in_timebracket.items()])
                    ):
                        raise ValueError(
                            "provided 'timeslice_in_timebracket' keys do not match 'daily_time_brackets'"
                        )
            else:
                if daily_time_brackets is not None:
                    raise ValueError(
                        "if providing 'timeslices' and 'time_brackets', the joining 'timeslice_in_timebracket' must be provided"
                    )
                else:
                    # default to a single timebracket
                    daily_time_brackets = [1]
                    timeslice_in_timebracket = 1

            # daytype
            if timeslice_in_daytype is not None:
                if set(timeslices) != set(timeslice_in_daytype.keys()):
                    raise ValueError(
                        "provided 'timeslices' do not match keys of 'timeslice_in_timebracket'"
                    )
                if timeslice_in_daytype is not None:
                    if set(day_types) != set(
                        flatten([list(v.keys()) for k, v in timeslice_in_daytype.items()])
                    ):
                        raise ValueError(
                            "provided 'timeslice_in_timebracket' keys do not match 'day_types'"
                        )
            else:
                if day_types is not None:
                    raise ValueError(
                        "if providing 'timeslices' and 'day_types', the joining 'timeslice_in_daytype' must be provided"
                    )
                else:
                    # default to a single daytype
                    day_types = [1]
                    timeslice_in_daytype = 1

            # seasons
            if timeslice_in_season is not None:
                if set(timeslices) != set(timeslice_in_season.keys()):
                    raise ValueError(
                        "provided 'timeslices' do not match keys of 'timeslice_in_season'"
                    )
                if timeslice_in_season is not None:
                    if set(seasons) != set(
                        flatten([list(v.keys()) for k, v in timeslice_in_season.items()])
                    ):
                        raise ValueError(
                            "provided 'timeslice_in_season' keys do not match 'seasons'"
                        )
            else:
                if seasons is not None:
                    raise ValueError(
                        "if providing 'timeslices' and 'seasons', the joining 'timeslice_in_season' must be provided"
                    )
                else:
                    # default to a single season
                    seasons = [1]
                    timeslice_in_season = 1

        else:
            # timeslices not defined

            if timeslice_in_daytype is not None:
                timeslices = timeslice_in_daytype.keys()
                if day_types is not None:
                    if set(day_types) != set(
                        flatten([list(v.keys()) for k, v in timeslice_in_daytype.items()])
                    ):
                        raise ValueError(
                            "provided 'timeslice_in_daytype' keys do not match 'day_types'"
                        )
                else:
                    day_types = sorted(
                        flatten([list(v.keys()) for k, v in timeslice_in_daytype.items()])
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
                        flatten([list(v.keys()) for k, v in timeslice_in_timebracket.items()])
                    ):
                        raise ValueError(
                            "provided 'timeslice_in_timebracket' keys do not match 'daily_time_brackets'"
                        )
                else:
                    daily_time_brackets = sorted(
                        flatten([list(v.keys()) for k, v in timeslice_in_timebracket.items()])
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
                        flatten([list(v.keys()) for k, v in timeslice_in_season.items()])
                    ):
                        raise ValueError(
                            "provided 'timeslice_in_season' keys do not match 'seasons'"
                        )
                else:
                    seasons = sorted(
                        flatten([list(v.keys()) for k, v in timeslice_in_season.items()])
                    )
            else:
                if seasons is None:
                    seasons = [1]

        if timeslices is None:
            # timeslices is _still_ None: join our time_brackets, day_types, and seasons
            # our timeslice_in_<object> constructs are also empty, let's build all

            timeslice_in_season, timeslice_in_daytype, timeslice_in_timebracket = (
                makehash(),
                makehash(),
                makehash(),
            )
            timeslices = []

            for season, day_type, time_bracket in product(seasons, day_types, daily_time_brackets):
                timeslices.append(f"S{season}D{day_type}H{time_bracket}")
                timeslice_in_season[f"S{season}D{day_type}H{time_bracket}"][season] = 1
                timeslice_in_daytype[f"S{season}D{day_type}H{time_bracket}"][day_type] = 1
                timeslice_in_timebracket[f"S{season}D{day_type}H{time_bracket}"][time_bracket] = 1

        # for these, check that they have the correct keys, or if they're None build from scratch
        if year_split is not None:
            if set(year_split.keys()) != set(timeslices):
                raise ValueError("'year_split' keys do not match timeslices.")
        else:
            # TODO: check equals 1
            year_split = 1 / len(timeslices)

        if day_split is not None:
            if set(day_split.keys()) != set(daily_time_brackets):
                raise ValueError("'day_split' keys do not match daily_time_brackets.")
        else:
            # TODO: check equals 1
            day_split = 1 / len(daily_time_brackets)

        if days_in_day_type is not None:
            if set(days_in_day_type.keys()) != set(day_types):
                raise ValueError("'days_in_day_type' keys do not match day_types.")
        else:
            # TODO: check equals 1
            days_in_day_type = 1 / len(day_types)

        if adj is None or adj_inv is None:
            year_adjacency = dict(zip(sorted(years)[:-1], sorted(years)[1:]))
            year_adjacency_inv = dict(zip(sorted(years)[1:], sorted(years)[:-1]))
            season_adjacency = dict(zip(sorted(seasons)[:-1], sorted(seasons)[1:]))
            season_adjacency_inv = dict(zip(sorted(seasons)[1:], sorted(seasons)[:-1]))
            day_type_adjacency = dict(zip(sorted(day_types)[:-1], sorted(day_types)[1:]))
            day_type_adjacency_inv = dict(zip(sorted(day_types)[1:], sorted(day_types)[:-1]))
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
        for key in cls.otoole_stems:
            dfs[key] = pd.read_csv(Path(root_dir) / f"{key}.csv")
            if dfs[key].empty:
                otoole_cfg.empty_dfs.append(key)

        # ###################
        # Basic Data Checks #
        #####################

        # Assert days in day type values <=7
        assert (
            dfs["DaysInDayType"]["VALUE"].isin([1, 2, 3, 4, 5, 6, 7]).all()
        ), "Days in day type can only take values from 1-7"

        years = dfs["YEAR"]["VALUE"].astype(str).values.tolist()
        seasons = dfs["SEASON"]["VALUE"].values.tolist() if not dfs["SEASON"].empty else None
        day_types = dfs["DAYTYPE"]["VALUE"].values.tolist() if not dfs["DAYTYPE"].empty else None
        daily_time_brackets = (
            dfs["DAILYTIMEBRACKET"]["VALUE"].values.tolist()
            if not dfs["DAILYTIMEBRACKET"].empty
            else None
        )
        timeslices = (
            dfs["TIMESLICE"]["VALUE"].values.tolist() if not dfs["TIMESLICE"].empty else None
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
                StringYearData(
                    data=group_to_json(
                        g=dfs["YearSplit"],
                        data_columns=["TIMESLICE", "YEAR"],
                        target_column="VALUE",
                    )
                ).model_dump()["data"]
                if not dfs["YearSplit"].empty
                else None
            ),
            day_split=(
                IntYearData(
                    data=group_to_json(
                        g=dfs["DaySplit"],
                        data_columns=["DAILYTIMEBRACKET", "YEAR"],
                        target_column="VALUE",
                    )
                ).model_dump()["data"]
                if not dfs["DaySplit"].empty
                else None
            ),
            days_in_day_type=(
                IntIntIntData(
                    data=group_to_json(
                        g=dfs["DaysInDayType"],
                        data_columns=["SEASON", "DAYTYPE", "YEAR"],
                        target_column="VALUE",
                    )
                ).model_dump()["data"]
                if not dfs["DaysInDayType"].empty
                else None
            ),
            timeslice_in_daytype=(
                StringYearData(
                    data=group_to_json(
                        g=dfs["Conversionld"],
                        data_columns=["TIMESLICE", "DAYTYPE"],
                        target_column="VALUE",
                    )
                ).model_dump()["data"]
                if not dfs["Conversionld"].empty
                else None
            ),
            timeslice_in_timebracket=(
                StringYearData(
                    data=group_to_json(
                        g=dfs["Conversionlh"],
                        data_columns=["TIMESLICE", "DAILYTIMEBRACKET"],
                        target_column="VALUE",
                    )
                ).model_dump()["data"]
                if not dfs["Conversionlh"].empty
                else None
            ),
            timeslice_in_season=(
                StringYearData(
                    data=group_to_json(
                        g=dfs["Conversionls"],
                        data_columns=["TIMESLICE", "SEASON"],
                        target_column="VALUE",
                    )
                ).model_dump()["data"]
                if not dfs["Conversionls"].empty
                else None
            ),
        )

    def to_otoole_csv(self, comparison_directory) -> None:
        ### Write sets to csv

        pd.DataFrame(
            {"VALUE": self.years if "YEAR" not in self.otoole_cfg.empty_dfs else []}
        ).to_csv(os.path.join(comparison_directory, "YEAR.csv"), index=False)
        pd.DataFrame(
            {"VALUE": self.seasons if "SEASON" not in self.otoole_cfg.empty_dfs else []}
        ).to_csv(os.path.join(comparison_directory, "SEASON.csv"), index=False)
        pd.DataFrame(
            {"VALUE": self.timeslices if "TIMESLICE" not in self.otoole_cfg.empty_dfs else []}
        ).to_csv(os.path.join(comparison_directory, "TIMESLICE.csv"), index=False)
        pd.DataFrame(
            {"VALUE": self.day_types if "DAYTYPE" not in self.otoole_cfg.empty_dfs else []}
        ).to_csv(os.path.join(comparison_directory, "DAYTYPE.csv"), index=False)
        pd.DataFrame(
            {
                "VALUE": self.daily_time_brackets
                if "DAILYTIMEBRACKET" not in self.otoole_cfg.empty_dfs
                else []
            }
        ).to_csv(os.path.join(comparison_directory, "DAILYTIMEBRACKET.csv"), index=False)

        ### Write parameters to csv

        # YearSplit
        if "YearSplit" not in self.otoole_cfg.empty_dfs:
            df_year_split = (
                pd.DataFrame(self.year_split.data)
                .reset_index()
                .rename(columns={"index": "YEAR"})
                .melt(id_vars="YEAR", var_name="TIMESLICE", value_name="VALUE")[
                    ["TIMESLICE", "YEAR", "VALUE"]
                ]
            )
            df_year_split.to_csv(os.path.join(comparison_directory, "YearSplit.csv"), index=False)
        else:
            pd.DataFrame(
                columns=["TIMESLICE", "YEAR", "VALUE"].to_csv(
                    os.path.join(comparison_directory, "YearSplit.csv"), index=False
                )
            )

        # DaySplit
        if "DaySplit" not in self.otoole_cfg.empty_dfs:
            df_day_split = (
                pd.DataFrame(self.day_split.data)
                .reset_index()
                .rename(columns={"index": "YEAR"})
                .melt(id_vars="YEAR", var_name="DAILYTIMEBRACKET", value_name="VALUE")[
                    ["DAILYTIMEBRACKET", "YEAR", "VALUE"]
                ]
            )
            df_day_split.to_csv(os.path.join(comparison_directory, "DaySplit.csv"), index=False)
        else:
            pd.DataFrame(columns=["DAILYTIMEBRACKET", "YEAR", "VALUE"]).to_csv(
                os.path.join(comparison_directory, "DaySplit.csv"), index=False
            )

        # DaysinDayType
        if "DaysInDayType" not in self.otoole_cfg.empty_dfs:
            df_days_in_day_type = json_dict_to_dataframe(self.days_in_day_type.data)
            df_days_in_day_type.columns = ["SEASON", "DAYTYPE", "YEAR", "VALUE"]
            df_days_in_day_type.to_csv(
                os.path.join(comparison_directory, "DaysInDayType.csv"), index=False
            )
        else:
            pd.DataFrame(columns=["SEASON", "DAYTYPE", "YEAR", "VALUE"]).to_csv(
                os.path.join(comparison_directory, "DaysInDayType.csv"), index=False
            )

        # Conversionld
        if "Conversionld" not in self.otoole_cfg.empty_dfs:
            df_conversion_ld = (
                pd.DataFrame(self.timeslice_in_daytype.data)
                .reset_index()
                .rename(columns={"index": "DAYTYPE"})
                .melt(id_vars="DAYTYPE", var_name="TIMESLICE", value_name="VALUE")[
                    ["TIMESLICE", "DAYTYPE", "VALUE"]
                ]
            )
            df_conversion_ld.to_csv(
                os.path.join(comparison_directory, "Conversionld.csv"), index=False
            )
        else:
            pd.DataFrame(columns=["TIMESLICE", "DAYTYPE", "VALUE"]).to_csv(
                os.path.join(comparison_directory, "Conversionld.csv"), index=False
            )

        # Conversionlh
        if "Conversionlh" not in self.otoole_cfg.empty_dfs:
            df_conversion_lh = (
                pd.DataFrame(self.timeslice_in_timebracket.data)
                .reset_index()
                .rename(columns={"index": "DAILYTIMEBRACKET"})
                .melt(id_vars="DAILYTIMEBRACKET", var_name="TIMESLICE", value_name="VALUE")[
                    ["TIMESLICE", "DAILYTIMEBRACKET", "VALUE"]
                ]
            )
            df_conversion_lh.to_csv(
                os.path.join(comparison_directory, "Conversionlh.csv"), index=False
            )
        else:
            pd.DataFrame(columns=["TIMESLICE", "DAILYTIMEBRACKET", "VALUE"]).to_csv(
                os.path.join(comparison_directory, "Conversionlh.csv"), index=False
            )

        # Conversionls
        if "Conversionls" not in self.otoole_cfg.empty_dfs:
            df_conversion_ls = (
                pd.DataFrame(self.timeslice_in_season.data)
                .reset_index()
                .rename(columns={"index": "SEASON"})
                .melt(id_vars="SEASON", var_name="TIMESLICE", value_name="VALUE")[
                    ["TIMESLICE", "SEASON", "VALUE"]
                ]
            )
            df_conversion_ls.to_csv(
                os.path.join(comparison_directory, "Conversionls.csv"), index=False
            )
        else:
            pd.DataFrame(columns=["TIMESLICE", "SEASON", "VALUE"]).to_csv(
                os.path.join(comparison_directory, "Conversionls.csv"), index=False
            )
