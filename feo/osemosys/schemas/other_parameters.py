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

    MODE_OF_OPERATION: conlist(int, min_length=1)
    DepreciationMethod: OSeMOSYSData | None
    DiscountRate: OSeMOSYSData | None
    DiscountRateIdv: OSeMOSYSData | None
    DiscountRateStorage: OSeMOSYSData | None
    ReserveMargin: OSeMOSYSData | None
    ReserveMarginTagFuel: OSeMOSYSDataInt | None
    ReserveMarginTagTechnology: OSeMOSYSDataInt | None
    REMinProductionTarget: OSeMOSYSData | None

    otoole_cfg: OtooleCfg | None
    otoole_stems: ClassVar[list[str]] = [
        "MODE_OF_OPERATION",
        "DepreciationMethod",
        "DiscountRate",
        "DiscountRateIdv",
        "DiscountRateStorage",
        "ReserveMargin",
        "ReserveMarginTagFuel",
        "ReserveMarginTagTechnology",
        "REMinProductionTarget",
    ]

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
        for key in cls.otoole_stems:
            try:
                dfs[key] = pd.read_csv(Path(root_dir) / f"{key}.csv")
                if dfs[key].empty:
                    otoole_cfg.empty_dfs.append(key)
            except FileNotFoundError:
                otoole_cfg.empty_dfs.append(key)

        return cls(
            id="OtherParameters",
            # TODO
            long_name=None,
            description=None,
            otoole_cfg=otoole_cfg,
            MODE_OF_OPERATION=dfs["MODE_OF_OPERATION"]["VALUE"].values.tolist(),
            DepreciationMethod=(
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
            DiscountRate=(
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
            DiscountRateIdv=(
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
            DiscountRateStorage=(
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
            ReserveMargin=(
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
            ReserveMarginTagFuel=(
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
            ReserveMarginTagTechnology=(
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
            REMinProductionTarget=(
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

    def to_otoole_csv(self, comparison_directory) -> "CSVs":

        # MODE_OF_OPERATION
        pd.DataFrame({"VALUE": self.MODE_OF_OPERATION}).to_csv(
            os.path.join(comparison_directory, "MODE_OF_OPERATION.csv"), index=False
        )

        # Depreciation Method
        if self.DepreciationMethod is not None:
            df = json_dict_to_dataframe(self.DepreciationMethod.data)
            df.columns = ["REGION","VALUE"]
            df.to_csv(os.path.join(comparison_directory, "DepreciationMethod.csv"), index=False)
        else:
            pd.DataFrame(
                columns=["REGION", "VALUE"]).to_csv(
                    os.path.join(comparison_directory, "DepreciationMethod.csv"), index=False
                )
        
        # DiscountRate
        if self.DiscountRate is not None:
            df = json_dict_to_dataframe(self.DiscountRate.data)
            df.columns = ["REGION","VALUE"]
            df.to_csv(os.path.join(comparison_directory, "DiscountRate.csv"), index=False)
        else:
            pd.DataFrame(
                columns=["REGION", "VALUE"]).to_csv(
                    os.path.join(comparison_directory, "DiscountRate.csv"), index=False
                )
            
        # DiscountRateIdv
        if self.DiscountRateIdv is not None:
            df = json_dict_to_dataframe(self.DiscountRateIdv.data)
            df.columns = ["REGION","TECHNOLOGY","VALUE"]
            df.to_csv(os.path.join(comparison_directory, "DiscountRateIdv.csv"), index=False)
        else:
            pd.DataFrame(
                columns=["REGION","TECHNOLOGY","VALUE"]).to_csv(
                    os.path.join(comparison_directory, "DiscountRateIdv.csv"), index=False
                )
            
        # DiscountRateStorage
        if self.DiscountRateStorage is not None:
            df = json_dict_to_dataframe(self.DiscountRateStorage.data)
            df.columns = ["REGION","STORAGE","VALUE"]
            df.to_csv(os.path.join(comparison_directory, "DiscountRateStorage.csv"), index=False)
        else:
            pd.DataFrame(
                columns=["REGION","STORAGE","VALUE"]).to_csv(
                    os.path.join(comparison_directory, "DiscountRateStorage.csv"), index=False
                )

        # ReserveMargin
        if self.ReserveMargin is not None:
            df = json_dict_to_dataframe(self.ReserveMargin.data)
            df.columns = ["REGION","YEAR","VALUE"]
            df.to_csv(os.path.join(comparison_directory, "ReserveMargin.csv"), index=False)
        else:
            pd.DataFrame(
                columns=["REGION","YEAR","VALUE"]).to_csv(
                    os.path.join(comparison_directory, "ReserveMargin.csv"), index=False
                )

        # ReserveMarginTagFuel
        if self.ReserveMarginTagFuel is not None:
            df = json_dict_to_dataframe(self.ReserveMarginTagFuel.data)
            df.columns = ["REGION","FUEL","YEAR","VALUE"]
            df.to_csv(os.path.join(comparison_directory, "ReserveMarginTagFuel.csv"), index=False)
        else:
            pd.DataFrame(
                columns=["REGION","FUEL","YEAR","VALUE"]).to_csv(
                    os.path.join(comparison_directory, "ReserveMarginTagFuel.csv"), index=False
                )
            
        # ReserveMarginTagTechnology
        if self.ReserveMarginTagTechnology is not None:
            df = json_dict_to_dataframe(self.ReserveMarginTagTechnology.data)
            df.columns = ["REGION","TECHNOLOGY","YEAR","VALUE"]
            df.to_csv(os.path.join(comparison_directory, "ReserveMarginTagTechnology.csv"), index=False)
        else:
            pd.DataFrame(
                columns=["REGION","TECHNOLOGY","YEAR","VALUE"]).to_csv(
                    os.path.join(comparison_directory, "ReserveMarginTagTechnology.csv"), index=False
                )

        # REMinProductionTarget
        if self.REMinProductionTarget is not None:
            df = json_dict_to_dataframe(self.REMinProductionTarget.data)
            df.columns = ["REGION","YEAR","VALUE"]
            df.to_csv(os.path.join(comparison_directory, "REMinProductionTarget.csv"), index=False)
        else:
            pd.DataFrame(
                columns=["REGION","YEAR","VALUE"]).to_csv(
                    os.path.join(comparison_directory, "REMinProductionTarget.csv"), index=False
                )

        