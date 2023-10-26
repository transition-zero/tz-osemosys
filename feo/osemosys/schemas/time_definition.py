import os

import pandas as pd

from feo.osemosys.utils import *

from .base import *


class TimeDefinition(OSeMOSYSBase):
    """
    Class to contain all temporal information, including years and timeslices.
    """

    # Sets
    years: List[int]
    season: List[int]
    timeslice: List[str]
    day_type: List[int]
    daily_time_bracket: List[int]
    # Parameters
    year_split: StringYearData | None
    day_split: IntYearData | None
    days_in_day_type: IntIntIntData | None
    conversion_ld: StringYearData | None
    conversion_lh: StringYearData | None
    conversion_ls: StringYearData | None

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
        # Sets
        df_years = pd.read_csv(os.path.join(root_dir, "YEAR.csv"))
        df_season = pd.read_csv(os.path.join(root_dir, "SEASON.csv"))
        df_timeslice = pd.read_csv(os.path.join(root_dir, "TIMESLICE.csv"))
        df_day_type = pd.read_csv(os.path.join(root_dir, "DAYTYPE.csv"))
        df_daily_time_bracket = pd.read_csv(os.path.join(root_dir, "DAILYTIMEBRACKET.csv"))

        # Parameters
        df_year_split = pd.read_csv(os.path.join(root_dir, "YearSplit.csv"))
        df_day_split = pd.read_csv(os.path.join(root_dir, "DaySplit.csv"))
        df_days_in_day_type = pd.read_csv(os.path.join(root_dir, "DaysInDayType.csv"))
        df_conversion_ld = pd.read_csv(os.path.join(root_dir, "Conversionld.csv"))
        df_conversion_lh = pd.read_csv(os.path.join(root_dir, "Conversionlh.csv"))
        df_conversion_ls = pd.read_csv(os.path.join(root_dir, "Conversionls.csv"))

        # Assert days in day type values <=7
        assert (
            df_days_in_day_type["VALUE"].isin([1, 2, 3, 4, 5, 6, 7]).all()
        ), "Days in day type can only take values from 1-7"

        return cls(
            id="TimeDefinition",
            # TODO
            long_name=None,
            description=None,
            # Sets
            years=df_years["VALUE"].values.tolist(),
            season=df_season["VALUE"].values.tolist(),
            timeslice=df_timeslice["VALUE"].values.tolist(),
            day_type=df_day_type["VALUE"].values.tolist(),
            daily_time_bracket=df_daily_time_bracket["VALUE"].values.tolist(),
            # Parameters
            year_split=(
                StringYearData(
                    data=group_to_json(
                        g=df_year_split,
                        data_columns=["TIMESLICE", "YEAR"],
                        target_column="VALUE",
                    )
                )
                if not df_year_split.empty
                else None
            ),
            day_split=(
                IntYearData(
                    data=group_to_json(
                        g=df_day_split,
                        data_columns=["DAILYTIMEBRACKET", "YEAR"],
                        target_column="VALUE",
                    )
                )
                if not df_day_split.empty
                else None
            ),
            days_in_day_type=(
                IntIntIntData(
                    data=group_to_json(
                        g=df_days_in_day_type,
                        data_columns=["SEASON", "DAYTYPE", "YEAR"],
                        target_column="VALUE",
                    )
                )
                if not df_days_in_day_type.empty
                else None
            ),
            conversion_ld=(
                StringYearData(
                    data=group_to_json(
                        g=df_conversion_ld,
                        data_columns=["TIMESLICE", "DAYTYPE"],
                        target_column="VALUE",
                    )
                )
                if not df_conversion_ld.empty
                else None
            ),
            conversion_lh=(
                StringYearData(
                    data=group_to_json(
                        g=df_conversion_lh,
                        data_columns=["TIMESLICE", "DAILYTIMEBRACKET"],
                        target_column="VALUE",
                    )
                )
                if not df_conversion_lh.empty
                else None
            ),
            conversion_ls=(
                StringYearData(
                    data=group_to_json(
                        g=df_conversion_ls,
                        data_columns=["TIMESLICE", "SEASON"],
                        target_column="VALUE",
                    )
                )
                if not df_conversion_ls.empty
                else None
            ),
        )

    def to_otoole_csv(self, comparison_directory) -> "cls":
        ### Write sets to csv

        pd.DataFrame({"VALUE": self.years}).to_csv(
            os.path.join(comparison_directory, "YEAR.csv"), index=False
        )
        pd.DataFrame({"VALUE": self.season}).to_csv(
            os.path.join(comparison_directory, "SEASON.csv"), index=False
        )
        pd.DataFrame({"VALUE": self.timeslice}).to_csv(
            os.path.join(comparison_directory, "TIMESLICE.csv"), index=False
        )
        pd.DataFrame({"VALUE": self.day_type}).to_csv(
            os.path.join(comparison_directory, "DAYTYPE.csv"), index=False
        )
        pd.DataFrame({"VALUE": self.daily_time_bracket}).to_csv(
            os.path.join(comparison_directory, "DAILYTIMEBRACKET.csv"), index=False
        )

        ### Write parameters to csv

        # YearSplit
        if self.year_split is not None:
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
        if self.day_split is not None:
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
        if self.days_in_day_type is not None:
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
        if self.conversion_ld is not None:
            df_conversion_ld = (
                pd.DataFrame(self.conversion_ld.data)
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
        if self.conversion_lh is not None:
            df_conversion_lh = (
                pd.DataFrame(self.conversion_lh.data)
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
        if self.conversion_ls is not None:
            df_conversion_ls = (
                pd.DataFrame(self.conversion_ls.data)
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
