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
        # Create output dataframe if not already existing
        if not os.path.isfile(os.path.join(comparison_directory, "SpecifiedAnnualDemand.csv")):
            pd.DataFrame(columns=["REGION", "FUEL", "YEAR", "VALUE"]).to_csv(
                os.path.join(comparison_directory, "SpecifiedAnnualDemand.csv"), index=False
            )
        if self.demand_annual is not None:
            # Read existing dataframe
            df_demand_annual = pd.read_csv(
                os.path.join(comparison_directory, "SpecifiedAnnualDemand.csv")
            )
            # Convert JSON data object to df
            df_demand_annual_to_add = json_dict_to_dataframe(self.demand_annual.data)
            df_demand_annual_to_add.columns = ["REGION", "YEAR", "VALUE"]
            df_demand_annual_to_add["FUEL"] = commodity
            df_demand_annual_to_add = df_demand_annual_to_add[["REGION", "FUEL", "YEAR", "VALUE"]]
            # Add to dataframe
            df_demand_annual = pd.concat([df_demand_annual, df_demand_annual_to_add])
            # Write dataframe
            df_demand_annual.to_csv(
                os.path.join(comparison_directory, "SpecifiedAnnualDemand.csv"), index=False
            )

        # demand_profile
        # Create output dataframe if not already existing
        if not os.path.isfile(os.path.join(comparison_directory, "SpecifiedDemandProfile.csv")):
            pd.DataFrame(columns=["REGION", "FUEL", "TIMESLICE", "YEAR", "VALUE"]).to_csv(
                os.path.join(comparison_directory, "SpecifiedDemandProfile.csv"), index=False
            )
        if self.demand_profile is not None:
            # Read existing dataframe
            df_demand_profile = pd.read_csv(
                os.path.join(comparison_directory, "SpecifiedDemandProfile.csv")
            )
            # Convert JSON data object to df
            df_demand_profile_to_add = json_dict_to_dataframe(self.demand_profile.data)
            df_demand_profile_to_add.columns = ["REGION", "TIMESLICE", "YEAR", "VALUE"]
            df_demand_profile_to_add["FUEL"] = commodity
            df_demand_profile_to_add = df_demand_profile_to_add[
                ["REGION", "FUEL", "TIMESLICE", "YEAR", "VALUE"]
            ]
            # Add to dataframe
            df_demand_profile = pd.concat([df_demand_profile, df_demand_profile_to_add])
            # Write dataframe
            df_demand_profile.to_csv(
                os.path.join(comparison_directory, "SpecifiedDemandProfile.csv"), index=False
            )

        # accumulated_demand
        # Create output dataframe if not already existing
        if not os.path.isfile(os.path.join(comparison_directory, "AccumulatedAnnualDemand.csv")):
            pd.DataFrame(columns=["REGION", "FUEL", "YEAR", "VALUE"]).to_csv(
                os.path.join(comparison_directory, "AccumulatedAnnualDemand.csv"), index=False
            )
        if self.accumulated_demand is not None:
            # Read existing dataframe
            df_accumulated_demand = pd.read_csv(
                os.path.join(comparison_directory, "AccumulatedAnnualDemand.csv")
            )
            # Convert JSON data object to df
            df_accumulated_demand_to_add = json_dict_to_dataframe(self.accumulated_demand.data)
            df_accumulated_demand_to_add.columns = ["REGION", "TIMESLICE", "YEAR", "VALUE"]
            df_accumulated_demand_to_add["FUEL"] = commodity
            df_accumulated_demand_to_add = df_accumulated_demand_to_add[
                ["REGION", "FUEL", "TIMESLICE", "YEAR", "VALUE"]
            ]
            # Add to dataframe
            df_accumulated_demand = pd.concat([df_accumulated_demand, df_accumulated_demand_to_add])
            # Write dataframe
            df_accumulated_demand.to_csv(
                os.path.join(comparison_directory, "AccumulatedAnnualDemand.csv"), index=False
            )

        # is_renewable
        # TODO
