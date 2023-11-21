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


class Impact(OSeMOSYSBase):
    """
    Class to contain all information pertaining to emissions restrictions and penalties (independant of technology).
    """

    # Annual emissions constraint per region, year, and emission type
    constraint_annual: OSeMOSYSData | None
    # Total modelled period emissions constraint per region and emission type
    constraint_total: OSeMOSYSData | None
    # Annual exogenous emission per region, year, and emission type. I.e. emissions from non-modelled sources.
    exogenous_annual: OSeMOSYSData | None
    # Total modelled period exogenous emission per region and emission type. I.e. emissions from non-modelled sources.
    exogenous_total: OSeMOSYSData | None
    # Financial penalty for each unit of eimssion per region, year, and emission type. E.g. used to model carbon prices.
    penalty: OSeMOSYSData | None

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
        constraint_annual = values.get("constraint_annual")
        constraint_total = values.get("constraint_total")
        exogenous_annual = values.get("exogenous_annual")
        exogenous_total = values.get("exogenous_total")
        penalty = values.get("penalty")

        return values
    
    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["cls"]:
        """
        Instantiate a number of Impact objects from otoole-organised csvs.

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

        df_impacts = pd.read_csv(os.path.join(root_dir, "EMISSION.csv"))
        
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

        impact_instances = []
        for impact in df_impacts["VALUE"].values.tolist():
            impact_instances.append(
                cls(
                    id=impact,
                    long_name=None,
                    description=None,
                    otoole_cfg=otoole_cfg,
                    constraint_annual=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["AnnualEmissionLimit"].loc[
                                    dfs["AnnualEmissionLimit"]["EMISSION"] == impact
                                ],
                                root_column="EMISSION",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if impact in dfs["AnnualEmissionLimit"]["EMISSION"].values
                        else None
                    ),
                    constraint_total=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["ModelPeriodEmissionLimit"].loc[
                                    dfs["ModelPeriodEmissionLimit"]["EMISSION"] == impact
                                ],
                                root_column="EMISSION",
                                data_columns=["REGION"],
                                target_column="VALUE",
                            )
                        )
                        if impact in dfs["ModelPeriodEmissionLimit"]["EMISSION"].values
                        else None
                    ),
                    exogenous_annual=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["AnnualExogenousEmission"].loc[
                                    dfs["AnnualExogenousEmission"]["EMISSION"] == impact
                                ],
                                root_column="EMISSION",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if impact in dfs["AnnualExogenousEmission"]["EMISSION"].values
                        else None
                    ),
                    exogenous_total=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["ModelPeriodExogenousEmission"].loc[
                                    dfs["ModelPeriodExogenousEmission"]["EMISSION"] == impact
                                ],
                                root_column="EMISSION",
                                data_columns=["REGION"],
                                target_column="VALUE",
                            )
                        )
                        if impact in dfs["ModelPeriodExogenousEmission"]["EMISSION"].values
                        else None
                    ),
                    penalty=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["EmissionsPenalty"].loc[dfs["EmissionsPenalty"]["EMISSION"] == impact],
                                root_column="EMISSION",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if impact in dfs["EmissionsPenalty"]["EMISSION"].values
                        else None
                    ),
                )
            )

        return impact_instances


    def to_otoole_csv(self, comparison_directory) -> "cls":
        
        impact = self.id

        # constraint_annual
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.constraint_annual, 
                         id=impact, 
                         column_structure=["REGION", "EMISSION", "YEAR", "VALUE"], 
                         id_column="EMISSION", 
                         output_csv_name="AnnualEmissionLimit.csv")
        # constraint_total
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.constraint_total, 
                         id=impact, 
                         column_structure=["REGION", "EMISSION", "VALUE"], 
                         id_column="EMISSION", 
                         output_csv_name="ModelPeriodEmissionLimit.csv")
        # exogenous_annual
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.exogenous_annual, 
                         id=impact, 
                         column_structure=["REGION", "EMISSION", "YEAR", "VALUE"], 
                         id_column="EMISSION", 
                         output_csv_name="AnnualExogenousEmission.csv")
        # exogenous_total
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.exogenous_total, 
                         id=impact, 
                         column_structure=["REGION", "EMISSION", "VALUE"], 
                         id_column="EMISSION", 
                         output_csv_name="ModelPeriodExogenousEmission.csv")
        # penalty
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.penalty, 
                         id=impact, 
                         column_structure=["REGION", "EMISSION", "YEAR", "VALUE"], 
                         id_column="EMISSION", 
                         output_csv_name="EmissionsPenalty.csv")

