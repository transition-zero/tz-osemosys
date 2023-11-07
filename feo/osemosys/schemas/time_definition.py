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
    YEAR: dict[int, int]
    SEASON: dict[int, int]
    DAYTYPE: dict[int, int]
    time_brackets: dict[int, int]


class TimeDefinition(OSeMOSYSBase):
    """
    Class to contain all temporal information, including years and timeslices.
    """

    # always required
    YEAR: conlist(int, min_length=1)

    # can be constructed
    TIMESLICE: conlist(int | str, min_length=1)
    SEASON: conlist(int, min_length=1)
    DAYTYPE: conlist(int, min_length=1)
    DAILYTIMEBRACKET: conlist(int, min_length=1)
    YearSplit: OSeMOSYSData
    DaySplit: OSeMOSYSData
    DaysInDayType: OSeMOSYSData
    Conversionlh: OSeMOSYSData
    Conversionld: OSeMOSYSData
    Conversionls: OSeMOSYSData

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
        YEAR = values.get("YEAR")
        SEASON = values.get("SEASON")
        TIMESLICE = values.get("TIMESLICE")
        DAYTYPE = values.get("DAYTYPE")
        DAILYTIMEBRACKET = values.get("DAILYTIMEBRACKET")
        YearSplit = values.get("YearSplit")
        DaySplit = values.get("DaySplit")
        DaysInDayType = values.get("DaysInDayType")
        Conversionlh = values.get("Conversionlh")
        Conversionld = values.get("Conversionld")
        Conversionls = values.get("Conversionls")
        adj = values.get("adj")
        adj_inv = values.get("adj_inv")

        # failed to specify years
        if not YEAR:
            raise ValueError("YEAR (List[int]) must be specified.")

        # maybe get TIMESLICE from 'in' constructs or directly
        if TIMESLICE is not None:
            # make sure it's index matchs the 'in' constructs
            # timebrackets:
            if Conversionlh is not None:
                if set(TIMESLICE) != set(Conversionlh.keys()):
                    raise ValueError(
                        "provided 'TIMESLICE' do not match keys of 'Conversionlh'"
                    )
                if DAILYTIMEBRACKET is not None:
                    if set(DAILYTIMEBRACKET) != set(
                        flatten([list(v.keys()) for k, v in Conversionlh.items()])
                    ):
                        raise ValueError(
                            "provided 'Conversionlh' keys do not match 'DAILYTIMEBRACKET'"
                        )
            else:
                if DAILYTIMEBRACKET is not None:
                    raise ValueError(
                        "if providing 'TIMESLICE' and 'time_brackets', the joining 'Conversionlh' must be provided"
                    )
                # If TIMESLICE defined, but neither DAILYTIMEBRACKET nor Conversionlh is
                else:
                    for slice in TIMESLICE:
                        if "H2" in slice:
                            raise ValueError(
                                "More than one daily time bracket specified in TIMESLICE, DAILYTIMEBRACKET and Conversionlh must be provided"
                            )
                    # default to a single timebracket
                    DAILYTIMEBRACKET = [1]
                    #TODO: Add correct conversion default
                    Conversionlh = 1

            # daytype
            if Conversionld is not None:
                if set(TIMESLICE) != set(Conversionld.keys()):
                    raise ValueError(
                        "provided 'TIMESLICE' do not match keys of 'Conversionlh'"
                    )
                if Conversionld is not None:
                    if set(DAYTYPE) != set(
                        flatten([list(v.keys()) for k, v in Conversionld.items()])
                    ):
                        raise ValueError(
                            "provided 'Conversionlh' keys do not match 'DAYTYPE'"
                        )
            else:
                if DAYTYPE is not None:
                    raise ValueError(
                        "if providing 'TIMESLICE' and 'DAYTYPE', the joining 'Conversionld' must be provided"
                    )
                # If TIMESLICE defined, but neither DAYTYPE nor Conversionld is
                else:
                    for slice in TIMESLICE:
                        if "D2" in slice:
                            raise ValueError(
                                "More than one day type specified in TIMESLICE, DAYTYPE and Conversionld must be provided"
                            )
                    # default to a single daytype
                    DAYTYPE = [1]
                    #TODO: Add correct conversion default
                    Conversionld = 1

            # SEASON
            if Conversionls is not None:
                if set(TIMESLICE) != set(Conversionls.keys()):
                    raise ValueError(
                        "provided 'TIMESLICE' do not match keys of 'Conversionls'"
                    )
                if Conversionls is not None:
                    if set(SEASON) != set(
                        flatten([list(v.keys()) for k, v in Conversionls.items()])
                    ):
                        raise ValueError(
                            "provided 'Conversionls' keys do not match 'SEASON'"
                        )
            else:
                if SEASON is not None:
                    raise ValueError(
                        "if providing 'TIMESLICE' and 'SEASON', the joining 'Conversionls' must be provided"
                    )
                # If TIMESLICE defined, but neither SEASON nor Conversionls is
                else:
                    for slice in TIMESLICE:
                        if "S2" in slice:
                            raise ValueError(
                                "More than one season specified in TIMESLICE, SEASON and Conversionls must be provided"
                            )
                    # default to a single season
                    SEASON = [1]
                    #TODO: Add correct conversion default
                    Conversionls = 1

        else:
            # TIMESLICE not defined

            if Conversionld is not None:
                TIMESLICE = Conversionld.keys()
                if DAYTYPE is not None:
                    if set(DAYTYPE) != set(
                        flatten([list(v.keys()) for k, v in Conversionld.items()])
                    ):
                        raise ValueError(
                            "provided 'Conversionld' keys do not match 'DAYTYPE'"
                        )
                else:
                    DAYTYPE = sorted(
                        flatten([list(v.keys()) for k, v in Conversionld.items()])
                    )
            else:
                if DAYTYPE is None:
                    DAYTYPE = [1]

            if Conversionlh is not None:
                if TIMESLICE is None:
                    TIMESLICE = Conversionlh.keys()
                else:
                    if set(TIMESLICE) != set(Conversionlh.keys()):
                        raise ValueError(
                            "provided 'Conversionlh' keys do not match other timeslice joins."
                        )
                if DAILYTIMEBRACKET is not None:
                    if set(DAILYTIMEBRACKET) != set(
                        flatten([list(v.keys()) for k, v in Conversionlh.items()])
                    ):
                        raise ValueError(
                            "provided 'Conversionlh' keys do not match 'DAILYTIMEBRACKET'"
                        )
                else:
                    DAILYTIMEBRACKET = sorted(
                        flatten([list(v.keys()) for k, v in Conversionlh.items()])
                    )
            else:
                if DAILYTIMEBRACKET is None:
                    DAILYTIMEBRACKET = [1]

            if Conversionls is not None:
                if TIMESLICE is None:
                    TIMESLICE = Conversionls.keys()
                else:
                    if set(TIMESLICE) != set(Conversionls.keys()):
                        raise ValueError(
                            "provided 'Conversionls' keys do not match other timeslice joins."
                        )
                if SEASON is not None:
                    if set(SEASON) != set(
                        flatten([list(v.keys()) for k, v in Conversionls.items()])
                    ):
                        raise ValueError(
                            "provided 'Conversionls' keys do not match 'SEASON'"
                        )
                else:
                    SEASON = sorted(
                        flatten([list(v.keys()) for k, v in Conversionls.items()])
                    )
            else:
                if SEASON is None:
                    SEASON = [1]

        if TIMESLICE is None:
            # TIMESLICE is _still_ None: join our time_brackets, DAYTYPE, and SEASON
            # our timeslice_in_<object> constructs are also empty, let's build all

            Conversionls, Conversionld, Conversionlh = (
                makehash(),
                makehash(),
                makehash(),
            )
            TIMESLICE = []

            for season, day_type, time_bracket in product(SEASON, DAYTYPE, DAILYTIMEBRACKET):
                TIMESLICE.append(f"S{season}D{day_type}H{time_bracket}")
                Conversionls[f"S{season}D{day_type}H{time_bracket}"][season] = 1
                Conversionld[f"S{season}D{day_type}H{time_bracket}"][day_type] = 1
                Conversionlh[f"S{season}D{day_type}H{time_bracket}"][time_bracket] = 1

        # for these, check that they have the correct keys, or if they're None build from scratch
        if YearSplit is not None:
            if set(YearSplit.keys()) != set(TIMESLICE):
                raise ValueError("'YearSplit' keys do not match TIMESLICE.")
        else:
            # TODO: check equals 1
            YearSplit = 1 / len(TIMESLICE)

        if DaySplit is not None:
            if set(DaySplit.keys()) != set(DAILYTIMEBRACKET):
                raise ValueError("'DaySplit' keys do not match DAILYTIMEBRACKET.")
        else:
            # TODO: check equals 1
            DaySplit = 1 / len(DAILYTIMEBRACKET)

        if DaysInDayType is not None:
            if set(DaysInDayType.keys()) != set(DAYTYPE):
                raise ValueError("'DaysInDayType' keys do not match DAYTYPE.")
        else:
            # TODO: check equals 1
            DaysInDayType = 1 / len(DAYTYPE)

        if adj is None or adj_inv is None:
            year_adjacency = dict(zip(sorted(YEAR)[:-1], sorted(YEAR)[1:]))
            year_adjacency_inv = dict(zip(sorted(YEAR)[1:], sorted(YEAR)[:-1]))
            season_adjacency = dict(zip(sorted(SEASON)[:-1], sorted(SEASON)[1:]))
            season_adjacency_inv = dict(zip(sorted(SEASON)[1:], sorted(SEASON)[:-1]))
            day_type_adjacency = dict(zip(sorted(DAYTYPE)[:-1], sorted(DAYTYPE)[1:]))
            day_type_adjacency_inv = dict(zip(sorted(DAYTYPE)[1:], sorted(DAYTYPE)[:-1]))
            time_brackets_adjacency = dict(
                zip(sorted(DAILYTIMEBRACKET)[:-1], sorted(DAILYTIMEBRACKET)[1:])
            )
            time_brackets_adjacency_inv = dict(
                zip(sorted(DAILYTIMEBRACKET)[1:], sorted(DAILYTIMEBRACKET)[:-1])
            )

            adj = dict(
                YEAR=year_adjacency,
                SEASON=season_adjacency,
                DAYTYPE=day_type_adjacency,
                time_brackets=time_brackets_adjacency,
            )

            adj_inv = dict(
                YEAR=year_adjacency_inv,
                SEASON=season_adjacency_inv,
                DAYTYPE=day_type_adjacency_inv,
                time_brackets=time_brackets_adjacency_inv,
            )

        values["YearSplit"] = OSeMOSYSData(data=YearSplit)
        values["DaySplit"] = OSeMOSYSData(data=DaySplit)
        values["DaysInDayType"] = OSeMOSYSData(data=DaysInDayType)
        values["Conversionlh"] = OSeMOSYSData(data=Conversionlh)
        values["Conversionld"] = OSeMOSYSData(data=Conversionld)
        values["Conversionls"] = OSeMOSYSData(data=Conversionls)
        values["SEASON"] = SEASON
        values["TIMESLICE"] = TIMESLICE
        values["DAYTYPE"] = DAYTYPE
        values["DAILYTIMEBRACKET"] = DAILYTIMEBRACKET
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

        YEAR = dfs["YEAR"]["VALUE"].astype(str).values.tolist()
        SEASON = dfs["SEASON"]["VALUE"].values.tolist() if not dfs["SEASON"].empty else None
        DAYTYPE = dfs["DAYTYPE"]["VALUE"].values.tolist() if not dfs["DAYTYPE"].empty else None
        DAILYTIMEBRACKET = (
            dfs["DAILYTIMEBRACKET"]["VALUE"].values.tolist()
            if not dfs["DAILYTIMEBRACKET"].empty
            else None
        )
        TIMESLICE = (
            dfs["TIMESLICE"]["VALUE"].values.tolist() if not dfs["TIMESLICE"].empty else None
        )

        return cls(
            id="TimeDefinition",
            long_name=None,
            description=None,
            YEAR=YEAR,
            SEASON=SEASON,
            TIMESLICE=TIMESLICE,
            DAYTYPE=DAYTYPE,
            otoole_cfg=otoole_cfg,
            DAILYTIMEBRACKET=DAILYTIMEBRACKET,
            YearSplit=(
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
            DaySplit=(
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
            DaysInDayType=(
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
            Conversionld=(
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
            Conversionlh=(
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
            Conversionls=(
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
            {"VALUE": self.YEAR if self.YEAR is not None else []}
        ).to_csv(os.path.join(comparison_directory, "YEAR.csv"), index=False)
        pd.DataFrame(
            {"VALUE": self.SEASON if self.SEASON is not None else []}
        ).to_csv(os.path.join(comparison_directory, "SEASON.csv"), index=False)
        pd.DataFrame(
            {"VALUE": self.TIMESLICE if self.TIMESLICE is not None else []}
        ).to_csv(os.path.join(comparison_directory, "TIMESLICE.csv"), index=False)
        pd.DataFrame(
            {"VALUE": self.DAYTYPE if self.DAYTYPE is not None else []}
        ).to_csv(os.path.join(comparison_directory, "DAYTYPE.csv"), index=False)
        pd.DataFrame(
            {
                "VALUE": self.DAILYTIMEBRACKET
                if self.DAILYTIMEBRACKET is not None
                else []
            }
        ).to_csv(os.path.join(comparison_directory, "DAILYTIMEBRACKET.csv"), index=False)

        ### Write parameters to csv

        # YearSplit
        if self.YearSplit is not None:
            df_YearSplit = json_dict_to_dataframe(self.YearSplit.data)
            df_YearSplit.columns = ["TIMESLICE", "YEAR", "VALUE"]
            df_YearSplit.to_csv(os.path.join(comparison_directory, "YearSplit.csv"), index=False)
        else:
            pd.DataFrame(
                columns=["TIMESLICE", "YEAR", "VALUE"].to_csv(
                    os.path.join(comparison_directory, "YearSplit.csv"), index=False
                )
            )

        # DaySplit
        #TODO: use json_dict_to_dataframe() instead once constructed in correct format
        if "DaySplit" not in self.otoole_cfg.empty_dfs:
            df_DaySplit = (
                pd.DataFrame(self.DaySplit.data)
                .reset_index()
                .rename(columns={"index": "YEAR"})
                .melt(id_vars="YEAR", var_name="DAILYTIMEBRACKET", value_name="VALUE")[
                    ["DAILYTIMEBRACKET", "YEAR", "VALUE"]
                ]
            )
            df_DaySplit.to_csv(os.path.join(comparison_directory, "DaySplit.csv"), index=False)
        else:
            pd.DataFrame(columns=["DAILYTIMEBRACKET", "YEAR", "VALUE"]).to_csv(
                os.path.join(comparison_directory, "DaySplit.csv"), index=False
            )

        # DaysinDayType
        #TODO: convert check to is not None once in correct format after being constructed
        if "DaysInDayType" not in self.otoole_cfg.empty_dfs:
            df_DaysInDayType = json_dict_to_dataframe(self.DaysInDayType.data)
            df_DaysInDayType.columns = ["SEASON", "DAYTYPE", "YEAR", "VALUE"]
            df_DaysInDayType.to_csv(
                os.path.join(comparison_directory, "DaysInDayType.csv"), index=False
            )
        else:
            pd.DataFrame(columns=["SEASON", "DAYTYPE", "YEAR", "VALUE"]).to_csv(
                os.path.join(comparison_directory, "DaysInDayType.csv"), index=False
            )

        # Conversionld
        if self.Conversionld is not None:
            df_conversion_ld = json_dict_to_dataframe(self.Conversionld.data)
            df_conversion_ld.columns = ["TIMESLICE", "DAYTYPE", "VALUE"]
            df_conversion_ld.to_csv(
                os.path.join(comparison_directory, "Conversionld.csv"), index=False
            )
        else:
            pd.DataFrame(columns=["TIMESLICE", "DAYTYPE", "VALUE"]).to_csv(
                os.path.join(comparison_directory, "Conversionld.csv"), index=False
            )

        # Conversionlh
        #TODO: convert check to is not None once in correct format after being constructed
        if "Conversionlh" not in self.otoole_cfg.empty_dfs:
            df_conversion_lh = json_dict_to_dataframe(self.Conversionlh.data)
            df_conversion_lh.columns = ["TIMESLICE", "DAILYTIMEBRACKET", "VALUE"]
            df_conversion_lh.to_csv(
                os.path.join(comparison_directory, "Conversionlh.csv"), index=False
            )
        else:
            pd.DataFrame(columns=["TIMESLICE", "DAILYTIMEBRACKET", "VALUE"]).to_csv(
                os.path.join(comparison_directory, "Conversionlh.csv"), index=False
            )

        # Conversionls
        if self.Conversionls is not None:
            df_conversion_ls = json_dict_to_dataframe(self.Conversionls.data)
            df_conversion_ls.columns = ["TIMESLICE", "SEASON", "VALUE"]
            df_conversion_ls.to_csv(
                os.path.join(comparison_directory, "Conversionls.csv"), index=False
            )
        else:
            pd.DataFrame(columns=["TIMESLICE", "SEASON", "VALUE"]).to_csv(
                os.path.join(comparison_directory, "Conversionls.csv"), index=False
            )
