from itertools import product
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Union

import pandas as pd
from pydantic import BaseModel, Field

from tz.osemosys.schemas.compat.base import OtooleCfg

if TYPE_CHECKING:
    from tz.osemosys.schemas.time_definition import TimeDefinition


class OtooleTimeDefinition(BaseModel):
    """
    Class to contain methods for converting TimeDefinition data to and from otoole style CSVs
    """

    otoole_cfg: OtooleCfg | None = Field(default=None)
    otoole_stems: ClassVar[dict[str : dict[str : Union[str, list[str]]]]] = {
        "YEAR": {"attribute": "years", "columns": ["VALUE"]},
        "SEASON": {"attribute": "seasons", "columns": ["VALUE"]},
        "TIMESLICE": {"attribute": "timeslices", "columns": ["VALUE"]},
        "DAYTYPE": {"attribute": "day_types", "columns": ["VALUE"]},
        "DAILYTIMEBRACKET": {"attribute": "daily_time_brackets", "columns": ["VALUE"]},
        "YearSplit": {
            "attribute": "year_split",
            "columns": ["TIMESLICE", "YEAR", "VALUE"],
        },
        "DaySplit": {
            "attribute": "day_split",
            "columns": ["DAILYTIMEBRACKET", "YEAR", "VALUE"],
        },
        "DaysInDayType": {
            "attribute": "days_in_day_type",
            "columns": ["SEASON", "DAYTYPE", "YEAR", "VALUE"],
        },
        "Conversionlh": {
            "attribute": "timeslice_in_timebracket",
            "columns": ["TIMESLICE", "DAILYTIMEBRACKET", "VALUE"],
        },
        "Conversionld": {
            "attribute": "timeslice_in_daytype",
            "columns": ["TIMESLICE", "DAYTYPE", "VALUE"],
        },
        "Conversionls": {
            "attribute": "timeslice_in_season",
            "columns": ["TIMESLICE", "SEASON", "VALUE"],
        },
    }

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

        if "YearSplit" not in otoole_cfg.empty_dfs:
            # check there are not different splits in different years
            if (dfs["YearSplit"].groupby("TIMESLICE").nunique()["VALUE"] > 1).any():
                raise ValueError("YearSplit must be consistent across years")

            year_split = (
                dfs["YearSplit"]
                .groupby(["TIMESLICE"])
                .nth(0)
                .set_index("TIMESLICE")["VALUE"]
                .to_dict()
            )
        else:
            year_split = None
        if "DaySplit" not in otoole_cfg.empty_dfs:
            # check there are not different splits in different years
            if (dfs["DaySplit"].groupby("DAILYTIMEBRACKET").nunique()["VALUE"] > 1).any():
                raise ValueError("DaySplit must be consistent across years")

            dfs["DaySplit"]["DAILYTIMEBRACKET"] = dfs["DaySplit"]["DAILYTIMEBRACKET"].astype(str)

            day_split = (
                dfs["DaySplit"]
                .groupby(["DAILYTIMEBRACKET"])
                .nth(0)
                .set_index("DAILYTIMEBRACKET")["VALUE"]
                .to_dict()
            )
        else:
            day_split = None

        if "Conversionld" not in otoole_cfg.empty_dfs:
            timeslice_in_daytype = (
                dfs["Conversionld"]
                .loc[dfs["Conversionld"]["VALUE"] == 1, ["TIMESLICE", "DAYTYPE"]]
                .set_index("TIMESLICE")["DAYTYPE"]
                .astype(str)
                .to_dict()
            )
        else:
            timeslice_in_daytype = None
        if "Conversionls" not in otoole_cfg.empty_dfs:
            timeslice_in_season = (
                dfs["Conversionls"]
                .loc[dfs["Conversionls"]["VALUE"] == 1, ["TIMESLICE", "SEASON"]]
                .set_index("TIMESLICE")["SEASON"]
                .astype(str)
                .to_dict()
            )
        else:
            timeslice_in_season = None
        if "Conversionlh" not in otoole_cfg.empty_dfs:
            timeslice_in_timebracket = (
                dfs["Conversionlh"]
                .loc[dfs["Conversionlh"]["VALUE"] == 1, ["TIMESLICE", "DAILYTIMEBRACKET"]]
                .set_index("TIMESLICE")["DAILYTIMEBRACKET"]
                .astype(str)
                .to_dict()
            )
        else:
            timeslice_in_timebracket = None

        if "DaysInDayType" not in otoole_cfg.empty_dfs:
            # check if there are different numbers of daytypes in different seasons or years
            if (dfs["DaysInDayType"].groupby("DAYTYPE").nunique()["VALUE"] > 1).any():
                raise ValueError("Different number of daytypes in seasons or years")

            days_in_day_type = (
                dfs["DaysInDayType"].groupby("DAYTYPE").nth(0).set_index("DAYTYPE")["VALUE"]
            )
            days_in_day_type.index = days_in_day_type.index.astype(str)
            days_in_day_type = days_in_day_type.to_dict()
        else:
            days_in_day_type = None

        return cls(
            id=Path(root_dir).name,
            years=years,
            seasons=seasons,
            timeslices=timeslices,
            day_types=day_types,
            otoole_cfg=otoole_cfg,
            daily_time_brackets=daily_time_brackets,
            year_split=year_split,
            day_split=day_split,
            days_in_day_type=days_in_day_type,
            timeslice_in_daytype=timeslice_in_daytype,
            timeslice_in_timebracket=timeslice_in_timebracket,
            timeslice_in_season=timeslice_in_season,
        )

    def _to_dataframe(self, stem: str) -> pd.DataFrame:
        if stem == "YEAR":
            return pd.DataFrame(data={"VALUE": sorted(self.years)})
        elif stem == "SEASON":
            return pd.DataFrame(data={"VALUE": self.seasons or []}, columns=["VALUE"])
        elif stem == "TIMESLICE":
            return pd.DataFrame(data={"VALUE": sorted(self.timeslices)}, columns=["VALUE"])
        elif stem == "DAILYTIMEBRACKET":
            return pd.DataFrame(data={"VALUE": self.daily_time_brackets or []}, columns=["VALUE"])
        elif stem == "DAYTYPE":
            return pd.DataFrame(data={"VALUE": self.day_types or []}, columns=["VALUE"])
        elif stem == "DaysInDayType":
            return (
                pd.DataFrame.from_records(
                    [
                        {
                            "SEASON": season,
                            "DAYTYPE": daytype,
                            "YEAR": year,
                            "VALUE": self.days_in_day_type[daytype],
                        }
                        for season, daytype, year in product(
                            self.seasons, list(self.days_in_day_type.keys()), self.years
                        )
                    ]
                )
                if self.days_in_day_type is not None
                else pd.DataFrame(columns=["SEASON", "DAYTYPE", "YEAR", "VALUE"])
            )
        elif stem == "YearSplit":
            return pd.DataFrame.from_records(
                [
                    {"TIMESLICE": ts, "YEAR": year, "VALUE": self.year_split[ts]}
                    for ts, year in product(list(self.year_split.keys()), self.years)
                ]
            )
        elif stem == "DaySplit":
            return (
                pd.DataFrame.from_records(
                    [
                        {
                            "DAILYTIMEBRACKET": dtb,
                            "YEAR": year,
                            "VALUE": self.day_split[dtb],
                        }
                        for dtb, year in product(self.daily_time_brackets, self.years)
                    ]
                )
                if self.daily_time_brackets is not None
                else pd.DataFrame(columns=["DAILYTIMEBRACKET", "YEAR", "VALUE"])
            )
        elif stem == "Conversionld":
            return (
                pd.DataFrame.from_records(
                    [
                        {
                            "TIMESLICE": timeslice,
                            "DAYTYPE": daytype,
                            "VALUE": 1,
                        }
                        for timeslice, daytype in self.timeslice_in_daytype.items()
                    ]
                )
                if self.timeslice_in_daytype is not None
                else pd.DataFrame(columns=["TIMESLICE", "DAYTYPE", "VALUE"])
            )
        elif stem == "Conversionls":
            return (
                pd.DataFrame.from_records(
                    [
                        {
                            "TIMESLICE": timeslice,
                            "SEASON": season,
                            "VALUE": 1,
                        }
                        for timeslice, season in self.timeslice_in_season.items()
                    ]
                )
                if self.timeslice_in_season is not None
                else pd.DataFrame(columns=["TIMESLICE", "SEASON", "VALUE"])
            )
        elif stem == "Conversionlh":
            return (
                pd.DataFrame.from_records(
                    [
                        {
                            "TIMESLICE": timeslice,
                            "DAILYTIMEBRACKET": dtb,
                            "VALUE": 1,
                        }
                        for timeslice, dtb in self.timeslice_in_timebracket.items()
                    ]
                )
                if self.timeslice_in_timebracket is not None
                else pd.DataFrame(columns=["TIMESLICE", "DAILYTIMEBRACKET", "VALUE"])
            )
        else:
            raise ValueError(f"no otoole compatibility method for '{stem}'")

    def to_dataframes(self):
        dfs = {}
        for stem, _params in self.otoole_stems.items():
            dfs[stem] = self._to_dataframe(stem)

        return dfs

    def to_otoole_csv(self, output_directory):
        for stem, _params in self.otoole_stems.items():
            if stem not in self.otoole_cfg.empty_dfs:
                self._to_dataframe(stem).to_csv(Path(output_directory) / f"{stem}.csv", index=False)
