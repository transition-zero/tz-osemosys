import os
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, List, Union

import pandas as pd
from pydantic import BaseModel, Field

from tz.osemosys.defaults import defaults
from tz.osemosys.schemas.base import OSeMOSYSData
from tz.osemosys.schemas.compat.base import OtooleCfg
from tz.osemosys.utils import group_to_json

if TYPE_CHECKING:
    from tz.osemosys.schemas.trade import Trade


class OtooleTrade(BaseModel):
    """
    Class to contain methods for converting Trade data to and from otoole style CSVs
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
        "DiscountRateTrade": {
            "attribute": "cost_of_capital",
            "columns": ["REGION", "_REGION", "FUEL", "VALUE"],
        },
    }

    @classmethod
    def from_otoole_csv(cls, root_dir) -> "Trade":
        """
        Instantiate a single Trade object containing all relevant data from
        otoole-organised csvs.

        Parameters
        ----------
        root_dir: str
            Path to the root of the otoole csv directory

        Returns
        -------
        Trade
            A single Trade instance that can be used downstream or dumped to json/yaml
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

        if "TradeRoute" in otoole_cfg.empty_dfs:
            trade_instances = None
        else:
            trade_instances = []
            for commodity in dfs["TradeRoute"]["FUEL"].values.tolist():

                id = commodity + " trade"
                commodity = commodity
                trade_routes = (
                    OSeMOSYSData.RRY.Bool(
                        group_to_json(
                            g=dfs["TradeRoute"].loc[dfs["TradeRoute"]["FUEL"] == commodity],
                            data_columns=["REGION", "LINKED_REGION", "YEAR"],
                            target_column="VALUE",
                        )
                    )
                    if "TradeRoute" not in otoole_cfg.empty_dfs
                    else None
                )
                trade_loss = (
                    OSeMOSYSData.RRY(
                        group_to_json(
                            g=dfs["TradeLossBetweenRegions"].loc[
                                dfs["TradeLossBetweenRegions"]["FUEL"] == commodity
                            ],
                            data_columns=["REGION", "LINKED_REGION", "YEAR"],
                            target_column="VALUE",
                        )
                    )
                    if "TradeLossBetweenRegions" not in otoole_cfg.empty_dfs
                    else OSeMOSYSData.RRY(defaults.trade_loss)
                )
                residual_capacity = (
                    OSeMOSYSData.RRY(
                        group_to_json(
                            g=dfs["ResidualTradeCapacity"].loc[
                                dfs["ResidualTradeCapacity"]["FUEL"] == commodity
                            ],
                            data_columns=["REGION", "LINKED_REGION", "YEAR"],
                            target_column="VALUE",
                        )
                    )
                    if "ResidualTradeCapacity" not in otoole_cfg.empty_dfs
                    else OSeMOSYSData.RRY(defaults.trade_residual_capacity)
                )
                capex = (
                    OSeMOSYSData.RRY(
                        group_to_json(
                            g=dfs["CapitalCostTrade"].loc[
                                dfs["CapitalCostTrade"]["FUEL"] == commodity
                            ],
                            data_columns=["REGION", "LINKED_REGION", "YEAR"],
                            target_column="VALUE",
                        )
                    )
                    if "CapitalCostTrade" not in otoole_cfg.empty_dfs
                    else OSeMOSYSData.RRY(defaults.trade_capex)
                )
                capacity_additional_max = (
                    OSeMOSYSData.RRY(
                        group_to_json(
                            g=dfs["TotalAnnualMaxTradeInvestment"].loc[
                                dfs["TotalAnnualMaxTradeInvestment"]["FUEL"] == commodity
                            ],
                            data_columns=["REGION", "LINKED_REGION", "YEAR"],
                            target_column="VALUE",
                        )
                    )
                    if "TotalAnnualMaxTradeInvestment" not in otoole_cfg.empty_dfs
                    else None
                )
                operational_life = (
                    OSeMOSYSData.RRY.Int(
                        group_to_json(
                            g=dfs["OperationalLifeTrade"].loc[
                                dfs["OperationalLifeTrade"]["FUEL"] == commodity
                            ],
                            data_columns=["REGION", "LINKED_REGION", "YEAR"],
                            target_column="VALUE",
                        )
                    )
                    if "OperationalLifeTrade" not in otoole_cfg.empty_dfs
                    else OSeMOSYSData.RRY.Int(defaults.trade_operating_life)
                )
                cost_of_capital = (
                    OSeMOSYSData.RR(
                        group_to_json(
                            g=dfs["DiscountRateTrade"].loc[
                                dfs["DiscountRateTrade"]["FUEL"] == commodity
                            ],
                            data_columns=["REGION", "LINKED_REGION"],
                            target_column="VALUE",
                        )
                    )
                    if "DiscountRateTrade" not in otoole_cfg.empty_dfs
                    else None
                )
                otoole_cfg = otoole_cfg

                trade_instances.append(
                    cls(
                        id=id,
                        commodity=commodity,
                        otoole_cfg=otoole_cfg,
                        trade_routes=trade_routes,
                        trade_loss=trade_loss,
                        residual_capacity=residual_capacity,
                        capex=capex,
                        capacity_additional_max=capacity_additional_max,
                        operational_life=operational_life,
                        cost_of_capital=cost_of_capital,
                    )
                )

        return trade_instances

    @classmethod
    def to_dataframes(cls, trade: List["Trade"]):

        dfs = {}

        trade_routes_dfs = []
        trade_loss_dfs = []
        residual_capacity_dfs = []
        capex_dfs = []
        capacity_additional_max_dfs = []
        operational_life_dfs = []
        cost_of_capital_dfs = []

        for trade_commodity in trade:

            if trade_commodity.trade_routes is not None:
                df = pd.json_normalize(trade_commodity.trade_routes.data).T.rename(
                    columns={0: "VALUE"}
                )
                df[["REGION", "_REGION", "YEAR"]] = pd.DataFrame(
                    df.index.str.split(".").to_list(), index=df.index
                )
                df["FUEL"] = trade_commodity.commodity
                df["VALUE"] = df["VALUE"].map({True: 1, False: 0})
                trade_routes_dfs.append(df)

            if trade_commodity.trade_loss is not None:
                df = pd.json_normalize(trade_commodity.trade_loss.data).T.rename(
                    columns={0: "VALUE"}
                )
                df[["REGION", "_REGION", "YEAR"]] = pd.DataFrame(
                    df.index.str.split(".").to_list(), index=df.index
                )
                df["FUEL"] = trade_commodity.commodity
                trade_loss_dfs.append(df)

            if trade_commodity.capacity_additional_max is not None:
                df = pd.json_normalize(trade_commodity.capacity_additional_max.data).T.rename(
                    columns={0: "VALUE"}
                )
                df[["REGION", "_REGION", "YEAR"]] = pd.DataFrame(
                    df.index.str.split(".").to_list(), index=df.index
                )
                df["FUEL"] = trade_commodity.commodity
                capacity_additional_max_dfs.append(df)

            if trade_commodity.residual_capacity is not None:
                df = pd.json_normalize(trade_commodity.residual_capacity.data).T.rename(
                    columns={0: "VALUE"}
                )

                df[["REGION", "_REGION", "YEAR"]] = pd.DataFrame(
                    df.index.str.split(".").to_list(), index=df.index
                )
                df["FUEL"] = trade_commodity.commodity
                residual_capacity_dfs.append(df)

            if trade_commodity.operational_life is not None:
                df = pd.json_normalize(trade_commodity.operational_life.data).T.rename(
                    columns={0: "VALUE"}
                )

                df[["REGION", "_REGION", "YEAR"]] = pd.DataFrame(
                    df.index.str.split(".").to_list(), index=df.index
                )
                df["FUEL"] = trade_commodity.commodity
                operational_life_dfs.append(df)

            if trade_commodity.capex is not None:
                df = pd.json_normalize(trade_commodity.capex.data).T.rename(columns={0: "VALUE"})
                df[["REGION", "_REGION", "YEAR"]] = pd.DataFrame(
                    df.index.str.split(".").to_list(), index=df.index
                )
                df["FUEL"] = trade_commodity.commodity
                capex_dfs.append(df)

            if trade_commodity.cost_of_capital is not None:
                df = pd.json_normalize(trade_commodity.cost_of_capital.data).T.rename(
                    columns={0: "VALUE"}
                )
                df[["REGION", "_REGION"]] = pd.DataFrame(
                    df.index.str.split(".").to_list(), index=df.index
                )
                df["FUEL"] = trade_commodity.commodity
                cost_of_capital_dfs.append(df)

        dfs["TradeRoute"] = (
            pd.concat(trade_routes_dfs)
            if trade_routes_dfs
            else pd.DataFrame(columns=cls.otoole_stems["TradeRoute"]["columns"])
        )
        dfs["TradeLossBetweenRegions"] = (
            pd.concat(trade_loss_dfs)
            if trade_loss_dfs
            else pd.DataFrame(columns=cls.otoole_stems["TradeLossBetweenRegions"]["columns"])
        )
        dfs["TotalAnnualMaxTradeInvestment"] = (
            pd.concat(capacity_additional_max_dfs)
            if capacity_additional_max_dfs
            else pd.DataFrame(columns=cls.otoole_stems["TotalAnnualMaxTradeInvestment"]["columns"])
        )
        dfs["ResidualTradeCapacity"] = (
            pd.concat(residual_capacity_dfs)
            if residual_capacity_dfs
            else pd.DataFrame(columns=cls.otoole_stems["ResidualTradeCapacity"]["columns"])
        )
        dfs["OperationalLifeTrade"] = (
            pd.concat(operational_life_dfs)
            if operational_life_dfs
            else pd.DataFrame(columns=cls.otoole_stems["OperationalLifeTrade"]["columns"])
        )
        dfs["CapitalCostTrade"] = (
            pd.concat(capex_dfs)
            if capex_dfs
            else pd.DataFrame(columns=cls.otoole_stems["CapitalCostTrade"]["columns"])
        )
        dfs["DiscountRateTrade"] = (
            pd.concat(cost_of_capital_dfs)
            if cost_of_capital_dfs
            else pd.DataFrame(columns=cls.otoole_stems["DiscountRateTrade"]["columns"])
        )

        return dfs

    @classmethod
    def to_otoole_csv(cls, trade: List["Trade"], output_directory: str):
        """Write a number of Trade objects to otoole-organised csvs.

        Args:
            trade (List[Trade]): A list of Trade instances
            output_directory (str): Path to the root of the otoole csv directory
        """

        dfs = cls.to_dataframes(trade=trade)

        # params to csv where appropriate
        for stem, _params in cls.otoole_stems.items():
            if any(
                [(stem not in trade_commodity.otoole_cfg.empty_dfs) for trade_commodity in trade]
            ):
                dfs[stem].to_csv(os.path.join(output_directory, f"{stem}.csv"), index=False)

        return True
