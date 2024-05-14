from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Union

import pandas as pd
from pydantic import BaseModel, Field

from tz.osemosys.schemas.base import OSeMOSYSData
from tz.osemosys.schemas.compat.base import OtooleCfg
from tz.osemosys.utils import group_to_json

if TYPE_CHECKING:
    from tz.osemosys.schemas.transmission import Transmission


class OtooleTransmission(BaseModel):
    """
    Class to contain methods for converting Transmission data to and from otoole style CSVs
    """

    otoole_cfg: OtooleCfg | None = Field(default=None)
    otoole_stems: ClassVar[dict[str : dict[str : Union[str, list[str]]]]] = {
        "TradeRoute": {
            "attribute": "year_split",
            "columns": ["TIMESLICE", "YEAR", "VALUE"],
        },
        "TradeLossBetweenRegions": {
            "attribute": "day_split",
            "columns": ["DAILYTIMEBRACKET", "YEAR", "VALUE"],
        },
        "TotalAnnualMaxTradeInvestment": {
            "attribute": "days_in_day_type",
            "columns": ["SEASON", "DAYTYPE", "YEAR", "VALUE"],
        },
        "ResidualTradeCapacity": {
            "attribute": "timeslice_in_timebracket",
            "columns": ["TIMESLICE", "DAILYTIMEBRACKET", "VALUE"],
        },
        "OperationalLifeTrade": {
            "attribute": "timeslice_in_daytype",
            "columns": ["TIMESLICE", "DAYTYPE", "VALUE"],
        },
        "CapitalCostTrade": {
            "attribute": "timeslice_in_season",
            "columns": ["TIMESLICE", "SEASON", "VALUE"],
        },
    }

    @classmethod
    def from_otoole_csv(cls, root_dir) -> "Transmission":
        """
        Instantiate a single Transmission object containing all relevant data from
        otoole-organised csvs.

        Parameters
        ----------
        root_dir: str
            Path to the root of the otoole csv directory

        Returns
        -------
        Transmission
            A single Transmission instance that can be used downstream or dumped to json/yaml
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

        # Rename _REGION to LINKED_REGION
        for df in dfs:
            df = df.rename(columns={"_REGION": "LINKED_REGION"})

        return cls(
            id=Path(root_dir).name,
            trade_routes=(
                OSeMOSYSData.RRCY(
                    group_to_json(
                        g=dfs["TradeRoute"],
                        data_columns=["REGION", "LINKED_REGION", "FUEL", "YEAR"],
                        target_column="VALUE",
                    )
                )
                if "TradeRoute" not in otoole_cfg.empty_dfs
                else None
            ),
            trade_loss=(
                OSeMOSYSData.RRCY(
                    group_to_json(
                        g=dfs["TradeLossBetweenRegions"],
                        data_columns=["REGION", "LINKED_REGION", "FUEL", "YEAR"],
                        target_column="VALUE",
                    )
                )
                if "TradeLossBetweenRegions" not in otoole_cfg.empty_dfs
                else None
            ),
            residual_capacity=(
                OSeMOSYSData.RRCY(
                    group_to_json(
                        g=dfs["ResidualTradeCapacity"],
                        data_columns=["REGION", "LINKED_REGION", "FUEL", "YEAR"],
                        target_column="VALUE",
                    )
                )
                if "ResidualTradeCapacity" not in otoole_cfg.empty_dfs
                else None
            ),
            capex=(
                OSeMOSYSData.RRCY(
                    group_to_json(
                        g=dfs["CapitalCostTrade"],
                        data_columns=["REGION", "LINKED_REGION", "FUEL", "YEAR"],
                        target_column="VALUE",
                    )
                )
                if "CapitalCostTrade" not in otoole_cfg.empty_dfs
                else None
            ),
            capacity_additional_max=(
                OSeMOSYSData.RRCY(
                    group_to_json(
                        g=dfs["TotalAnnualMaxTradeInvestment"],
                        data_columns=["REGION", "LINKED_REGION", "FUEL", "YEAR"],
                        target_column="VALUE",
                    )
                )
                if "TotalAnnualMaxTradeInvestment" not in otoole_cfg.empty_dfs
                else None
            ),
            operational_life=(
                OSeMOSYSData.RRCY(
                    group_to_json(
                        g=dfs["OperationalLifeTrade"],
                        data_columns=["REGION", "LINKED_REGION", "FUEL", "YEAR"],
                        target_column="VALUE",
                    )
                )
                if "OperationalLifeTrade" not in otoole_cfg.empty_dfs
                else None
            ),
            otoole_cfg=otoole_cfg,
        )

    def to_dataframes(self):
        dfs = {}

        if self.trade_routes is not None:
            df = pd.json_normalize(self.trade_routes.data).T.rename(columns={0: "VALUE"})
            df[["REGION", "_REGION", "FUEL", "YEAR"]] = pd.DataFrame(
                df.index.str.split(".").to_list(), index=df.index
            )
            dfs["TradeRoute"] = df

        if self.trade_routes is not None:
            df = pd.json_normalize(self.trade_routes.data).T.rename(columns={0: "VALUE"})
            df[["REGION", "_REGION", "FUEL", "YEAR"]] = pd.DataFrame(
                df.index.str.split(".").to_list(), index=df.index
            )
            dfs["TradeRoute"] = df

        if self.trade_routes is not None:
            df = pd.json_normalize(self.trade_routes.data).T.rename(columns={0: "VALUE"})
            df[["REGION", "_REGION", "FUEL", "YEAR"]] = pd.DataFrame(
                df.index.str.split(".").to_list(), index=df.index
            )
            dfs["TradeRoute"] = df

        if self.trade_routes is not None:
            df = pd.json_normalize(self.trade_routes.data).T.rename(columns={0: "VALUE"})
            df[["REGION", "_REGION", "FUEL", "YEAR"]] = pd.DataFrame(
                df.index.str.split(".").to_list(), index=df.index
            )
            dfs["TradeRoute"] = df

        if self.trade_routes is not None:
            df = pd.json_normalize(self.trade_routes.data).T.rename(columns={0: "VALUE"})
            df[["REGION", "_REGION", "FUEL", "YEAR"]] = pd.DataFrame(
                df.index.str.split(".").to_list(), index=df.index
            )
            dfs["TradeRoute"] = df

        if self.trade_routes is not None:
            df = pd.json_normalize(self.trade_routes.data).T.rename(columns={0: "VALUE"})
            df[["REGION", "_REGION", "FUEL", "YEAR"]] = pd.DataFrame(
                df.index.str.split(".").to_list(), index=df.index
            )
            dfs["TradeRoute"] = df

            # "TradeRoute"

        # "TradeLossBetweenRegions": {

        # "TotalAnnualMaxTradeInvestment": {

        # "ResidualTradeCapacity": {

        # "OperationalLifeTrade": {

        # "CapitalCostTrade": {

        return dfs

    def to_otoole_csv(self, output_directory):

        dfs = self.to_dataframes(self)

        for stem, _params in self.otoole_stems.items():
            if stem not in self.otoole_cfg.empty_dfs:
                dfs(stem).to_csv(Path(output_directory) / f"{stem}.csv", index=False)
