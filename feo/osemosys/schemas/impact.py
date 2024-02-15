import os
from pathlib import Path
from typing import ClassVar, List, Union

import pandas as pd
from pydantic import BaseModel, model_validator

from feo.osemosys.schemas.validation.impact_validation import (
    exogenous_annual_within_constraint,
    exogenous_total_within_constraint,
)
from feo.osemosys.utils import group_to_json

from .base import OSeMOSYSBase, OSeMOSYSData


class OtooleCfg(BaseModel):
    """
    Paramters needed to round-trip csvs from otoole
    """

    empty_dfs: List[str] | None


class Impact(OSeMOSYSBase):
    """
    Class to contain all information pertaining to emissions restrictions and penalties
    (independant of technology).
    """

    # Annual emissions constraint per region, year, and emission type
    constraint_annual: OSeMOSYSData | None
    # Total modelled period emissions constraint per region and emission type
    constraint_total: OSeMOSYSData | None
    # Annual exogenous emission per region, year, and emission type
    # I.e. emissions from non-modelled sources
    exogenous_annual: OSeMOSYSData | None
    # Total modelled period exogenous emission per region and emission type
    # I.e. emissions from non-modelled sources
    exogenous_total: OSeMOSYSData | None
    # Financial penalty for each unit of eimssion per region, year, and emission type
    # E.g. used to model carbon prices
    penalty: OSeMOSYSData | None

    otoole_cfg: OtooleCfg | None
    otoole_stems: ClassVar[dict[str : dict[str : Union[str, list[str]]]]] = {
        "AnnualEmissionLimit": {
            "attribute": "constraint_annual",
            "column_structure": ["REGION", "EMISSION", "YEAR", "VALUE"],
        },
        "ModelPeriodEmissionLimit": {
            "attribute": "constraint_total",
            "column_structure": ["REGION", "EMISSION", "VALUE"],
        },
        "AnnualExogenousEmission": {
            "attribute": "exogenous_annual",
            "column_structure": ["REGION", "EMISSION", "YEAR", "VALUE"],
        },
        "ModelPeriodExogenousEmission": {
            "attribute": "exogenous_total",
            "column_structure": ["REGION", "EMISSION", "VALUE"],
        },
        "EmissionsPenalty": {
            "attribute": "penalty",
            "column_structure": ["REGION", "EMISSION", "YEAR", "VALUE"],
        },
    }

    @model_validator(mode="before")
    def validator(cls, values):
        values = exogenous_annual_within_constraint(values)
        values = exogenous_total_within_constraint(values)
        return values

    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["Impact"]:
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
        for key in list(cls.otoole_stems):
            try:
                dfs[key] = pd.read_csv(Path(root_dir) / f"{key}.csv")
                if dfs[key].empty:
                    otoole_cfg.empty_dfs.append(key)
            except FileNotFoundError:
                otoole_cfg.empty_dfs.append(key)
                dfs[key] = pd.DataFrame(columns=["EMISSION"])

        # ###################
        # Basic Data Checks #
        #####################

        # Check no duplicates in EMISSION.csv
        if len(df_impacts) != len(df_impacts["VALUE"].unique()):
            raise ValueError("EMISSION.csv must not contain duplicate values")

        # Check impact names are consistent with those in EMISSION.csv
        for df in dfs.keys():
            for impact in dfs[df]["EMISSION"].unique():
                if impact not in list(df_impacts["VALUE"]):
                    raise ValueError(f"{impact} given in {df}.csv but not in EMISSION.csv")

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
                                g=dfs["EmissionsPenalty"].loc[
                                    dfs["EmissionsPenalty"]["EMISSION"] == impact
                                ],
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
