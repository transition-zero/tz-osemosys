import os

import pandas as pd

from feo.osemosys.utils import *

from .base import *


class Fuel(OSeMOSYSBase):
    # either demand (region:year:timeslice:value)
    # or annual_demand (region:year:value) must be specified;
    # SpecifiedDemandProfile may be optionally specified with annual_demand
    SpecifiedAnnualDemand: RegionYearData | None
    SpecifiedDemandProfile: RegionYearTimeData | None
    AccumulatedAnnualDemand: RegionYearData | None
    RETagFuel: RegionYearData | None  # why would this change over time??

    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["cls"]:
        #
        df_fuel = pd.read_csv(os.path.join(root_dir, "FUEL.csv"))
        df_annual_demand = pd.read_csv(os.path.join(root_dir, "SpecifiedAnnualDemand.csv"))
        df_SpecifiedDemandProfile = pd.read_csv(os.path.join(root_dir, "SpecifiedDemandProfile.csv"))
        df_AccumulatedAnnualDemand = pd.read_csv(os.path.join(root_dir, "AccumulatedAnnualDemand.csv"))
        df_RETagFuel = pd.read_csv(os.path.join(root_dir, "RETagFuel.csv"))

        assert (
            (df_SpecifiedDemandProfile.groupby(["REGION", "FUEL", "YEAR"])["VALUE"].sum() == 1.0).all(),
            "demand profiles must sum to one for all REGION, FUEL, and YEAR",
        )

        fuel_instances = []
        for fuel in df_fuel["VALUE"].values.tolist():
            fuel_instances.append(
                cls(
                    id=fuel,
                    # TODO
                    long_name=None,
                    description=None,
                    SpecifiedAnnualDemand=(
                        RegionYearData(
                            data=group_to_json(
                                g=df_annual_demand.loc[df_annual_demand["FUEL"] == fuel],
                                root_column="FUEL",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if fuel in df_annual_demand["FUEL"].values
                        else None
                    ),
                    SpecifiedDemandProfile=(
                        RegionYearTimeData(
                            data=group_to_json(
                                g=df_SpecifiedDemandProfile.loc[df_SpecifiedDemandProfile["FUEL"] == fuel],
                                root_column="FUEL",
                                data_columns=["REGION", "TIMESLICE", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if fuel in df_SpecifiedDemandProfile["FUEL"].values
                        else None
                    ),
                    AccumulatedAnnualDemand=(
                        RegionYearData(
                            data=group_to_json(
                                g=df_AccumulatedAnnualDemand.loc[
                                    df_AccumulatedAnnualDemand["FUEL"] == fuel
                                ],
                                root_column="FUEL",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if fuel in df_AccumulatedAnnualDemand["FUEL"].values
                        else None
                    ),
                    RETagFuel=(
                        RegionYearData(
                            data=group_to_json(
                                g=df_RETagFuel.loc[df_RETagFuel["FUEL"] == fuel],
                                root_column="FUEL",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if fuel in df_RETagFuel["FUEL"].values
                        else None
                    ),
                )
            )

        return fuel_instances


    def to_otoole_csv(self, comparison_directory) -> "cls":
        
        fuel = self.id

        # SpecifiedAnnualDemand
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.SpecifiedAnnualDemand, 
                         id=fuel, 
                         column_structure=["REGION", "FUEL", "YEAR", "VALUE"], 
                         id_column="FUEL", 
                         output_csv_name="SpecifiedAnnualDemand.csv")
        # SpecifiedDemandProfile
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.SpecifiedDemandProfile, 
                         id=fuel, 
                         column_structure=["REGION", "FUEL", "TIMESLICE", "YEAR", "VALUE"], 
                         id_column="FUEL", 
                         output_csv_name="SpecifiedDemandProfile.csv")
        # AccumulatedAnnualDemand        
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.AccumulatedAnnualDemand, 
                         id=fuel, 
                         column_structure=["REGION", "FUEL", "YEAR", "VALUE"], 
                         id_column="FUEL", 
                         output_csv_name="AccumulatedAnnualDemand.csv")
        # RETagFuel
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.RETagFuel, 
                         id=fuel, 
                         column_structure=["REGION", "FUEL", "YEAR", "VALUE"], 
                         id_column="FUEL", 
                         output_csv_name="RETagFuel.csv")
