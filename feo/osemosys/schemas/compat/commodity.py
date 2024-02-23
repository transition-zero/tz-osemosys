import os
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, List, Union

import pandas as pd
from pydantic import BaseModel, Field

from feo.osemosys.schemas.base import OSeMOSYSData, OSeMOSYSData_Bool
from feo.osemosys.schemas.compat.base import OtooleCfg
from feo.osemosys.utils import group_to_json

if TYPE_CHECKING:
    from feo.osemosys.schemas.commodity import Commodity


class OtooleCommodity(BaseModel):
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
            "attribute": "is_renewable",
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
                OSeMOSYSData(
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
                OSeMOSYSData(
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
            if demand_annual is not None and accumulated_demand is not None:
                raise ValueError(
                    f"Commodity '{commodity}' specified with both annual and accumulated demand."
                )

            demand_profile = (
                OSeMOSYSData(
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
            is_renewable = (
                OSeMOSYSData_Bool(
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

            commodity_instances.append(
                cls(
                    id=commodity,
                    otoole_cfg=otoole_cfg,
                    demand_annual=demand_annual or accumulated_demand,
                    demand_profile=demand_profile,
                    is_renewable=is_renewable,
                )
            )

        return commodity_instances

    @classmethod
    def to_otoole_csv(cls, commodities: List["Commodity"], output_directory: str):
        """Write a number of Commodity objects to otoole-organised csvs.

        Args:
            commodities (List[Commodity]): A list of Commodity instances
            output_directory (str): Path to the root of the otoole csv directory
        """

        # Sets
        commodities_df = pd.DataFrame({"VALUE": [commodity.id for commodity in commodities]})
        commodities_df.to_csv(os.path.join(output_directory, "FUEL.csv"), index=False)

        # Parameters
        # collect demand dataframes
        accumulated_demand_dfs = []
        annual_demand_dfs = []
        demand_profile_dfs = []
        for commodity in commodities:
            if commodity.demand_annual is not None:
                df = pd.json_normalize(commodity.demand_annual.data).T.rename(columns={0: "VALUE"})
                df["FUEL"] = commodity.id
                df[["REGION", "YEAR"]] = pd.DataFrame(
                    df.index.str.split(".").to_list(), index=df.index
                )

                if commodity.demand_profile is not None:
                    # if profile data is given, add df to annual_demand_dfs
                    annual_demand_dfs.append(df)

                    # ... and add profile df to demand_profile_dfs
                    df = pd.json_normalize(commodity.demand_profile.data).T.rename(
                        columns={0: "VALUE"}
                    )
                    df["FUEL"] = commodity.id
                    df[["REGION", "YEAR", "TIMESLICE"]] = pd.DataFrame(
                        df.index.str.split(".").to_list(), index=df.index
                    )
                    demand_profile_dfs.append(df)
                else:
                    accumulated_demand_dfs.append(df)

        if any(
            [
                ("SpecifiedDemandProfile" not in commodity.otoole_cfg.empty_dfs)
                for commodity in commodities
            ]
        ):
            pd.concat(demand_profile_dfs).to_csv(
                os.path.join(output_directory, "SpecifiedDemandProfile.csv"), index=False
            )

        if any(
            [
                ("SpecifiedAnnualDemand" not in commodity.otoole_cfg.empty_dfs)
                for commodity in commodities
            ]
        ):
            pd.concat(annual_demand_dfs).to_csv(
                os.path.join(output_directory, "SpecifiedAnnualDemand.csv"), index=False
            )

        if any(
            [
                ("AccumulatedAnnualDemand" not in commodity.otoole_cfg.empty_dfs)
                for commodity in commodities
            ]
        ):
            pd.concat(accumulated_demand_dfs).to_csv(
                os.path.join(output_directory, "AccumulatedAnnualDemand.csv"), index=False
            )

        return True
