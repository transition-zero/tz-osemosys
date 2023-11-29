import os

import pandas as pd
from pydantic import BaseModel, conlist, root_validator
from typing import ClassVar
from pathlib import Path

from feo.osemosys.utils import *

from .base import *


class OtooleCfg(BaseModel):
    """
    Paramters needed to round-trip csvs from otoole
    """

    empty_dfs: List[str] | None


class OtherParameters(OSeMOSYSBase):
    """
    Class to contain all other parameters
    """

    mode_of_operation: conlist(int, min_length=1)
    depreciation_method: OSeMOSYSData | None
    discount_rate: OSeMOSYSData | None
    discount_rate_idv: OSeMOSYSData | None
    discount_rate_storage: OSeMOSYSData | None
    reserve_margin: OSeMOSYSData | None
    reserve_margin_tag_fuel: OSeMOSYSDataInt | None
    reserve_margin_tag_technology: OSeMOSYSDataInt | None
    renewable_production_target: OSeMOSYSData | None

    otoole_cfg: OtooleCfg | None
    otoole_stems: ClassVar[dict[str:dict[str:Union[str, list[str]]]]] = {
        "MODE_OF_OPERATION":{"attribute":"mode_of_operation","column_structure":["VALUE"]},
        "DepreciationMethod":{"attribute":"depreciation_method","column_structure":["REGION","VALUE"]},
        "DiscountRate":{"attribute":"discount_rate","column_structure":["REGION","VALUE"]},
        "DiscountRateIdv":{"attribute":"discount_rate_idv","column_structure":["REGION","TECHNOLOGY","VALUE"]},
        "DiscountRateStorage":{"attribute":"discount_rate_storage","column_structure":["REGION","STORAGE","VALUE"]},
        "ReserveMargin":{"attribute":"reserve_margin","column_structure":["REGION","YEAR","VALUE"]},
        "ReserveMarginTagFuel":{"attribute":"reserve_margin_tag_fuel","column_structure":["REGION","FUEL","YEAR","VALUE"]},
        "ReserveMarginTagTechnology":{"attribute":"reserve_margin_tag_technology","column_structure":["REGION","TECHNOLOGY","YEAR","VALUE"]},
        "REMinProductionTarget":{"attribute":"renewable_production_target","column_structure":["REGION","YEAR","VALUE"]},
    }
    
    @root_validator(pre=True)
    def construct_from_components(cls, values):
        mode_of_operation = values.get("mode_of_operation")
        depreciation_method = values.get("depreciation_method")
        discount_rate = values.get("discount_rate")
        discount_rate_idv = values.get("discount_rate_idv")
        discount_rate_storage = values.get("discount_rate_storage")
        reserve_margin = values.get("reserve_margin")
        reserve_margin_tag_fuel = values.get("reserve_margin_tag_fuel")
        reserve_margin_tag_technology = values.get("reserve_margin_tag_technology")
        renewable_production_target = values.get("renewable_production_target")
        
        # failed to specify mode_of_operation
        if not mode_of_operation:
            raise ValueError("mode_of_operation (List[int]) must be specified.")

        return values

    @classmethod
    def from_otoole_csv(cls, root_dir) -> "cls":
        """
        Instantiate a single OtherParameter object containing all relevant data from otoole-organised csvs.

        Parameters
        ----------
        root_dir: str
            Path to the root of the otoole csv directory

        Returns
        -------
        OtherParameters
            A single OtherParameters instance that can be used downstream or dumped to json/yaml
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
        if "MODE_OF_OPERATION" in dfs:
            mode_of_operation = dfs["MODE_OF_OPERATION"]["VALUE"].values.tolist()
        else:
            raise FileNotFoundError("MODE_OF_OPERATION.csv not read in, likely missing from root_dir")

        return cls(
            id="OtherParameters",
            # TODO
            long_name=None,
            description=None,
            otoole_cfg=otoole_cfg,
            mode_of_operation=mode_of_operation,
            depreciation_method=(
                OSeMOSYSData(
                    data=group_to_json(
                        g=dfs["DepreciationMethod"],
                        data_columns=["REGION"],
                        target_column="VALUE",
                    )
                )
                if "DepreciationMethod" not in otoole_cfg.empty_dfs
                else None
            ),
            discount_rate=(
                OSeMOSYSData(
                    data=group_to_json(
                        g=dfs["DiscountRate"],
                        data_columns=["REGION"],
                        target_column="VALUE",
                    )
                )
                if "DiscountRate" not in otoole_cfg.empty_dfs
                else None
            ),
            discount_rate_idv=(
                OSeMOSYSData(
                    data=group_to_json(
                        g=dfs["DiscountRateIdv"],
                        data_columns=["REGION","TECHNOLOGY"],
                        target_column="VALUE",
                    )
                )
                if "DiscountRateIdv" not in otoole_cfg.empty_dfs
                else None
            ),
            discount_rate_storage=(
                OSeMOSYSData(
                    data=group_to_json(
                        g=dfs["DiscountRateStorage"],
                        data_columns=["REGION","STORAGE"],
                        target_column="VALUE",
                    )
                )
                if "DiscountRateStorage" not in otoole_cfg.empty_dfs
                else None
            ),
            reserve_margin=(
                OSeMOSYSData(
                    data=group_to_json(
                        g=dfs["ReserveMargin"],
                        data_columns=["REGION","YEAR"],
                        target_column="VALUE",
                    )
                )
                if "ReserveMargin" not in otoole_cfg.empty_dfs
                else None
            ),
            reserve_margin_tag_fuel=(
                OSeMOSYSDataInt(
                    data=group_to_json(
                        g=dfs["ReserveMarginTagFuel"],
                        data_columns=["REGION","FUEL","YEAR"],
                        target_column="VALUE",
                    )
                )
                if "ReserveMarginTagFuel" not in otoole_cfg.empty_dfs
                else None
            ),
            reserve_margin_tag_technology=(
                OSeMOSYSDataInt(
                    data=group_to_json(
                        g=dfs["ReserveMarginTagTechnology"],
                        data_columns=["REGION","TECHNOLOGY","YEAR"],
                        target_column="VALUE",
                    )
                )
                if "ReserveMarginTagTechnology" not in otoole_cfg.empty_dfs
                else None
            ),
            renewable_production_target=(
                OSeMOSYSData(
                    data=group_to_json(
                        g=dfs["REMinProductionTarget"],
                        data_columns=["REGION","YEAR"],
                        target_column="VALUE",
                    )
                )
                if "REMinProductionTarget" not in otoole_cfg.empty_dfs
                else None
            )
            )
    