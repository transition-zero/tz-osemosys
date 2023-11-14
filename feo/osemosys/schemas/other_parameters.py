import os

import pandas as pd

from feo.osemosys.utils import *

from .base import *


class OtherParameters(OSeMOSYSBase):
    """
    Class to contain all other parameters
    """

    MODE_OF_OPERATION: list[int]
    DepreciationMethod: RegionData | None
    DiscountRate: RegionData | None
    DiscountRateIdv: RegionTechnologyYearData | None
    DiscountRateStorage: RegionCommodityYearData | None
    ReserveMargin: RegionYearData | None
    ReserveMarginTagFuel: OSeMOSYSDataInt | None
    ReserveMarginTagTechnology: OSeMOSYSDataInt | None
    REMinProductionTarget: RegionYearData | None

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

        df_MODE_OF_OPERATION = pd.read_csv(os.path.join(root_dir, "MODE_OF_OPERATION.csv"))
        df_DepreciationMethod = pd.read_csv(os.path.join(root_dir, "DepreciationMethod.csv"))
        df_DiscountRate = pd.read_csv(os.path.join(root_dir, "DiscountRate.csv"))
        try:
            df_DiscountRateIdv = pd.read_csv(os.path.join(root_dir, "DiscountRateIdv.csv"))
        except:
            df_DiscountRateIdv = pd.DataFrame(columns=["REGION","TECHNOLOGY","VALUE"])
        df_DiscountRateStorage = pd.read_csv(os.path.join(root_dir, "DiscountRateStorage.csv"))
        df_ReserveMargin = pd.read_csv(os.path.join(root_dir, "ReserveMargin.csv"))
        df_ReserveMarginTagFuel = pd.read_csv(os.path.join(root_dir, "ReserveMarginTagFuel.csv"))
        df_ReserveMarginTagTechnology = pd.read_csv(os.path.join(root_dir, "ReserveMarginTagTechnology.csv"))
        df_REMinProductionTarget = pd.read_csv(os.path.join(root_dir, "REMinProductionTarget.csv"))

        return cls(
            id="OtherParameters",
            # TODO
            long_name=None,
            description=None,
            MODE_OF_OPERATION=df_MODE_OF_OPERATION["VALUE"].values.tolist(),
            DepreciationMethod=(
                RegionData(
                    data=group_to_json(
                        g=df_DepreciationMethod,
                        data_columns=["REGION"],
                        target_column="VALUE",
                    )
                )
                if not df_DepreciationMethod.empty
                else None
            ),
            DiscountRate=(
                RegionData(
                    data=group_to_json(
                        g=df_DiscountRate,
                        data_columns=["REGION"],
                        target_column="VALUE",
                    )
                )
                if not df_DiscountRate.empty
                else None
            ),
            DiscountRateIdv=(
                RegionData(
                    data=group_to_json(
                        g=df_DiscountRateIdv,
                        data_columns=["REGION","TECHNOLOGY"],
                        target_column="VALUE",
                    )
                )
                if not df_DiscountRateIdv.empty
                else None
            ),
            DiscountRateStorage=(
                RegionData(
                    data=group_to_json(
                        g=df_DiscountRateStorage,
                        data_columns=["REGION","STORAGE"],
                        target_column="VALUE",
                    )
                )
                if not df_DiscountRateStorage.empty
                else None
            ),
            ReserveMargin=(
                RegionYearData(
                    data=group_to_json(
                        g=df_ReserveMargin,
                        data_columns=["REGION","YEAR"],
                        target_column="VALUE",
                    )
                )
                if not df_ReserveMargin.empty
                else None
            ),
            ReserveMarginTagFuel=(
                OSeMOSYSDataInt(
                    data=group_to_json(
                        g=df_ReserveMarginTagFuel,
                        data_columns=["REGION","FUEL","YEAR"],
                        target_column="VALUE",
                    )
                )
                if not df_ReserveMarginTagFuel.empty
                else None
            ),
            ReserveMarginTagTechnology=(
                OSeMOSYSDataInt(
                    data=group_to_json(
                        g=df_ReserveMarginTagTechnology,
                        data_columns=["REGION","TECHNOLOGY","YEAR"],
                        target_column="VALUE",
                    )
                )
                if not df_ReserveMarginTagTechnology.empty
                else None
            ),
            REMinProductionTarget=(
                RegionYearData(
                    data=group_to_json(
                        g=df_REMinProductionTarget,
                        data_columns=["REGION","YEAR"],
                        target_column="VALUE",
                    )
                )
                if not df_REMinProductionTarget.empty
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

        