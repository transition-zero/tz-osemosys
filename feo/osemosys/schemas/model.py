import os
import pandas as pd


from .base import *
from .utils import *


class RunSpec(OSeMOSYSBase):

    # financials
    depreciation_method: RegionData # 1= "straight-line" # or "sinking-fund"
    discount_rate: RegionTechnologyYearData | None # may want to express this at the technology or model level

    # time definition
    time_definition: TimeDefinition

    # nodes
    regions: List[Region]

    # commodities
    commodities: List[Commodity]

    # impact constraints (e.g. CO2)
    impacts: List[Impact]

    # technologies
    production_technologies: List[TechnologyProduction]
    storage_technologies: List[TechnologyStorage]
    transmission_technologies: List[TechnologyTransmission]

    # reserve margins if any
    reserve_margins_commodity: List[List[str,RegionYearData]] | None
    reserve_margins_technology: List[List[str, RegionalYearData]] | None

    # renewable targets
    renewable_targets: RegionYearData | None
    

    def to_simplicity(self, root_dir) -> Dict[str,str]:
        """
        Dump regions to 

        Parameters
        ----------
        root_dir: str
            Path to the root of the simplicity directory

        Returns
        -------
        Dict[str,str]
            A dictionary with keys the otool filenames and paths the otool paths
        """
        self.commodities.to_simplicity(root_dir)
        
        pass

    @classmethod
    def from_simplicity(cls, root_dir) -> cls:

        def get_depreciation_method(root_dir):
            df = pd.read_csv(os.path.join(root_dir, 'DepreciationMethod.csv'))
            

        def get_discount_rate(root_dir):

        def get_reserve_margins_commodity(root_dir):

        def get_reserve_margins_technology(root_dir):

        def get_renewable_targets(root_dir):


        # depreciation method
        depreciation_method = get_depreciation_method(root_dir)
        discount_rate = get_discount_rate(root_dir)
        reserve_margins_commodity = get_reserve_margins_commodity(root_dir)
        reserve_margins_technology = get_reserve_margins_technology(root_dir)
        renewable_targets = get_renewable_targets(root_dir)


        return cls(
            depreciation_method = depreciation_method,
            discount_rate=discount_rate,
            regions=Region.from_simplicity(root_dir=root_dir),
            production_technologies=TechnologyProduction.from_simplicity(root_dir=root_dir),
            storage_technologies=TechnologyStorage.from_simplicity(root_dir=root_dir),
            transmission_technologies=TechnologyTransmission.from_simplicity(root_dir=root_dir),
            reserve_margins_commodity=reserve_margins_commodity,
            reserve_margins_technology=reserve_margins_technology,
            renewable_targets=renewable_targets
        )