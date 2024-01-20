import os
from typing import List, Optional

import pandas as pd
import xarray as xr
import yaml

from feo.osemosys.defaults import DefaultsOtoole, defaults
from feo.osemosys.schemas.base import OSeMOSYSBase
from feo.osemosys.schemas.commodity import Commodity
from feo.osemosys.schemas.impact import Impact
from feo.osemosys.schemas.region import Region
from feo.osemosys.schemas.technology import Technology, TechnologyStorage
from feo.osemosys.schemas.time_definition import TimeDefinition
from feo.osemosys.utils import to_df_helper


class RunSpec(OSeMOSYSBase):
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
    defaults_otoole: Optional[DefaultsOtoole] = None

    def to_xr_ds(self):
        """
        Return the current RunSpec as an xarray dataset

        Args:
          self: this RunSpec instance

        Returns:
          xr.Dataset: An XArray dataset containing all data from the RunSpec
        """

        # Convert Runspec data to dfs
        data_dfs = to_df_helper(self)

        # Set index to columns other than "VALUE" (only for parameter dataframes)
        for df_name, df in data_dfs.items():
            if not df_name.isupper():
                data_dfs[df_name] = df.set_index(df.columns.difference(["VALUE"]).tolist())
        # Convert params to data arrays
        data_arrays = {x: y.to_xarray()["VALUE"] for x, y in data_dfs.items() if not x.isupper()}
        # Create dataset
        ds = xr.Dataset(data_vars=data_arrays)

        # If runspec not generated using otoole config yaml, use linopy defaults
        if self.defaults_otoole is None:
            default_values = defaults.otoole_name_defaults
        # Otherwise take defaults from otoole config yaml file
        else:
            default_values = {}
            for name, data in self.defaults_otoole.values.items():
                if data["type"] == "param":
                    default_values[name] = data["default"]

        # Replace any nan values in ds with default values (or None) for corresponding param,
        # adding default values as attribute of each data array
        for name in ds.data_vars.keys():
            # Replace nan values with default values if available
            if name in default_values.keys():
                ds[name].attrs["default"] = default_values[name]
                ds[name] = ds[name].fillna(default_values[name])
            # Replace all other nan values with None
            else:
                ds[name].attrs["default"] = None
                ds[name] = ds[name].fillna(None)

        return ds

    def to_otoole(self, output_directory):
        """
        Convert Runspec to otoole style output CSVs and config.yaml

        Parameters
        ----------
        output_directory: str
            Path to the output directory for CSV files to be placed
        """

        # Clear comparison directory
        for file in os.listdir(output_directory):
            os.remove(os.path.join(output_directory, file))

        # Convert Runspec data to dfs
        output_dfs = to_df_helper(self)

        # Write output CSVs
        for file in list(output_dfs):
            output_dfs[file].to_csv(os.path.join(output_directory, file + ".csv"), index=False)

        # Write empty storage CSVs if no storage technologies present
        if not self.storage_technologies:
            storage_csv_dict = TechnologyStorage.otoole_stems
            for file in list(storage_csv_dict):
                (
                    pd.DataFrame(columns=storage_csv_dict[file]["column_structure"]).to_csv(
                        os.path.join(output_directory, file + ".csv"), index=False
                    )
                )
                pd.DataFrame(columns=["VALUE"]).to_csv(
                    os.path.join(output_directory, "STORAGE.csv"), index=False
                )

        # write config yaml if used to generate Runspec
        if self.defaults_otoole:
            yaml_file_path = os.path.join(output_directory, "config.yaml")
            with open(yaml_file_path, "w") as yaml_file:
                yaml.dump(self.defaults_otoole.values, yaml_file, default_flow_style=False)

    @classmethod
    def from_otoole(cls, root_dir):
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
            defaults_otoole=DefaultsOtoole.from_otoole_yaml(root_dir=root_dir),
        )

    def to_osemosys_data_file(self, root_dir):
        """
        Convert Runspec to osemosys ready text file (uses otoole)

        Parameters
        ----------
        root_dir: str
            Path to the directory containing data CSVs and yaml config file

        #TODO: acceptable to use otoole here or should otoole only be for post processing?
        """
