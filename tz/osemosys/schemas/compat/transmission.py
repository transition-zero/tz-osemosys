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
            "attribute": "trade_routes",
            "columns": ["REGION", "_REGION", "FUEL", "YEAR", "VALUE"],
        },
        "TradeLossBetweenRegions": {
            "attribute": "trade_loss",
            "columns": ["REGION", "_REGION", "FUEL", "YEAR", "VALUE"],
        },
        "TotalAnnualMaxTradeInvestment": {
            "attribute": "capacity_additional_max",
            "columns": ["REGION", "_REGION", "FUEL", "YEAR", "VALUE"],
        },
        "ResidualTradeCapacity": {
            "attribute": "residual_capacity",
            "columns": ["REGION", "_REGION", "FUEL", "YEAR", "VALUE"],
        },
        "OperationalLifeTrade": {
            "attribute": "operational_life",
            "columns": ["REGION", "_REGION", "FUEL", "YEAR", "VALUE"],
        },
        "CapitalCostTrade": {
            "attribute": "capex",
            "columns": ["REGION", "_REGION", "FUEL", "YEAR", "VALUE"],
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
        for name, df in dfs.items():
            dfs[name] = df.rename(columns={"_REGION": "LINKED_REGION"})

        return cls(
            id=Path(root_dir).name,
            trade_routes=(
                OSeMOSYSData.RRCY.Bool(
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
                OSeMOSYSData.RRCY.Int(
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
            df["VALUE"] = df["VALUE"].map({True: 1, False: 0})
            dfs["TradeRoute"] = df

        if self.trade_loss is not None:
            df = pd.json_normalize(self.trade_loss.data).T.rename(columns={0: "VALUE"})
            df[["REGION", "_REGION", "FUEL", "YEAR"]] = pd.DataFrame(
                df.index.str.split(".").to_list(), index=df.index
            )
            dfs["TradeLossBetweenRegions"] = df

        if self.capacity_additional_max is not None:
            df = pd.json_normalize(self.capacity_additional_max.data).T.rename(columns={0: "VALUE"})
            df[["REGION", "_REGION", "FUEL", "YEAR"]] = pd.DataFrame(
                df.index.str.split(".").to_list(), index=df.index
            )
            dfs["TotalAnnualMaxTradeInvestment"] = df

        if self.residual_capacity is not None:
            df = pd.json_normalize(self.residual_capacity.data).T.rename(columns={0: "VALUE"})
            df[["REGION", "_REGION", "FUEL", "YEAR"]] = pd.DataFrame(
                df.index.str.split(".").to_list(), index=df.index
            )
            dfs["ResidualTradeCapacity"] = df

        if self.operational_life is not None:
            df = pd.json_normalize(self.operational_life.data).T.rename(columns={0: "VALUE"})
            df[["REGION", "_REGION", "FUEL", "YEAR"]] = pd.DataFrame(
                df.index.str.split(".").to_list(), index=df.index
            )
            dfs["OperationalLifeTrade"] = df

        if self.capex is not None:
            df = pd.json_normalize(self.capex.data).T.rename(columns={0: "VALUE"})
            df[["REGION", "_REGION", "FUEL", "YEAR"]] = pd.DataFrame(
                df.index.str.split(".").to_list(), index=df.index
            )
            dfs["CapitalCostTrade"] = df

        return dfs

    def to_otoole_csv(self, output_directory):

        dfs = self.to_dataframes()

        for stem, _params in self.otoole_stems.items():
            if stem not in self.otoole_cfg.empty_dfs:
                dfs[stem].to_csv(Path(output_directory) / f"{stem}.csv", index=False)
