import os
from typing import List

import pandas as pd
import xarray as xr
import yaml

from feo.osemosys.schemas.base import OSeMOSYSBase
from feo.osemosys.schemas.commodity import Commodity
from feo.osemosys.schemas.default_values import DefaultValues
from feo.osemosys.schemas.impact import Impact
from feo.osemosys.schemas.other_parameters import OtherParameters
from feo.osemosys.schemas.region import Region
from feo.osemosys.schemas.technology import Technology, TechnologyStorage
from feo.osemosys.schemas.time_definition import TimeDefinition
from feo.osemosys.utils import to_csv_helper


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
          xr.Dataset: An XArray dataset containing all data from the RunSpec
        """

        # Create dataframes for params and sets
        time_definition = to_csv_helper(self, TimeDefinition.otoole_stems, "time_definition")
        other_params = to_csv_helper(self, OtherParameters.otoole_stems, "other_parameters")
        region = to_csv_helper(self, Region.otoole_stems, "regions", root_column="REGION")
        commodities = to_csv_helper(self, Commodity.otoole_stems, "commodities", root_column="FUEL")
        impacts = to_csv_helper(self, Impact.otoole_stems, "impacts", root_column="EMISSION")
        technologies = to_csv_helper(
            self, Technology.otoole_stems, "technologies", root_column="TECHNOLOGY"
        )
        if self.storage_technologies:
            storage_technologies = to_csv_helper(
                self,
                TechnologyStorage.otoole_stems,
                "storage_technologies",
                root_column="STORAGE",
            )
            technologies = {**technologies, **storage_technologies}

        # Combine dataframes
        data_dfs = {
            **time_definition,
            **other_params,
            **region,
            **commodities,
            **impacts,
            **technologies,
        }

        # Set index to non-VALUE columns for parameters
        for df_name, df in data_dfs.items():
            if not df_name.isupper():
                index = list(df.columns)
                index.remove("VALUE")
                data_dfs[df_name] = df.set_index(index)
        # Convert params to data arrays
        data_arrays = {
            x: xr.DataArray.from_series(y["VALUE"]) for x, y in data_dfs.items() if not x.isupper()
        }
        # Create dataset
        ds = xr.Dataset(data_vars=data_arrays)

        # Replace any nan values with default values for corrsponding param
        default_values = self.default_values.values
        # Add default values as attribute of each data array
        for name, data in default_values.items():
            if name in list(ds.data_vars.keys()):
                ds[name].attrs["default"] = data["default"]
                ds[name] = ds[name].fillna(data["default"])

        return ds

    def to_otoole(self, comparison_directory):
        """
        Convert Runspec to otoole style output CSVs and config.yaml

        Parameters
        ----------
        comparison_directory: str
            Path to the output directory for CSV files to be placed
        """

        # Clear comparison directory
        for file in os.listdir(comparison_directory):
            os.remove(os.path.join(comparison_directory, file))

        # Write output CSVs

        # time_definition
        to_csv_helper(
            self,
            TimeDefinition.otoole_stems,
            "time_definition",
            comparison_directory,
            write_csv=True,
        )

        # other_parameters
        to_csv_helper(
            self,
            OtherParameters.otoole_stems,
            "other_parameters",
            comparison_directory,
            write_csv=True,
        )

        # regions
        to_csv_helper(
            self, Region.otoole_stems, "regions", comparison_directory, "REGION", write_csv=True
        )

        # commodities
        to_csv_helper(
            self,
            Commodity.otoole_stems,
            "commodities",
            comparison_directory,
            "FUEL",
            write_csv=True,
        )

        # impacts
        to_csv_helper(
            self, Impact.otoole_stems, "impacts", comparison_directory, "EMISSION", write_csv=True
        )

        # technologies
        to_csv_helper(
            self,
            Technology.otoole_stems,
            "technologies",
            comparison_directory,
            "TECHNOLOGY",
            write_csv=True,
        )

        # storage_technologies
        if not self.storage_technologies:  # If no storage technologies
            # Create empty output CSVs
            storage_csv_dict = TechnologyStorage.otoole_stems
            for file in list(storage_csv_dict):
                (
                    pd.DataFrame(columns=storage_csv_dict[file]["column_structure"]).to_csv(
                        os.path.join(comparison_directory, file + ".csv"), index=False
                    )
                )
                pd.DataFrame(columns=["VALUE"]).to_csv(
                    os.path.join(comparison_directory, "STORAGE.csv"), index=False
                )
        else:
            to_csv_helper(
                self,
                TechnologyStorage.otoole_stems,
                "storage_technologies",
                comparison_directory,
                "STORAGE",
                write_csv=True,
            )

        # write config yaml
        yaml_file_path = os.path.join(comparison_directory, "config.yaml")
        with open(yaml_file_path, "w") as yaml_file:
            yaml.dump(self.default_values.values, yaml_file, default_flow_style=False)

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
            other_parameters=OtherParameters.from_otoole_csv(root_dir=root_dir),
            default_values=DefaultValues.from_otoole_yaml(root_dir=root_dir),
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
