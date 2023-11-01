import os

import pandas as pd

from feo.osemosys.utils import *

from .base import *


class Emission(OSeMOSYSBase):
    """
    Class to contain all information pertaining to emissions restrictions and penalties (independant of technology).
    """

    # Annual emissions constraint per region, year, and emission type
    AnnualEmissionLimit: RegionTechnologyYearData | None
    # Total modelled period emissions constraint per region and emission type
    ModelPeriodEmissionLimit: RegionTechnologyYearData | None
    # Annual exogenous emission per region, year, and emission type. I.e. emissions from non-modelled sources.
    AnnualExogenousEmission: RegionTechnologyYearData | None
    # Total modelled period exogenous emission per region and emission type. I.e. emissions from non-modelled sources.
    ModelPeriodExogenousEmission: RegionTechnologyYearData | None
    # Financial EmissionsPenalty for each unit of eimssion per region, year, and emission type. E.g. used to model carbon prices.
    EmissionsPenalty: RegionTechnologyYearData | None

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

        df_emissions = pd.read_csv(os.path.join(root_dir, "EMISSION.csv"))
        df_AnnualEmissionLimit = pd.read_csv(os.path.join(root_dir, "AnnualEmissionLimit.csv"))
        df_ModelPeriodEmissionLimit = pd.read_csv(os.path.join(root_dir, "ModelPeriodEmissionLimit.csv"))
        df_AnnualExogenousEmission = pd.read_csv(os.path.join(root_dir, "AnnualExogenousEmission.csv"))
        df_ModelPeriodExogenousEmission = pd.read_csv(os.path.join(root_dir, "ModelPeriodExogenousEmission.csv"))
        df_EmissionsPenalty = pd.read_csv(os.path.join(root_dir, "EmissionsPenalty.csv"))

        emission_instances = []
        for emission in df_emissions["VALUE"].values.tolist():
            emission_instances.append(
                cls(
                    id=emission,
                    long_name=None,
                    description=None,
                    AnnualEmissionLimit=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_AnnualEmissionLimit.loc[
                                    df_AnnualEmissionLimit["EMISSION"] == emission
                                ],
                                root_column="EMISSION",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if emission in df_AnnualEmissionLimit["EMISSION"].values
                        else None
                    ),
                    ModelPeriodEmissionLimit=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_ModelPeriodEmissionLimit.loc[
                                    df_ModelPeriodEmissionLimit["EMISSION"] == emission
                                ],
                                root_column="EMISSION",
                                data_columns=["REGION"],
                                target_column="VALUE",
                            )
                        )
                        if emission in df_ModelPeriodEmissionLimit["EMISSION"].values
                        else None
                    ),
                    AnnualExogenousEmission=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_AnnualExogenousEmission.loc[
                                    df_AnnualExogenousEmission["EMISSION"] == emission
                                ],
                                root_column="EMISSION",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if emission in df_AnnualExogenousEmission["EMISSION"].values
                        else None
                    ),
                    ModelPeriodExogenousEmission=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_ModelPeriodExogenousEmission.loc[
                                    df_ModelPeriodExogenousEmission["EMISSION"] == emission
                                ],
                                root_column="EMISSION",
                                data_columns=["REGION"],
                                target_column="VALUE",
                            )
                        )
                        if emission in df_ModelPeriodExogenousEmission["EMISSION"].values
                        else None
                    ),
                    EmissionsPenalty=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_EmissionsPenalty.loc[df_EmissionsPenalty["EMISSION"] == emission],
                                root_column="EMISSION",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if emission in df_EmissionsPenalty["EMISSION"].values
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

