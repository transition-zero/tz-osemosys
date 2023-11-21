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

class Commodity(OSeMOSYSBase):
    # either demand (region:year:timeslice:value)
    # or annual_demand (region:year:value) must be specified;
    # SpecifiedDemandProfile may be optionally specified with annual_demand
    SpecifiedAnnualDemand: OSeMOSYSData | None
    SpecifiedDemandProfile: OSeMOSYSData | None
    AccumulatedAnnualDemand: OSeMOSYSData | None
    RETagFuel: OSeMOSYSData | None  # why would this change over time??

    otoole_cfg: OtooleCfg | None
    otoole_stems: ClassVar[list[str]] = [
        "SpecifiedAnnualDemand",
        "SpecifiedDemandProfile",
        "AccumulatedAnnualDemand",
        "RETagFuel",
    ]

    @root_validator(pre=True)
    def construct_from_components(cls, values):
        CapacityTSpecifiedAnnualDemandoActivityUnit = values.get("SpecifiedAnnualDemand")
        SpecifiedDemandProfile = values.get("SpecifiedDemandProfile")
        AccumulatedAnnualDemand = values.get("AccumulatedAnnualDemand")
        RETagFuel = values.get("RETagFuel")

        return values

    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["cls"]:
        
        # ###########
        # Load Data #
        # ###########

        df_commodity = pd.read_csv(os.path.join(root_dir, "FUEL.csv"))
        
        dfs = {}
        otoole_cfg = OtooleCfg(empty_dfs=[])
        for key in cls.otoole_stems:
            try:
                dfs[key] = pd.read_csv(Path(root_dir) / f"{key}.csv")
                if dfs[key].empty:
                    otoole_cfg.empty_dfs.append(key)
            except FileNotFoundError:
                otoole_cfg.empty_dfs.append(key)
                dfs[key] = pd.DataFrame(columns=["FUEL"])

        assert (
            (dfs["SpecifiedDemandProfile"].groupby(["REGION", "FUEL", "YEAR"])["VALUE"].sum() == 1.0).all(),
            "demand profiles must sum to one for all REGION, FUEL, and YEAR",
        )

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
                    SpecifiedAnnualDemand=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["SpecifiedAnnualDemand"].loc[dfs["SpecifiedAnnualDemand"]["FUEL"] == commodity],
                                root_column="FUEL",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if commodity in dfs["SpecifiedAnnualDemand"]["FUEL"].values
                        else None
                    ),
                    SpecifiedDemandProfile=(
                        OSeMOSYSData(
                            data=group_to_json(
                                g=dfs["SpecifiedDemandProfile"].loc[dfs["SpecifiedDemandProfile"]["FUEL"] == commodity],
                                root_column="FUEL",
                                data_columns=["REGION", "TIMESLICE", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if commodity in dfs["SpecifiedDemandProfile"]["FUEL"].values
                        else None
                    ),
                    #TODO: why does this default year values to str rather than ints?
                    AccumulatedAnnualDemand=(   
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
                    RETagFuel=(
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


    def to_otoole_csv(self, comparison_directory) -> "cls":
        
        commodity = self.id

        # SpecifiedAnnualDemand
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.SpecifiedAnnualDemand, 
                         id=commodity, 
                         column_structure=["REGION", "FUEL", "YEAR", "VALUE"], 
                         id_column="FUEL", 
                         output_csv_name="SpecifiedAnnualDemand.csv")
        # SpecifiedDemandProfile
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.SpecifiedDemandProfile, 
                         id=commodity, 
                         column_structure=["REGION", "FUEL", "TIMESLICE", "YEAR", "VALUE"], 
                         id_column="FUEL", 
                         output_csv_name="SpecifiedDemandProfile.csv")
        # AccumulatedAnnualDemand        
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.AccumulatedAnnualDemand, 
                         id=commodity, 
                         column_structure=["REGION", "FUEL", "YEAR", "VALUE"], 
                         id_column="FUEL", 
                         output_csv_name="AccumulatedAnnualDemand.csv")
        # RETagFuel
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.RETagFuel, 
                         id=commodity, 
                         column_structure=["REGION", "FUEL", "YEAR", "VALUE"], 
                         id_column="FUEL", 
                         output_csv_name="RETagFuel.csv")
