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


class Emission(OSeMOSYSBase):
    """
    Class to contain all information pertaining to emissions restrictions and penalties (independant of technology).
    """

    # Annual emissions constraint per region, year, and emission type
    AnnualEmissionLimit: OSeMOSYSData | None
    # Total modelled period emissions constraint per region and emission type
    ModelPeriodEmissionLimit: OSeMOSYSData | None
    # Annual exogenous emission per region, year, and emission type. I.e. emissions from non-modelled sources.
    AnnualExogenousEmission: OSeMOSYSData | None
    # Total modelled period exogenous emission per region and emission type. I.e. emissions from non-modelled sources.
    ModelPeriodExogenousEmission: OSeMOSYSData | None
    # Financial EmissionsPenalty for each unit of eimssion per region, year, and emission type. E.g. used to model carbon prices.
    EmissionsPenalty: OSeMOSYSData | None

    otoole_cfg: OtooleCfg | None
    otoole_stems: ClassVar[list[str]] = [
        "AnnualEmissionLimit",
        "ModelPeriodEmissionLimit",
        "AnnualExogenousEmission",
        "ModelPeriodExogenousEmission",
        "EmissionsPenalty",
    ]

    @root_validator(pre=True)
    def construct_from_components(cls, values):
        AnnualEmissionLimit = values.get("AnnualEmissionLimit")
        ModelPeriodEmissionLimit = values.get("ModelPeriodEmissionLimit")
        AnnualExogenousEmission = values.get("AnnualExogenousEmission")
        ModelPeriodExogenousEmission = values.get("ModelPeriodExogenousEmission")
        EmissionsPenalty = values.get("EmissionsPenalty")

        return values
    
    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["cls"]:
        """
        Instantiate a number of Emission objects from otoole-organised csvs.

        Parameters
        ----------
        root_dir: str
            Path to the root of the otoole csv directory

        Returns
        -------
        List[Emission]
            A list of Emission instances that can be used downstream or dumped to json/yaml
        """

        # ###########
        # Load Data #
        # ###########

        df_emissions = pd.read_csv(os.path.join(root_dir, "EMISSION.csv"))
        
        dfs = {}
        otoole_cfg = OtooleCfg(empty_dfs=[])
        for key in cls.otoole_stems:
            try:
                dfs[key] = pd.read_csv(Path(root_dir) / f"{key}.csv")
                if dfs[key].empty:
                    otoole_cfg.empty_dfs.append(key)
            except FileNotFoundError:
                otoole_cfg.empty_dfs.append(key)
                dfs[key] = pd.DataFrame(columns=["EMISSION"])


        # ########################
        # Define class instances #
        # ########################

        emission_instances = []
        for emission in df_emissions["VALUE"].values.tolist():
            emission_instances.append(
                cls(
                    id=emission,
                    long_name=None,
                    description=None,
                    otoole_cfg=otoole_cfg,
                    AnnualEmissionLimit=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["AnnualEmissionLimit"].loc[
                                    dfs["AnnualEmissionLimit"]["EMISSION"] == emission
                                ],
                                root_column="EMISSION",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if emission in dfs["AnnualEmissionLimit"]["EMISSION"].values
                        else None
                    ),
                    ModelPeriodEmissionLimit=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["ModelPeriodEmissionLimit"].loc[
                                    dfs["ModelPeriodEmissionLimit"]["EMISSION"] == emission
                                ],
                                root_column="EMISSION",
                                data_columns=["REGION"],
                                target_column="VALUE",
                            )
                        )
                        if emission in dfs["ModelPeriodEmissionLimit"]["EMISSION"].values
                        else None
                    ),
                    AnnualExogenousEmission=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["AnnualExogenousEmission"].loc[
                                    dfs["AnnualExogenousEmission"]["EMISSION"] == emission
                                ],
                                root_column="EMISSION",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if emission in dfs["AnnualExogenousEmission"]["EMISSION"].values
                        else None
                    ),
                    ModelPeriodExogenousEmission=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["ModelPeriodExogenousEmission"].loc[
                                    dfs["ModelPeriodExogenousEmission"]["EMISSION"] == emission
                                ],
                                root_column="EMISSION",
                                data_columns=["REGION"],
                                target_column="VALUE",
                            )
                        )
                        if emission in dfs["ModelPeriodExogenousEmission"]["EMISSION"].values
                        else None
                    ),
                    EmissionsPenalty=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["EmissionsPenalty"].loc[dfs["EmissionsPenalty"]["EMISSION"] == emission],
                                root_column="EMISSION",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if emission in dfs["EmissionsPenalty"]["EMISSION"].values
                        else None
                    ),
                )
            )

        return emission_instances


    def to_otoole_csv(self, comparison_directory) -> "cls":
        
        emission = self.id

        # AnnualEmissionLimit
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.AnnualEmissionLimit, 
                         id=emission, 
                         column_structure=["REGION", "EMISSION", "YEAR", "VALUE"], 
                         id_column="EMISSION", 
                         output_csv_name="AnnualEmissionLimit.csv")
        # ModelPeriodEmissionLimit
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.ModelPeriodEmissionLimit, 
                         id=emission, 
                         column_structure=["REGION", "EMISSION", "VALUE"], 
                         id_column="EMISSION", 
                         output_csv_name="ModelPeriodEmissionLimit.csv")
        # AnnualExogenousEmission
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.AnnualExogenousEmission, 
                         id=emission, 
                         column_structure=["REGION", "EMISSION", "YEAR", "VALUE"], 
                         id_column="EMISSION", 
                         output_csv_name="AnnualExogenousEmission.csv")
        # ModelPeriodExogenousEmission
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.ModelPeriodExogenousEmission, 
                         id=emission, 
                         column_structure=["REGION", "EMISSION", "VALUE"], 
                         id_column="EMISSION", 
                         output_csv_name="ModelPeriodExogenousEmission.csv")
        # EmissionsPenalty
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.EmissionsPenalty, 
                         id=emission, 
                         column_structure=["REGION", "EMISSION", "YEAR", "VALUE"], 
                         id_column="EMISSION", 
                         output_csv_name="EmissionsPenalty.csv")

