import os
from pathlib import Path
from typing import ClassVar, List, Union

import pandas as pd
from pydantic import BaseModel, conlist, model_validator

from feo.osemosys.schemas.validation.region_validation import (
    discount_rate_as_decimals,
    reserve_margin_fully_defined,
)
from feo.osemosys.utils import group_to_json

from .base import OSeMOSYSBase, OSeMOSYSData, OSeMOSYSDataInt

##########
# REGION #
##########


class OtooleCfg(BaseModel):
    """
    Paramters needed to round-trip csvs from otoole
    """

    empty_dfs: List[str] | None


class Region(OSeMOSYSBase):
    """
    Class to contain all information pertaining to regions and trade routes including:
    - discount rates
    - reserve margins
    - renewable production targets
    - depreciation method
    """

    neighbours: conlist(str, min_length=0) | None
    trade_route: OSeMOSYSDataInt | None
    depreciation_method: OSeMOSYSDataInt | None
    discount_rate: OSeMOSYSData | None
    discount_rate_idv: OSeMOSYSData | None
    discount_rate_storage: OSeMOSYSData | None
    reserve_margin: OSeMOSYSData | None
    reserve_margin_tag_fuel: OSeMOSYSDataInt | None
    reserve_margin_tag_technology: OSeMOSYSDataInt | None
    renewable_production_target: OSeMOSYSData | None

    otoole_cfg: OtooleCfg | None
    otoole_stems: ClassVar[dict[str : dict[str : Union[str, list[str]]]]] = {
        "TradeRoute": {
            "attribute": "trade_route",
            "column_structure": ["REGION", "_REGION", "FUEL", "YEAR", "VALUE"],
        },
        "DepreciationMethod": {
            "attribute": "depreciation_method",
            "column_structure": ["REGION", "VALUE"],
        },
        "DiscountRate": {"attribute": "discount_rate", "column_structure": ["REGION", "VALUE"]},
        "DiscountRateIdv": {
            "attribute": "discount_rate_idv",
            "column_structure": ["REGION", "TECHNOLOGY", "VALUE"],
        },
        "DiscountRateStorage": {
            "attribute": "discount_rate_storage",
            "column_structure": ["REGION", "STORAGE", "VALUE"],
        },
        "ReserveMargin": {
            "attribute": "reserve_margin",
            "column_structure": ["REGION", "YEAR", "VALUE"],
        },
        "ReserveMarginTagFuel": {
            "attribute": "reserve_margin_tag_fuel",
            "column_structure": ["REGION", "FUEL", "YEAR", "VALUE"],
        },
        "ReserveMarginTagTechnology": {
            "attribute": "reserve_margin_tag_technology",
            "column_structure": ["REGION", "TECHNOLOGY", "YEAR", "VALUE"],
        },
        "REMinProductionTarget": {
            "attribute": "renewable_production_target",
            "column_structure": ["REGION", "YEAR", "VALUE"],
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
                    # TODO
                    long_name=None,
                    description=None,
                    otoole_cfg=otoole_cfg,
                    neighbours=(
                        (
                            dfs["TradeRoute"]
                            .loc[dfs["TradeRoute"]["REGION"] == region["VALUE"], "_REGION"]
                            .values.tolist()
                        )
                        if dst_regions is not None
                        else None
                    ),
                    trade_route=(
                        OSeMOSYSDataInt(
                            data=group_to_json(
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
                    depreciation_method=(
                        OSeMOSYSDataInt(
                            data=group_to_json(
                                g=dfs["DepreciationMethod"].loc[
                                    dfs["DepreciationMethod"]["REGION"] == region["VALUE"]
                                ],
                                root_column="REGION",
                                target_column="VALUE",
                            )
                        )
                        if "DepreciationMethod" not in otoole_cfg.empty_dfs
                        else None
                    ),
                    discount_rate=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["DiscountRate"].loc[
                                    dfs["DiscountRate"]["REGION"] == region["VALUE"]
                                ],
                                root_column="REGION",
                                target_column="VALUE",
                            )
                        )
                        if "DiscountRate" not in otoole_cfg.empty_dfs
                        else None
                    ),
                    discount_rate_idv=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["DiscountRateIdv"].loc[
                                    dfs["DiscountRateIdv"]["REGION"] == region["VALUE"]
                                ],
                                root_column="REGION",
                                data_columns=["TECHNOLOGY"],
                                target_column="VALUE",
                            )
                        )
                        if "DiscountRateIdv" not in otoole_cfg.empty_dfs
                        else None
                    ),
                    discount_rate_storage=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["DiscountRateStorage"].loc[
                                    dfs["DiscountRateStorage"]["REGION"] == region["VALUE"]
                                ],
                                root_column="REGION",
                                data_columns=["STORAGE"],
                                target_column="VALUE",
                            )
                        )
                        if "DiscountRateStorage" not in otoole_cfg.empty_dfs
                        else None
                    ),
                    reserve_margin=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["ReserveMargin"].loc[
                                    dfs["ReserveMargin"]["REGION"] == region["VALUE"]
                                ],
                                root_column="REGION",
                                data_columns=["YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if "ReserveMargin" not in otoole_cfg.empty_dfs
                        else None
                    ),
                    reserve_margin_tag_fuel=(
                        OSeMOSYSDataInt(
                            data=group_to_json(
                                g=dfs["ReserveMarginTagFuel"].loc[
                                    dfs["ReserveMarginTagFuel"]["REGION"] == region["VALUE"]
                                ],
                                root_column="REGION",
                                data_columns=["FUEL", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if "ReserveMarginTagFuel" not in otoole_cfg.empty_dfs
                        else None
                    ),
                    reserve_margin_tag_technology=(
                        OSeMOSYSDataInt(
                            data=group_to_json(
                                g=dfs["ReserveMarginTagTechnology"].loc[
                                    dfs["ReserveMarginTagTechnology"]["REGION"] == region["VALUE"]
                                ],
                                root_column="REGION",
                                data_columns=["TECHNOLOGY", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if "ReserveMarginTagTechnology" not in otoole_cfg.empty_dfs
                        else None
                    ),
                    renewable_production_target=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["REMinProductionTarget"].loc[
                                    dfs["REMinProductionTarget"]["REGION"] == region["VALUE"]
                                ],
                                root_column="REGION",
                                data_columns=["YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if "REMinProductionTarget" not in otoole_cfg.empty_dfs
                        else None
                    ),
                )
            )

        return region_instances
