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

        self.time_definition.to_otoole_csv(comparison_directory)
        self.other_parameters.to_otoole_csv(comparison_directory)

        region_list = []
        region_csv_dict = self.regions[0].otoole_stems
        output_dfs = {}
        # Create output dfs, adding to dict with filename as key
        for file in list(region_csv_dict):
            output_dfs[file] = pd.DataFrame(columns = region_csv_dict[file]["column_structure"])
        # Add data to output dfs iteratively
        for region in self.regions:
            region_list.append(region.id)
            output_dfs = region.to_otoole_csv(comparison_directory, output_dfs)
        # Write output csv files
        for file in list(output_dfs):
            output_dfs[file].to_csv(os.path.join(comparison_directory, file+".csv"), index=False)
        pd.DataFrame(region_list, columns = ["VALUE"]).to_csv(os.path.join(comparison_directory, "REGION.csv"), index=False)
        pd.DataFrame(region_list, columns = ["VALUE"]).to_csv(os.path.join(comparison_directory, "_REGION.csv"), index=False)
        
        commodity_list = []
        commodity_csv_dict = self.commodities[0].otoole_stems
        output_dfs = {}
        # Create output dfs, adding to dict with filename as key
        for file in list(commodity_csv_dict):
            output_dfs[file] = pd.DataFrame(columns = commodity_csv_dict[file]["column_structure"])
        # Add data to output dfs iteratively
        for commodity in self.commodities:
            commodity_list.append(commodity.id)
            output_dfs = commodity.to_otoole_csv(comparison_directory, output_dfs)
        # Write output csv files
        for file in list(output_dfs):
            output_dfs[file].to_csv(os.path.join(comparison_directory, file+".csv"), index=False)
        pd.DataFrame(commodity_list, columns = ["VALUE"]).to_csv(os.path.join(comparison_directory, "FUEL.csv"), index=False)
        
        impact_list = []
        impact_csv_dict = self.impacts[0].otoole_stems
        output_dfs = {}
        # Create output dfs, adding to dict with filename as key
        for file in list(impact_csv_dict):
            output_dfs[file] = pd.DataFrame(columns = impact_csv_dict[file]["column_structure"])
        # Add data to output dfs iteratively
        for impact in self.impacts:
            impact_list.append(impact.id)
            output_dfs = impact.to_otoole_csv(comparison_directory, output_dfs)
        # Write output csv files
        for file in list(output_dfs):
            output_dfs[file].to_csv(os.path.join(comparison_directory, file+".csv"), index=False)
        pd.DataFrame(impact_list, columns = ["VALUE"]).to_csv(os.path.join(comparison_directory, "EMISSION.csv"), index=False)

        technology_list = []
        for technology in self.technologies:
            technology_list.append(technology.id)
            technology.to_otoole_csv(comparison_directory)
        pd.DataFrame(technology_list, columns = ["VALUE"]).to_csv(os.path.join(comparison_directory, "TECHNOLOGY.csv"), index=False)

        # If no storage technologies
        if not self.storage_technologies:
            TechnologyStorage.to_empty_csv(comparison_directory=comparison_directory)
        else:
            storage_list = []
            for storage_technology in self.storage_technologies:
                storage_list.append(storage_technology.id)
                storage_technology.to_otoole_csv(comparison_directory)
            pd.DataFrame(storage_list, columns = ["VALUE"]).to_csv(os.path.join(comparison_directory, "STORAGE.csv"), index=False)
            


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
