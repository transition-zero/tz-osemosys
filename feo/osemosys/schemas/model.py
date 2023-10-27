import os

import pandas as pd

from feo.osemosys.schemas.base import *
from feo.osemosys.schemas.commodity import Commodity
from feo.osemosys.schemas.impact import Impact
from feo.osemosys.schemas.region import Region
from feo.osemosys.schemas.technology import Technology, TechnologyStorage
from feo.osemosys.schemas.time_definition import TimeDefinition
from feo.osemosys.utils import *


class RunSpec(OSeMOSYSBase):
    # financials
    depreciation_method: RegionData | None  # 1= "straight-line" # or "sinking-fund"
    discount_rate: RegionData | None  # may want to express this at the technology or model level

    # time definition
    time_definition: TimeDefinition

    # nodes
    regions: List[Region]

    # commodities
    commodities: List[Commodity]

    # impact constraints (e.g. CO2)
    impacts: List[Impact]

    # technologies
    technologies: List[Technology]
    storage_technologies: List[TechnologyStorage]
    # TODO
    # production_technologies: List[TechnologyProduction]
    # transmission_technologies: List[TechnologyTransmission]

    # reserve margins if any
    reserve_margins_level: RegionYearData | None
    reserve_margins_commodity: RegionCommodityYearData | None
    reserve_margins_technology: RegionTechnologyYearData | None

    # renewable targets
    renewable_targets: RegionYearData | None

    # Default values
    # TODO

    def to_xr_ds(self):
        """
        Return the current RunSpec as an xarray dataset

        Args:
          self: this RunSpec

        Returns:
          xr.Dataset: An XArray dataset
        """

        coords = {}

    def to_otoole_csv(self, comparison_directory) -> Dict[str, str]:
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

        self.time_definition.to_otoole_csv(comparison_directory)

        for commodity in self.commodities:
            commodity.to_otoole_csv(comparison_directory)
            
        for impact in self.impacts:
            impact.to_otoole_csv(comparison_directory)

        for technology in self.technologies:
            technology.to_otoole_csv(comparison_directory)

        for storage_technology in self.storage_technologies:
            storage_technology.to_otoole_csv(comparison_directory)


    @classmethod
    def from_otoole_csv(cls, root_dir, comparison_directory) -> "cls":
        
        # Clear comparison directory
        for file in os.listdir(comparison_directory):
            os.remove(os.path.join(comparison_directory, file))
        
        def get_depreciation_method(root_dir):
            df = pd.read_csv(os.path.join(root_dir, "DepreciationMethod.csv"))
            return df if not df.empty else None

        def get_discount_rate(root_dir):
            df = pd.read_csv(os.path.join(root_dir, "DiscountRate.csv"))
            return df if not df.empty else None

        def get_reserve_margins_level(root_dir):
            df = pd.read_csv(os.path.join(root_dir, "ReserveMargin.csv"))
            return df if not df.empty else None

        def get_reserve_margins_commodity(root_dir):
            df = pd.read_csv(os.path.join(root_dir, "ReserveMarginTagFuel.csv"))
            return df if not df.empty else None

        def get_reserve_margins_technology(root_dir):
            df = pd.read_csv(os.path.join(root_dir, "ReserveMarginTagTechnology.csv"))
            return df if not df.empty else None

        def get_renewable_targets(root_dir):
            df = pd.read_csv(os.path.join(root_dir, "REMinProductionTarget.csv"))
            return df if not df.empty else None

        depreciation_method = get_depreciation_method(root_dir)
        discount_rate = get_discount_rate(root_dir)
        reserve_margins_level = get_reserve_margins_level(root_dir)
        reserve_margins_commodity = get_reserve_margins_commodity(root_dir)
        reserve_margins_technology = get_reserve_margins_technology(root_dir)
        renewable_targets = get_renewable_targets(root_dir)

        return cls(
            id="id",
            long_name=None,
            description=None,
            depreciation_method=depreciation_method,
            discount_rate=discount_rate,
            impacts=Impact.from_otoole_csv(root_dir=root_dir),
            regions=Region.from_otoole_csv(root_dir=root_dir),
            technologies=Technology.from_otoole_csv(root_dir=root_dir),
            storage_technologies=TechnologyStorage.from_otoole_csv(root_dir=root_dir, comparison_directory=comparison_directory),
            # TODO
            # production_technologies=TechnologyProduction.from_otoole_csv(root_dir=root_dir),
            # transmission_technologies=TechnologyTransmission.from_otoole_csv(root_dir=root_dir),
            commodities=Commodity.from_otoole_csv(root_dir=root_dir),
            time_definition=TimeDefinition.from_otoole_csv(root_dir=root_dir),
            reserve_margins_level=reserve_margins_level,
            reserve_margins_commodity=reserve_margins_commodity,
            reserve_margins_technology=reserve_margins_technology,
            renewable_targets=renewable_targets,
        )
