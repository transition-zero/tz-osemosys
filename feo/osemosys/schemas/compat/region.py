import os
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, List, Union

import pandas as pd
from pydantic import BaseModel, Field, model_validator

from feo.osemosys.schemas.base import OSeMOSYSData
from feo.osemosys.schemas.compat.base import OtooleCfg
from feo.osemosys.schemas.validation.region_validation import (
    discount_rate_as_decimals,
    reserve_margin_fully_defined,
)
from feo.osemosys.utils import group_to_json

if TYPE_CHECKING:
    from feo.osemosys.schemas.region import Region

##########
# REGION #
##########


class OtooleRegion(BaseModel):
    otoole_cfg: OtooleCfg | None = Field(default=None)
    otoole_stems: ClassVar[dict[str : dict[str : Union[str, list[str]]]]] = {
        "TradeRoute": {
            "attribute": "trade_route",
            "column_structure": ["REGION", "_REGION", "FUEL", "YEAR", "VALUE"],
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

        ##########################
        # Define class instances #
        ##########################

        region_instances = []
        for _index, region in src_regions.iterrows():
            region_instances.append(
                cls(
                    id=region["VALUE"],
                    otoole_cfg=otoole_cfg,
                    trade_routes=(
                        OSeMOSYSData(
                            group_to_json(
                                g=dfs["TradeRoute"].loc[
                                    dfs["TradeRoute"]["REGION"] == region["VALUE"]
                                ],
                                root_column="REGION",
                                data_columns=["_REGION", "FUEL", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if "TradeRoute" not in otoole_cfg.empty_dfs
                        else None
                    ),
                )
            )

        return region_instances

    @classmethod
    def to_otoole_csv(cls, regions: List["Region"], output_directory: str):
        """Write a number of Region objects to otoole-organised csvs.

        Args:
            regions (List[Region]): A list of Region instances
            output_directory (str): Path to the root of the otoole csv directory
        """

        # Sets
        regions_df = pd.DataFrame({"VALUE": [r.id for r in regions]})
        regions_df.to_csv(os.path.join(output_directory, "REGION.csv"), index=False)
        regions_df.to_csv(os.path.join(output_directory, "_REGION.csv"), index=False)

        # Parameters
        # collect TradeRoutes
        if any([("TradeRoute" not in r.otoole_cfg.empty_dfs) for r in regions]):
            trade_route_dfs = []
            for region in regions:
                if region.trade_routes is not None:
                    for neighbour, trade_route in region.trade_routes.items():
                        df = pd.json_normalize(trade_route.data).T.rename(columns={0: "VALUE"})
                        df["REGION"] = region.id
                        df["_REGION"] = neighbour
                        df[["FUEL", "YEAR"]] = pd.DataFrame(
                            df.index.str.split(".").to_list(), index=df.index
                        )
                        trade_route_dfs.append(df)

            trade_routes = pd.concat(trade_route_dfs)
            trade_routes.to_csv(os.path.join(output_directory, "TradeRoute.csv"), index=False)

        return True
