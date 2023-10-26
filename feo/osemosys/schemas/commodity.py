import os
import pandas as pd

from .base import *
from .utils import *

class Commodity(OSeMOSYSBase):
    # either demand (region:year:timeslice:value)
    # or annual_demand (region:year:value) must be specified;
    # demand_profile may be optionally specified with annual_demand
    demand_annual: RegionYearData | None
    demand_profile: RegionYearTimeData | None
    demand: RegionYearTimeData | None
    is_renewable: RegionYearData | None # why would this change over time??

    @classmethod
    def from_simplicity(cls, root_dir) -> List[cls]:

        # 
        df_fuel = pd.read_csv(os.path.join(root_dir, 'FUEL.csv'))
        df_annual_demand = pd.read_csv(os.path.join(root_dir, 'SpecifiedAnnualDemand.csv'))
        df_demand_profile = pd.read_csv(os.path.join(root_dir, 'SpecifiedDemandProfile.csv'))
        df_re_tag = pd.read_csv(os.path.join(root_dir, 'RETagFuel.csv'))

        assert (
            (df_demand_profile.groupby(['REGION','FUEL','YEAR'])['VALUE'].sum()==1.).all(), 
            "demand profiles must sum to one for all REGION, FUEL, and YEAR"
        )

        commodity_instances = []
        for commodity in df_fuel['VALUE'].values.tolist():
            commodity_instances.append(
                cls(
                    id=commodity,
                    demand_annual = RegionYearData(
                        data=group_to_json(
                            g=df_annual_demand.loc[df_annual_demand['FUEL']==commodity],
                            root_column='FUEL',
                            data_columns=['REGION','YEAR'],
                            target_column='VALUE',
                        )
                    ),
                    demand_profile = RegionYearTimeData(
                        data = group_to_json(
                            g=df_demand_profile.loc[df_demand_profile['FUEL']==commodity],
                            root_column='FUEL',
                            data_columns=['REGION','TIMESLICE','YEAR'],
                            target_column='VALUE'
                        )
                    )
                )
            )
        return commodity_instances





