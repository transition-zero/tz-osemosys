import os
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, List, Union

import pandas as pd
from pydantic import BaseModel, Field, model_validator

from tz.osemosys.schemas.base import OSeMOSYSData
from tz.osemosys.schemas.compat.base import OtooleCfg
from tz.osemosys.schemas.validation.region_validation import (
    discount_rate_as_decimals,
    reserve_margin_fully_defined,
)
from tz.osemosys.utils import group_to_json

if TYPE_CHECKING:
    from tz.osemosys.schemas.region import Region

##########
# REGION #
##########


class OtooleRegion(BaseModel):
    """
    Class to contain methods for converting Region data to and from otoole style CSVs
    """

    otoole_cfg: OtooleCfg | None = Field(default=None)
    otoole_stems: ClassVar[dict[str : dict[str : Union[str, list[str]]]]] = {
        "TradeRoute": {
            "attribute": "trade_route",
            "columns": ["REGION", "_REGION", "FUEL", "YEAR", "VALUE"],
        },
    }

    @model_validator(mode="before")
    def validation(cls, values):
        values = reserve_margin_fully_defined(values)
        values = discount_rate_as_decimals(values)
        return values

    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["Region"]:
        """Instantiate a number of Region objects from otoole-organised csvs.

        Args:
            root_dir (str): Path to the root of the otoole csv directory

        Returns:
            List[Region] (list): A list of Region instances,
            that can be used downstream or dumped to json/yaml
        """

        #############
        # Load Data #
        #############

        # Sets
        src_regions = pd.read_csv(os.path.join(root_dir, "REGION.csv"))
        try:
            dst_regions = pd.read_csv(os.path.join(root_dir, "_REGION.csv"))
        except FileNotFoundError:
            dst_regions = None

        # Parameters
        dfs = {}
        otoole_cfg = OtooleCfg(empty_dfs=[])
        for key in list(cls.otoole_stems):
            try:
                dfs[key] = pd.read_csv(Path(root_dir) / f"{key}.csv")
                if dfs[key].empty:
                    otoole_cfg.empty_dfs.append(key)
            except FileNotFoundError:
                otoole_cfg.empty_dfs.append(key)

        #####################
        # Basic Data Checks #
        #####################

        # Assert regions in REGION.csv match those in _REGION.csv
        assert (
            dfs["TradeRoute"]["REGION"].isin(src_regions["VALUE"]).all()
        ), "REGION in trade_route missing from REGION.csv"
        if dst_regions is not None:
            assert src_regions.equals(dst_regions), "Source and destination regions not equal."
            assert (
                dfs["TradeRoute"]["_REGION"].isin(dst_regions["VALUE"]).all()
            ), "_REGION in trade_route missing from _REGION.csv"

        # Rename "_REGION" to account for it not being valid in itertuples() in utils
        dfs["TradeRoute"] = dfs["TradeRoute"].rename(columns={"_REGION": "LINKED_REGION"})

        # Convert TradeRoute binary linking value to bool
        dfs["TradeRoute"]["VALUE"] = dfs["TradeRoute"]["VALUE"].map({1: True, 0: False})

        ##########################
        # Define class instances #
        ##########################

        # Identify regions with trade route defined
        if "TradeRoute" not in otoole_cfg.empty_dfs:
            regions_with_trade = []
            for region in src_regions["VALUE"].values:
                if not dfs["TradeRoute"].loc[dfs["TradeRoute"]["REGION"] == region].empty:
                    regions_with_trade.append(region)
        else:
            regions_with_trade = []

        region_instances = []
        for _index, region in src_regions.iterrows():
            region_instances.append(
                cls(
                    id=region["VALUE"],
                    otoole_cfg=otoole_cfg,
                    trade_routes=(
                        OSeMOSYSData.RCY.Bool(
                            group_to_json(
                                g=dfs["TradeRoute"].loc[
                                    dfs["TradeRoute"]["REGION"] == region["VALUE"]
                                ],
                                root_column="REGION",
                                data_columns=["LINKED_REGION", "FUEL", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if region["VALUE"] in regions_with_trade
                        else None
                    ),
                )
            )

        return region_instances

    @classmethod
    def to_dataframes(cls, regions: List["Region"]):
        # collect dataframes
        dfs = {}

        # Parameters
        # collect TradeRoutes
        trade_route_dfs = []
        for region in regions:
            if region.trade_routes is not None:
                for neighbour, trade_route in region.trade_routes.data.items():
                    df = pd.json_normalize(trade_route).T.rename(columns={0: "VALUE"})
                    df["REGION"] = region.id
                    df["_REGION"] = neighbour
                    df[["FUEL", "YEAR"]] = pd.DataFrame(
                        df.index.str.split(".").to_list(), index=df.index
                    )
                    trade_route_dfs.append(df)

        if trade_route_dfs:
            dfs["TradeRoute"] = pd.concat(trade_route_dfs)

        # SETS
        dfs["REGION"] = pd.DataFrame({"VALUE": [r.id for r in regions]})
        dfs["_REGION"] = pd.DataFrame({"VALUE": [r.id for r in regions]})

        return dfs

    @classmethod
    def to_otoole_csv(cls, regions: List["Region"], output_directory: str):
        """Write a number of Region objects to otoole-organised csvs.

        Args:
            regions (List[Region]): A list of Region instances
            output_directory (str): Path to the root of the otoole csv directory
        """

        dfs = cls.to_dataframes(regions)

        # Sets
        dfs["REGION"].to_csv(os.path.join(output_directory, "REGION.csv"), index=False)
        dfs["_REGION"].to_csv(os.path.join(output_directory, "_REGION.csv"), index=False)

        if "TradeRoute" in dfs:
            dfs["TradeRoute"]["VALUE"] = dfs["TradeRoute"]["VALUE"].astype(int)

        # write dataframes
        for stem, _params in cls.otoole_stems.items():
            if any([(stem not in region.otoole_cfg.empty_dfs) for region in regions]):
                dfs[stem].to_csv(os.path.join(output_directory, f"{stem}.csv"), index=False)

        return True
