import os

import pandas as pd

from feo.osemosys.utils import *

from .base import *


class Commodity(OSeMOSYSBase):
    # either demand (region:year:timeslice:value)
    # or annual_demand (region:year:value) must be specified;
    # demand_profile may be optionally specified with annual_demand
    demand_annual: RegionYearData | None
    demand_profile: RegionYearTimeData | None
    accumulated_demand: RegionYearData | None
    is_renewable: RegionYearData | None  # why would this change over time??

    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["cls"]:
        #
        df_fuel = pd.read_csv(os.path.join(root_dir, "FUEL.csv"))
        df_annual_demand = pd.read_csv(os.path.join(root_dir, "SpecifiedAnnualDemand.csv"))
        df_demand_profile = pd.read_csv(os.path.join(root_dir, "SpecifiedDemandProfile.csv"))
        df_accumulated_demand = pd.read_csv(os.path.join(root_dir, "AccumulatedAnnualDemand.csv"))
        df_re_tag = pd.read_csv(os.path.join(root_dir, "RETagFuel.csv"))

        assert (
            (df_demand_profile.groupby(["REGION", "FUEL", "YEAR"])["VALUE"].sum() == 1.0).all(),
            "demand profiles must sum to one for all REGION, FUEL, and YEAR",
        )

        commodity_instances = []
        for commodity in df_fuel["VALUE"].values.tolist():
            commodity_instances.append(
                cls(
                    id=commodity,
                    # TODO
                    long_name=None,
                    description=None,
                    demand_annual=(
                        RegionYearData(
                            data=group_to_json(
                                g=df_annual_demand.loc[df_annual_demand["FUEL"] == commodity],
                                root_column="FUEL",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if commodity in df_annual_demand["FUEL"].values
                        else None
                    ),
                    demand_profile=(
                        RegionYearTimeData(
                            data=group_to_json(
                                g=df_demand_profile.loc[df_demand_profile["FUEL"] == commodity],
                                root_column="FUEL",
                                data_columns=["REGION", "TIMESLICE", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if commodity in df_demand_profile["FUEL"].values
                        else None
                    ),
                    accumulated_demand=(
                        RegionYearData(
                            data=group_to_json(
                                g=df_accumulated_demand.loc[
                                    df_accumulated_demand["FUEL"] == commodity
                                ],
                                root_column="FUEL",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if commodity in df_accumulated_demand["FUEL"].values
                        else None
                    ),
                    is_renewable=(
                        RegionYearData(
                            data=group_to_json(
                                g=df_re_tag.loc[df_re_tag["FUEL"] == commodity],
                                root_column="FUEL",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if commodity in df_re_tag["FUEL"].values
                        else None
                    ),
                )
            )

        return commodity_instances


    def to_otoole_csv(self, comparison_directory) -> "cls":
        
        commodity = self.id

        # demand_annual
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.demand_annual, 
                         id=commodity, 
                         column_structure=["REGION", "FUEL", "YEAR", "VALUE"], 
                         id_column="FUEL", 
                         output_csv_name="SpecifiedAnnualDemand.csv")
        # demand_profile
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.demand_profile, 
                         id=commodity, 
                         column_structure=["REGION", "FUEL", "TIMESLICE", "YEAR", "VALUE"], 
                         id_column="FUEL", 
                         output_csv_name="SpecifiedDemandProfile.csv")
        # accumulated_demand        
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.accumulated_demand, 
                         id=commodity, 
                         column_structure=["REGION", "FUEL", "YEAR", "VALUE"], 
                         id_column="FUEL", 
                         output_csv_name="AccumulatedAnnualDemand.csv")
        # is_renewable
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.is_renewable, 
                         id=commodity, 
                         column_structure=["REGION", "FUEL", "YEAR", "VALUE"], 
                         id_column="FUEL", 
                         output_csv_name="RETagFuel.csv")
