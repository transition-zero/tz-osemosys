from pathlib import Path
from typing import ClassVar, List, Union

import pandas as pd
from pydantic import BaseModel, conlist, root_validator

from feo.osemosys.schemas.validation.timedefinition_validation import timedefinition_validation
from feo.osemosys.utils import group_to_json

from .base import OSeMOSYSBase, OSeMOSYSData


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
    As well as the mode_of_operation set
    """

    # always required
    years: conlist(int, min_length=1)

    # can be constructed
    seasons: conlist(int | str, min_length=1)
    timeslices: conlist(int | str, min_length=1)
    day_types: conlist(int | str, min_length=1)
    daily_time_brackets: conlist(int | str, min_length=1)
    mode_of_operation: conlist(int, min_length=1)
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

    @root_validator(pre=True)
    def validation(cls, values):
        return timedefinition_validation(values)

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
