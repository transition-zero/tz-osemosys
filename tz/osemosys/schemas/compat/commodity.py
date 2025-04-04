import os
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, List, Union

import pandas as pd
from pydantic import BaseModel, Field

from tz.osemosys.schemas.base import OSeMOSYSData
from tz.osemosys.schemas.compat.base import OtooleCfg
from tz.osemosys.utils import group_to_json

if TYPE_CHECKING:
    from tz.osemosys.schemas.commodity import Commodity


class OtooleCommodity(BaseModel):
    """
    Class to contain methods for converting Commodity data to and from otoole style CSVs
    """

    otoole_cfg: OtooleCfg | None = Field(None)
    otoole_stems: ClassVar[dict[str : dict[str : Union[str, list[str]]]]] = {
        "SpecifiedAnnualDemand": {
            "attribute": "demand_annual",
            "columns": ["REGION", "FUEL", "YEAR", "VALUE"],
        },
        "SpecifiedDemandProfile": {
            "attribute": "demand_profile",
            "columns": ["REGION", "FUEL", "TIMESLICE", "YEAR", "VALUE"],
        },
        "AccumulatedAnnualDemand": {
            "attribute": "accumulated_demand",
            "columns": ["REGION", "FUEL", "YEAR", "VALUE"],
        },
        "RETagFuel": {
            "attribute": "include_in_joint_renewable_target",
            "columns": ["REGION", "FUEL", "YEAR", "VALUE"],
        },
    }

    @classmethod
    def from_otoole_csv(cls, root_dir):
        # ###########
        # Load Data #
        # ###########

        df_commodity = pd.read_csv(os.path.join(root_dir, "FUEL.csv"))

        dfs = {}
        otoole_cfg = OtooleCfg(empty_dfs=[])
        for key in list(cls.otoole_stems):
            try:
                dfs[key] = pd.read_csv(Path(root_dir) / f"{key}.csv")
                if dfs[key].empty:
                    otoole_cfg.empty_dfs.append(key)
            except FileNotFoundError:
                otoole_cfg.empty_dfs.append(key)
                dfs[key] = pd.DataFrame(columns=["FUEL"])

        # ###################
        # Basic Data Checks #
        #####################

        # Check no duplicates in FUEL.csv
        if len(df_commodity) != len(df_commodity["VALUE"].unique()):
            raise ValueError("FUEL.csv must not contain duplicate values")

        # Check impact names are consistent with those in FUEL.csv
        for df in dfs.keys():
            for commodity in dfs[df]["FUEL"].unique():
                if commodity not in list(df_commodity["VALUE"]):
                    raise ValueError(f"{commodity} given in {df}.csv but not in FUEL.csv")

        # ########################
        # Define class instances #
        # ########################

        commodity_instances = []
        for commodity in df_commodity["VALUE"].values.tolist():
            demand_annual = (
                OSeMOSYSData.RY(
                    group_to_json(
                        g=dfs["SpecifiedAnnualDemand"].loc[
                            dfs["SpecifiedAnnualDemand"]["FUEL"] == commodity
                        ],
                        root_column="FUEL",
                        data_columns=["REGION", "YEAR"],
                        target_column="VALUE",
                    )
                )
                if commodity in dfs["SpecifiedAnnualDemand"]["FUEL"].values
                else None
            )
            accumulated_demand = (
                OSeMOSYSData.RY(
                    group_to_json(
                        g=dfs["AccumulatedAnnualDemand"].loc[
                            dfs["AccumulatedAnnualDemand"]["FUEL"] == commodity
                        ],
                        root_column="FUEL",
                        data_columns=["REGION", "YEAR"],
                        target_column="VALUE",
                    )
                )
                if commodity in dfs["AccumulatedAnnualDemand"]["FUEL"].values
                else None
            )

            # For each region and demand, check the same demand in not specified for both
            # deman_annual and acumulated_demand
            if demand_annual is not None and accumulated_demand is not None:
                for region in demand_annual.data.keys():
                    if region in accumulated_demand.data.keys():
                        raise ValueError(
                            f"In CSVs, Commodity '{commodity}' specified in both specified annual "
                            f"and accumulated demand for region '{region}'"
                        )

            demand_profile = (
                OSeMOSYSData.RYS.SumOne(
                    group_to_json(
                        g=dfs["SpecifiedDemandProfile"].loc[
                            dfs["SpecifiedDemandProfile"]["FUEL"] == commodity
                        ],
                        root_column="FUEL",
                        data_columns=["REGION", "YEAR", "TIMESLICE"],
                        target_column="VALUE",
                    )
                )
                if commodity in dfs["SpecifiedDemandProfile"]["FUEL"].values
                else None
            )
            include_in_joint_renewable_target = (
                OSeMOSYSData.RY.Bool(
                    group_to_json(
                        g=dfs["RETagFuel"].loc[dfs["RETagFuel"]["FUEL"] == commodity],
                        root_column="FUEL",
                        data_columns=["REGION", "YEAR"],
                        target_column="VALUE",
                    )
                )
                if commodity in dfs["RETagFuel"]["FUEL"].values
                else None
            )

            # Combine specified annual demand and accumulated annual demand
            if demand_annual is not None and accumulated_demand is not None:
                demand = OSeMOSYSData.RY({**demand_annual.data, **accumulated_demand.data})
            elif demand_annual is not None:
                demand = demand_annual
            elif accumulated_demand is not None:
                demand = accumulated_demand
            else:
                demand = None

            commodity_instances.append(
                cls(
                    id=commodity,
                    otoole_cfg=otoole_cfg,
                    demand_annual=demand,
                    demand_profile=demand_profile,
                    include_in_joint_renewable_target=include_in_joint_renewable_target,
                )
            )

        return commodity_instances

    @classmethod
    def to_dataframes(cls, commodities: List["Commodity"]):
        # collect dataframes
        dfs = {}

        dfs["FUEL"] = pd.DataFrame({"VALUE": [commodity.id for commodity in commodities]})

        # Parameters
        # collect demand dataframes
        accumulated_demand_dfs = []
        annual_demand_dfs = []
        demand_profile_dfs = []
        include_in_joint_renewable_target_dfs = []

        for commodity in commodities:
            if commodity.demand_annual is not None:
                df = pd.json_normalize(commodity.demand_annual.data).T.rename(columns={0: "VALUE"})
                df["FUEL"] = commodity.id
                df[["REGION", "YEAR"]] = pd.DataFrame(
                    df.index.str.split(".").to_list(), index=df.index
                )

                if commodity.demand_profile is not None:
                    for region in commodity.demand_annual.data.keys():
                        if region in commodity.demand_profile.data.keys():
                            # if profile data is given, add df to annual_demand_dfs
                            annual_demand_dfs.append(df.loc[df["REGION"] == region])

                            # ... and add profile df to demand_profile_dfs
                            df_profile = pd.json_normalize(commodity.demand_profile.data).T.rename(
                                columns={0: "VALUE"}
                            )
                            df_profile["FUEL"] = commodity.id
                            df_profile[["REGION", "YEAR", "TIMESLICE"]] = pd.DataFrame(
                                df_profile.index.str.split(".").to_list(),
                                index=df_profile.index,
                            )
                            demand_profile_dfs.append(
                                df_profile.loc[df_profile["REGION"] == region]
                            )
                        else:
                            accumulated_demand_dfs.append(df.loc[df["REGION"] == region])
                # If no demand_profile, put all data in accumulated demand
                else:
                    accumulated_demand_dfs.append(df)

            if commodity.include_in_joint_renewable_target is not None:
                df = pd.json_normalize(commodity.include_in_joint_renewable_target.data).T.rename(
                    columns={0: "VALUE"}
                )
                df["FUEL"] = commodity.id
                df[["REGION", "YEAR"]] = pd.DataFrame(
                    df.index.str.split(".").to_list(), index=df.index
                )
                df["VALUE"] = df["VALUE"].map({True: 1, False: 0})
                include_in_joint_renewable_target_dfs.append(df)

        dfs["SpecifiedAnnualDemand"] = (
            pd.concat(annual_demand_dfs)
            if annual_demand_dfs
            else pd.DataFrame(columns=cls.otoole_stems["SpecifiedAnnualDemand"]["columns"])
        )
        dfs["AccumulatedAnnualDemand"] = (
            pd.concat(accumulated_demand_dfs)
            if accumulated_demand_dfs
            else pd.DataFrame(columns=cls.otoole_stems["AccumulatedAnnualDemand"]["columns"])
        )
        dfs["SpecifiedDemandProfile"] = (
            pd.concat(demand_profile_dfs)
            if demand_profile_dfs
            else pd.DataFrame(columns=cls.otoole_stems["SpecifiedDemandProfile"]["columns"])
        )
        dfs["RETagFuel"] = (
            pd.concat(include_in_joint_renewable_target_dfs)
            if include_in_joint_renewable_target_dfs
            else pd.DataFrame(columns=cls.otoole_stems["RETagFuel"]["columns"])
        )

        return dfs

    @classmethod
    def to_otoole_csv(cls, commodities: List["Commodity"], output_directory: str):
        """Write a number of Commodity objects to otoole-organised csvs.

        Args:
            commodities (List[Commodity]): A list of Commodity instances
            output_directory (str): Path to the root of the otoole csv directory
        """

        dfs = cls.to_dataframes(commodities=commodities)

        # Sets
        dfs["FUEL"].to_csv(os.path.join(output_directory, "FUEL.csv"), index=False)

        # params to csv where appropriate
        for stem, _params in cls.otoole_stems.items():
            if any([(stem not in commodity.otoole_cfg.empty_dfs) for commodity in commodities]):
                dfs[stem].to_csv(os.path.join(output_directory, f"{stem}.csv"), index=False)

        return True
