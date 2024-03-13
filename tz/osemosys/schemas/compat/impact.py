import os
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, List, Union

import pandas as pd
from pydantic import BaseModel, Field

from tz.osemosys.schemas.base import OSeMOSYSData
from tz.osemosys.schemas.compat.base import OtooleCfg
from tz.osemosys.utils import group_to_json

if TYPE_CHECKING:
    from tz.osemosys.schemas.impact import Impact


class OtooleImpact(BaseModel):
    """
    Class to contain methods for converting Impact data to and from otoole style CSVs
    """

    otoole_cfg: OtooleCfg | None = Field(None)
    otoole_stems: ClassVar[dict[str : dict[str : Union[str, list[str]]]]] = {
        "AnnualEmissionLimit": {
            "attribute": "constraint_annual",
            "columns": ["REGION", "EMISSION", "YEAR", "VALUE"],
        },
        "ModelPeriodEmissionLimit": {
            "attribute": "constraint_total",
            "columns": ["REGION", "EMISSION", "VALUE"],
        },
        "AnnualExogenousEmission": {
            "attribute": "exogenous_annual",
            "columns": ["REGION", "EMISSION", "YEAR", "VALUE"],
        },
        "ModelPeriodExogenousEmission": {
            "attribute": "exogenous_total",
            "columns": ["REGION", "EMISSION", "VALUE"],
        },
        "EmissionsPenalty": {
            "attribute": "penalty",
            "columns": ["REGION", "EMISSION", "YEAR", "VALUE"],
        },
    }

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
                    otoole_cfg=otoole_cfg,
                    constraint_annual=(
                        OSeMOSYSData.RY(
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
                        OSeMOSYSData.R(
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
                        OSeMOSYSData.RY(
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
                        OSeMOSYSData.R(
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
                        OSeMOSYSData.RY(
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

    @classmethod
    def to_dataframes(cls, impacts: List["Impact"]) -> dict[str, pd.DataFrame]:
        """Write a number of Impact objects to otoole-organised dataframes.

        Args:
            impacts (List[Impact]): A list of Impact instances

        Returns:
            dict[str, pd.DataFrame]: A dictionary of dataframes
        """

        # collect constraint, exogenous, and penalty dataframes
        penalty_dfs = []
        annual_constraint_dfs = []
        total_constraint_dfs = []
        annual_exogenous_dfs = []
        total_exogenous_dfs = []

        for impact in impacts:
            if impact.penalty is not None:
                df = pd.json_normalize(impact.penalty.data).T.rename(columns={0: "VALUE"})
                df["EMISSION"] = impact.id
                df[["REGION", "YEAR"]] = pd.DataFrame(
                    df.index.str.split(".").to_list(), index=df.index
                )
                penalty_dfs.append(df)
            if impact.constraint_annual is not None:
                df = pd.json_normalize(impact.constraint_annual.data).T.rename(columns={0: "VALUE"})
                df["EMISSION"] = impact.id
                df[["REGION", "YEAR"]] = pd.DataFrame(
                    df.index.str.split(".").to_list(), index=df.index
                )
                annual_constraint_dfs.append(df)
            if impact.constraint_total is not None:
                df = pd.json_normalize(impact.constraint_total.data).T.rename(columns={0: "VALUE"})
                df["EMISSION"] = impact.id
                df["REGION"] = df.index
                total_constraint_dfs.append(df)
            if impact.exogenous_annual is not None:
                df = pd.json_normalize(impact.exogenous_annual.data).T.rename(columns={0: "VALUE"})
                df["EMISSION"] = impact.id
                df[["REGION", "YEAR"]] = pd.DataFrame(
                    df.index.str.split(".").to_list(), index=df.index
                )
                annual_exogenous_dfs.append(df)
            if impact.exogenous_total is not None:
                df = pd.json_normalize(impact.exogenous_total.data).T.rename(columns={0: "VALUE"})
                df["EMISSION"] = impact.id
                df["REGION"] = df.index
                total_exogenous_dfs.append(df)

        # collect concatenaed dfs
        dfs = {}
        if penalty_dfs:
            dfs["EmissionsPenalty"] = pd.concat(penalty_dfs)
        if annual_constraint_dfs:
            dfs["AnnualEmissionLimit"] = pd.concat(annual_constraint_dfs)
        if total_constraint_dfs:
            dfs["ModelPeriodEmissionLimit"] = pd.concat(total_constraint_dfs)
        if annual_exogenous_dfs:
            dfs["AnnualExogenousEmission"] = pd.concat(annual_exogenous_dfs)
        if total_exogenous_dfs:
            dfs["ModelPeriodExogenousEmission"] = pd.concat(total_exogenous_dfs)

        # SETS
        dfs["EMISSION"] = pd.DataFrame({"VALUE": [impact.id for impact in impacts]})

        return dfs

    @classmethod
    def to_otoole_csv(cls, impacts: List["Impact"], output_directory: str):
        """Write a number of Impact objects to otoole-organised csvs.

        Args:
            impacts (List[Impact]): A list of Impact instances
            output_directory (str): Path to the root of the otoole csv directory
        """

        # TODO: it's getting wet. Refactor into functions alongside other compat methods

        dfs = cls.to_dataframes(impacts)

        # set to csv
        dfs["EMISSION"].to_csv(os.path.join(output_directory, "EMISSION.csv"), index=False)

        # params to csv where appropriate
        for stem, _params in cls.otoole_stems.items():
            if any([(stem not in impact.otoole_cfg.empty_dfs) for impact in impacts]):
                dfs[stem].to_csv(os.path.join(output_directory, f"{stem}.csv"), index=False)

        return True
