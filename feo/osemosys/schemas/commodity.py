import os
from pathlib import Path
from typing import ClassVar, List, Union

import pandas as pd
from pydantic import BaseModel, root_validator

from feo.osemosys.schemas.validation.commodity_validation import demand_profile_sums_one
from feo.osemosys.utils import group_to_json

from .base import OSeMOSYSBase, OSeMOSYSData


class OtooleCfg(BaseModel):
    """
    Paramters needed to round-trip csvs from otoole
    """

    empty_dfs: List[str] | None


class Commodity(OSeMOSYSBase):
    # either demand (region:year:timeslice:value)
    # or annual_demand (region:year:value) must be specified;
    # demand_profile may be optionally specified with annual_demand
    demand_annual: OSeMOSYSData | None
    demand_profile: OSeMOSYSData | None
    accumulated_demand: OSeMOSYSData | None
    is_renewable: OSeMOSYSData | None  # why would this change over time??

    otoole_cfg: OtooleCfg | None
    otoole_stems: ClassVar[dict[str : dict[str : Union[str, list[str]]]]] = {
        "SpecifiedAnnualDemand": {
            "attribute": "demand_annual",
            "column_structure": ["REGION", "FUEL", "YEAR", "VALUE"],
        },
        "SpecifiedDemandProfile": {
            "attribute": "demand_profile",
            "column_structure": ["REGION", "FUEL", "TIMESLICE", "YEAR", "VALUE"],
        },
        "AccumulatedAnnualDemand": {
            "attribute": "accumulated_demand",
            "column_structure": ["REGION", "FUEL", "YEAR", "VALUE"],
        },
        "RETagFuel": {
            "attribute": "is_renewable",
            "column_structure": ["REGION", "FUEL", "YEAR", "VALUE"],
        },
    }

    @root_validator(pre=True)
    def validation(cls, values):
        values = demand_profile_sums_one(values)
        return values

    @classmethod
    def from_otoole_csv(cls, root_dir):
        # ###########
        # Load Data #
        # ###########

        df_commodity = pd.read_csv(os.path.join(root_dir, "FUEL.csv"))

        dfs = {}
        otoole_cfg = OtooleCfg(empty_dfs=[])
        for key in list(cls.otoole_stems):
            try:
                dfs[key] = pd.read_csv(Path(root_dir) / f"{key}.csv")
                if dfs[key].empty:
                    otoole_cfg.empty_dfs.append(key)
            except FileNotFoundError:
                otoole_cfg.empty_dfs.append(key)
                dfs[key] = pd.DataFrame(columns=["FUEL"])

        # ###################
        # Basic Data Checks #
        #####################

        # Check no duplicates in FUEL.csv
        if len(df_commodity) != len(df_commodity["VALUE"].unique()):
            raise ValueError("FUEL.csv must not contain duplicate values")

        # Check commodity names are consistent with those in FUEL.csv
        for df in dfs.keys():
            for commodity in dfs[df]["FUEL"].unique():
                if commodity not in list(df_commodity["VALUE"]):
                    raise ValueError(f"{commodity} given in {df}.csv but not in FUEL.csv")

        # ########################
        # Define class instances #
        # ########################

        commodity_instances = []
        for commodity in df_commodity["VALUE"].values.tolist():
            commodity_instances.append(
                cls(
                    id=commodity,
                    # TODO
                    long_name=None,
                    description=None,
                    otoole_cfg=otoole_cfg,
                    demand_annual=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["SpecifiedAnnualDemand"].loc[
                                    dfs["SpecifiedAnnualDemand"]["FUEL"] == commodity
                                ],
                                root_column="FUEL",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if commodity in dfs["SpecifiedAnnualDemand"]["FUEL"].values
                        else None
                    ),
                    demand_profile=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["SpecifiedDemandProfile"].loc[
                                    dfs["SpecifiedDemandProfile"]["FUEL"] == commodity
                                ],
                                root_column="FUEL",
                                data_columns=["REGION", "TIMESLICE", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if commodity in dfs["SpecifiedDemandProfile"]["FUEL"].values
                        else None
                    ),
                    # TODO: why does this default year values to str rather than ints?
                    accumulated_demand=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["AccumulatedAnnualDemand"].loc[
                                    dfs["AccumulatedAnnualDemand"]["FUEL"] == commodity
                                ],
                                root_column="FUEL",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if commodity in dfs["AccumulatedAnnualDemand"]["FUEL"].values
                        else None
                    ),
                    is_renewable=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["RETagFuel"].loc[dfs["RETagFuel"]["FUEL"] == commodity],
                                root_column="FUEL",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if commodity in dfs["RETagFuel"]["FUEL"].values
                        else None
                    ),
                )
            )

        return commodity_instances
