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
    from tz.osemosys.schemas.storage import Storage


class OtooleStorage(BaseModel):
    """
    Class to contain methods for converting Storage data to and from otoole style CSVs
    """

    otoole_cfg: OtooleCfg | None = Field(None)
    otoole_stems: ClassVar[dict[str : dict[str : Union[str, list[str]]]]] = {
        "CapitalCostStorage": {
            "attribute": "capex",
            "columns": ["REGION", "STORAGE", "YEAR", "VALUE"],
        },
        "OperationalLifeStorage": {
            "attribute": "operating_life",
            "columns": ["REGION", "STORAGE", "VALUE"],
        },
        "MinStorageCharge": {
            "attribute": "minimum_charge",
            "columns": ["REGION", "STORAGE", "YEAR", "VALUE"],
        },
        "StorageLevelStart": {
            "attribute": "initial_level",
            "columns": ["REGION", "STORAGE", "VALUE"],
        },
        "ResidualStorageCapacity": {
            "attribute": "residual_capacity",
            "columns": ["REGION", "STORAGE", "YEAR", "VALUE"],
        },
        "StorageMaxDischargeRate": {
            "attribute": "max_discharge_rate",
            "columns": ["REGION", "STORAGE", "VALUE"],
        },
        "StorageMaxChargeRate": {
            "attribute": "max_charge_rate",
            "columns": ["REGION", "STORAGE", "VALUE"],
        },
    }

    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["Storage"]:
        #############
        # Load Data #
        #############

        df_storage_technologies = pd.read_csv(os.path.join(root_dir, "STORAGE.csv"))

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

        # Check no duplicates in STORAGE.csv
        if len(df_storage_technologies) != len(df_storage_technologies["VALUE"].unique()):
            raise ValueError("STORAGE.csv must not contain duplicate values")

        # Check storage technology names are consistent with those in STORAGE.csv
        for df in dfs.keys():
            for storage in dfs[df]["STORAGE"].unique():
                if storage not in list(df_storage_technologies["VALUE"]):
                    raise ValueError(f"{storage} given in {df}.csv but not in STORAGE.csv")

        ##########################
        # Define class instances #
        ##########################

        storage_instances = []
        for storage in df_storage_technologies["VALUE"].values.tolist():
            data_json_format = {}
            for stem in list(cls.otoole_stems):
                # If input CSV present
                if stem in dfs:
                    data_columns = dfs[stem].columns.tolist()
                    data_columns.remove("STORAGE")
                    data_columns.remove("VALUE")
                    data_json_format[stem] = (
                        group_to_json(
                            g=dfs[stem].loc[dfs[stem]["STORAGE"] == storage],
                            root_column="STORAGE",
                            data_columns=data_columns,
                            target_column="VALUE",
                        )
                        if storage in dfs[stem]["STORAGE"].values
                        else None
                    )
                # If input CSV missing
                else:
                    data_json_format[stem] = None

            storage_instances.append(
                cls(
                    id=storage,
                    otoole_cfg=otoole_cfg,
                    capex=(
                        OSeMOSYSData.RY(data=data_json_format["CapitalCostStorage"])
                        if data_json_format["CapitalCostStorage"] is not None
                        else None
                    ),
                    operating_life=(
                        OSeMOSYSData.R.Int(data=data_json_format["OperationalLifeStorage"])
                        if data_json_format["OperationalLifeStorage"] is not None
                        else None
                    ),
                    minimum_charge=(
                        OSeMOSYSData.RY(data=data_json_format["MinStorageCharge"])
                        if data_json_format["MinStorageCharge"] is not None
                        else defaults.technology_storage_minimum_charge
                    ),
                    initial_level=(
                        OSeMOSYSData.R(data=data_json_format["StorageLevelStart"])
                        if data_json_format["StorageLevelStart"] is not None
                        else defaults.technology_storage_initial_level
                    ),
                    residual_capacity=(
                        OSeMOSYSData.RY(data=data_json_format["ResidualStorageCapacity"])
                        if data_json_format["ResidualStorageCapacity"] is not None
                        else defaults.technology_storage_residual_capacity
                    ),
                    max_discharge_rate=(
                        OSeMOSYSData.R(data=data_json_format["StorageMaxDischargeRate"])
                        if data_json_format["StorageMaxDischargeRate"] is not None
                        else None
                    ),
                    max_charge_rate=(
                        OSeMOSYSData.R(data=data_json_format["StorageMaxChargeRate"])
                        if data_json_format["StorageMaxChargeRate"] is not None
                        else None
                    ),
                )
            )

        return storage_instances

    @classmethod
    def to_dataframes(cls, storage: List["Storage"]) -> dict[str, pd.DataFrame]:
        """Write a number of Storage objects to otoole-organised dataframes.

        Args:
            storage (List[Storage]): A list of Storage instances

        Returns:
            dict[str, pd.DataFrame]: A dictionary of dataframes
        """

        # collect parameter dataframes
        capex_dfs = []
        operating_life_dfs = []
        minimum_charge_dfs = []
        initial_level_dfs = []
        residual_capacity_dfs = []
        max_discharge_rate_dfs = []
        max_charge_rate_dfs = []

        for sto in storage:
            if sto.capex is not None:
                df = pd.json_normalize(sto.capex.data).T.rename(columns={0: "VALUE"})
                df["STORAGE"] = sto.id
                df[["REGION", "YEAR"]] = pd.DataFrame(
                    df.index.str.split(".").to_list(), index=df.index
                )
                capex_dfs.append(df)
            if sto.operating_life is not None:
                df = pd.json_normalize(sto.operating_life.data).T.rename(columns={0: "VALUE"})
                df["STORAGE"] = sto.id
                df["REGION"] = df.index
                operating_life_dfs.append(df)
            if sto.minimum_charge is not None:
                df = pd.json_normalize(sto.minimum_charge.data).T.rename(columns={0: "VALUE"})
                df["STORAGE"] = sto.id
                df[["REGION", "YEAR"]] = pd.DataFrame(
                    df.index.str.split(".").to_list(), index=df.index
                )
                minimum_charge_dfs.append(df)
            if sto.initial_level is not None:
                df = pd.json_normalize(sto.initial_level.data).T.rename(columns={0: "VALUE"})
                df["STORAGE"] = sto.id
                df["REGION"] = df.index
                initial_level_dfs.append(df)
            if sto.residual_capacity is not None:
                df = pd.json_normalize(sto.residual_capacity.data).T.rename(columns={0: "VALUE"})
                df["STORAGE"] = sto.id
                df[["REGION", "YEAR"]] = pd.DataFrame(
                    df.index.str.split(".").to_list(), index=df.index
                )
                residual_capacity_dfs.append(df)
            if sto.max_discharge_rate is not None:
                df = pd.json_normalize(sto.max_discharge_rate.data).T.rename(columns={0: "VALUE"})
                df["STORAGE"] = sto.id
                df["REGION"] = df.index
                max_discharge_rate_dfs.append(df)
            if sto.max_charge_rate is not None:
                df = pd.json_normalize(sto.max_charge_rate.data).T.rename(columns={0: "VALUE"})
                df["STORAGE"] = sto.id
                df["REGION"] = df.index
                max_charge_rate_dfs.append(df)

        # collect concatenaed dfs
        dfs = {}
        if capex_dfs:
            dfs["CapitalCostStorage"] = pd.concat(capex_dfs)
        if operating_life_dfs:
            dfs["OperationalLifeStorage"] = pd.concat(operating_life_dfs)
        if minimum_charge_dfs:
            dfs["MinStorageCharge"] = pd.concat(minimum_charge_dfs)
        if initial_level_dfs:
            dfs["StorageLevelStart"] = pd.concat(initial_level_dfs)
        if residual_capacity_dfs:
            dfs["ResidualStorageCapacity"] = pd.concat(residual_capacity_dfs)
        if max_discharge_rate_dfs:
            dfs["StorageMaxDischargeRate"] = pd.concat(max_discharge_rate_dfs)
        if max_charge_rate_dfs:
            dfs["StorageMaxChargeRate"] = pd.concat(max_charge_rate_dfs)

        # SETS
        dfs["STORAGE"] = pd.DataFrame({"VALUE": [sto.id for sto in storage]})

        return dfs

    @classmethod
    def to_otoole_csv(cls, storage: List["Storage"], output_directory: str):
        """Write a number of Storage objects to otoole-organised csvs.

        Args:
            storage_technologies (List[Storage]): A list of Storage instances
            output_directory (str): Path to the root of the otoole csv directory
        """

        dfs = cls.to_dataframes(storage)

        # set to csv
        dfs["STORAGE"].to_csv(os.path.join(output_directory, "STORAGE.csv"), index=False)

        # params to csv where appropriate
        for stem, _params in cls.otoole_stems.items():
            if any([(stem not in sto.otoole_cfg.empty_dfs) for sto in storage]):
                dfs[stem].to_csv(os.path.join(output_directory, f"{stem}.csv"), index=False)

        return True
