import os

import pandas as pd

from feo.osemosys.schemas.base import *
from feo.osemosys.schemas.commodity import Commodity
from feo.osemosys.schemas.impact import Impact
from feo.osemosys.schemas.region import Region
from feo.osemosys.schemas.technology import Technology, TechnologyStorage
from feo.osemosys.schemas.time_definition import TimeDefinition
from feo.osemosys.schemas.other_parameters import OtherParameters
from feo.osemosys.schemas.default_values import DefaultValues
from feo.osemosys.utils import *


class RunSpec(OSeMOSYSBase):

    # Other parameters
    other_parameters: OtherParameters
    
    # time definition
    time_definition: TimeDefinition

    # nodes
    regions: List[Region]

    # commodities
    commodities: List[Commodity]

    # Impact constraints (e.g. CO2)
    impacts: List[Impact]

    # technologies
    technologies: List[Technology]
    storage_technologies: List[TechnologyStorage]
    # TODO
    # production_technologies: List[TechnologyProduction]
    # transmission_technologies: List[TechnologyTransmission]

    # Default values
    default_values: DefaultValues


    def to_xr_ds(self):
        """
        Return the current RunSpec as an xarray dataset

        Args:
          self: this RunSpec

        Returns:
          xr.Dataset: An XArray dataset
        """

        coords = {
            "REGION": [region.id for region in self.regions],
            "_REGION": [region.id for region in self.regions],
            "TIMESLICE": [timeslice for timeslice in self.time_definition.timeslice],
            "DAYTYPE": [daytype for daytype in self.time_definition.day_type],
            "DAILYTIMEBRACKET": [
                timebracket for timebracket in self.time_definition.daily_time_bracket
            ],
            "SEASON": [season for season in self.time_definition.season],
            "YEAR": [year for year in self.time_definition.years],
            "STORAGE": [],
            "MODE_OF_OPERATION": [],
            "EMISSION": [],
            "COMMODITY": [],
            "TECHNOLOGY": [],
        }

        print("coords")
        print(coords)

    def to_otoole_csv(self, comparison_directory):
        """
        Convert Runspec to otoole style output CSVs

        Parameters
        ----------
        comparison_directory: str
            Path to the output directory for CSV files to be placed
        """

        ### Clear comparison directory
        for file in os.listdir(comparison_directory):
            os.remove(os.path.join(comparison_directory, file))

        ### Write output CSVs

        # time_definition
        to_csv_helper(self, TimeDefinition.otoole_stems, "time_definition", comparison_directory)
        
        self.other_parameters.to_otoole_csv(comparison_directory)

        # regions
        to_csv_helper(self, Region.otoole_stems, "regions", comparison_directory, "REGION")
        
        # commodities
        to_csv_helper(self, Commodity.otoole_stems, "commodities", comparison_directory, "FUEL")
        
        # impacts
        to_csv_helper(self, Impact.otoole_stems, "impacts", comparison_directory, "EMISSION")

        # technologies
        to_csv_helper(self, Technology.otoole_stems, "technologies", comparison_directory, "TECHNOLOGY")

        # storage_technologies
        if not self.storage_technologies: # If no storage technologies
            # Create empty output CSVs
            storage_csv_dict = TechnologyStorage.otoole_stems
            for file in list(storage_csv_dict):
                (pd.DataFrame(columns = storage_csv_dict[file]["column_structure"])
                 .to_csv(os.path.join(comparison_directory, file+".csv"), index=False))
                pd.DataFrame(columns=["VALUE"]).to_csv(os.path.join(comparison_directory, "STORAGE.csv"), index=False)
        else:
            to_csv_helper(self, TechnologyStorage.otoole_stems, "storage_technologies", comparison_directory, "STORAGE")
            


    @classmethod
    def from_otoole(cls, root_dir) -> "cls":

        return cls(
            id="id",
            long_name=None,
            description=None,
            impacts=Impact.from_otoole_csv(root_dir=root_dir),
            regions=Region.from_otoole_csv(root_dir=root_dir),
            technologies=Technology.from_otoole_csv(root_dir=root_dir),
            storage_technologies=TechnologyStorage.from_otoole_csv(root_dir=root_dir),
            # TODO
            # production_technologies=TechnologyProduction.from_otoole_csv(root_dir=root_dir),
            # transmission_technologies=TechnologyTransmission.from_otoole_csv(root_dir=root_dir),
            commodities=Commodity.from_otoole_csv(root_dir=root_dir),
            time_definition=TimeDefinition.from_otoole_csv(root_dir=root_dir),
            other_parameters=OtherParameters.from_otoole_csv(root_dir=root_dir),
            default_values=DefaultValues.from_otoole_yaml(root_dir=root_dir),
        )
