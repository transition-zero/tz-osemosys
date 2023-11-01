import os

import pandas as pd

from feo.osemosys.utils import *

from .base import *


class Emission(OSeMOSYSBase):
    """
    Class to contain all information pertaining to emissions restrictions and penalties (independant of technology).
    """

    # Annual emissions constraint per region, year, and emission type
    constraint_annual: RegionTechnologyYearData | None
    # Total modelled period emissions constraint per region and emission type
    constraint_total: RegionTechnologyYearData | None
    # Annual exogenous emission per region, year, and emission type. I.e. emissions from non-modelled sources.
    exogenous_annual: RegionTechnologyYearData | None
    # Total modelled period exogenous emission per region and emission type. I.e. emissions from non-modelled sources.
    exogenous_total: RegionTechnologyYearData | None
    # Financial penalty for each unit of eimssion per region, year, and emission type. E.g. used to model carbon prices.
    penalty: RegionTechnologyYearData | None

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
        df_constraint_annual = pd.read_csv(os.path.join(root_dir, "AnnualEmissionLimit.csv"))
        df_constraint_total = pd.read_csv(os.path.join(root_dir, "ModelPeriodEmissionLimit.csv"))
        df_exogenous_annual = pd.read_csv(os.path.join(root_dir, "AnnualExogenousEmission.csv"))
        df_exogenous_total = pd.read_csv(os.path.join(root_dir, "ModelPeriodExogenousEmission.csv"))
        df_penalty = pd.read_csv(os.path.join(root_dir, "EmissionsPenalty.csv"))

        emission_instances = []
        for emission in df_emissions["VALUE"].values.tolist():
            emission_instances.append(
                cls(
                    id=emission,
                    long_name=None,
                    description=None,
                    constraint_annual=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_constraint_annual.loc[
                                    df_constraint_annual["EMISSION"] == emission
                                ],
                                root_column="EMISSION",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if emission in df_constraint_annual["EMISSION"].values
                        else None
                    ),
                    constraint_total=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_constraint_total.loc[
                                    df_constraint_total["EMISSION"] == emission
                                ],
                                root_column="EMISSION",
                                data_columns=["REGION"],
                                target_column="VALUE",
                            )
                        )
                        if emission in df_constraint_total["EMISSION"].values
                        else None
                    ),
                    exogenous_annual=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_exogenous_annual.loc[
                                    df_exogenous_annual["EMISSION"] == emission
                                ],
                                root_column="EMISSION",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if emission in df_exogenous_annual["EMISSION"].values
                        else None
                    ),
                    exogenous_total=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_exogenous_total.loc[
                                    df_exogenous_total["EMISSION"] == emission
                                ],
                                root_column="EMISSION",
                                data_columns=["REGION"],
                                target_column="VALUE",
                            )
                        )
                        if emission in df_exogenous_total["EMISSION"].values
                        else None
                    ),
                    penalty=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_penalty.loc[df_penalty["EMISSION"] == emission],
                                root_column="EMISSION",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if emission in df_penalty["EMISSION"].values
                        else None
                    ),
                )
            )

            return emission_instances


    def to_otoole_csv(self, comparison_directory) -> "cls":
        
        emission = self.id

        # constraint_annual
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.constraint_annual, 
                         id=emission, 
                         column_structure=["REGION", "EMISSION", "YEAR", "VALUE"], 
                         id_column="EMISSION", 
                         output_csv_name="AnnualEmissionLimit.csv")
        # constraint_total
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.constraint_total, 
                         id=emission, 
                         column_structure=["REGION", "EMISSION", "VALUE"], 
                         id_column="EMISSION", 
                         output_csv_name="ModelPeriodEmissionLimit.csv")
        # exogenous_annual
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.exogenous_annual, 
                         id=emission, 
                         column_structure=["REGION", "EMISSION", "YEAR", "VALUE"], 
                         id_column="EMISSION", 
                         output_csv_name="AnnualExogenousEmission.csv")
        # exogenous_total
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.exogenous_total, 
                         id=emission, 
                         column_structure=["REGION", "EMISSION", "VALUE"], 
                         id_column="EMISSION", 
                         output_csv_name="ModelPeriodExogenousEmission.csv")
        # penalty
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.penalty, 
                         id=emission, 
                         column_structure=["REGION", "EMISSION", "YEAR", "VALUE"], 
                         id_column="EMISSION", 
                         output_csv_name="EmissionsPenalty.csv")

