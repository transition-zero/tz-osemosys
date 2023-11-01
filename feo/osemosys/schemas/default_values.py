import os

import pandas as pd
import yaml

from feo.osemosys.utils import *

from .base import *


class DefaultValues(OSeMOSYSBase):
    """
    Class to contain all default values
    """

    values: StringData

    @classmethod
    def from_otoole_yaml(cls, root_dir) -> "cls":
        """
        Instantiate a single DefaultValues object containing default values for all parameters.

        Parameters
        ----------
        root_dir: str
            Path to the root of the otoole csv directory

        Returns
        -------
        DefaultValues
            A single DefaultValues instance
        """

        # Find otoole config yaml file in root_dir
        yaml_files = [file for file in os.listdir(root_dir) if file.endswith(".yaml") or file.endswith(".yml")]
        if len(yaml_files) == 0:
            raise FileNotFoundError("No otoole config YAML file found in the directory")
        elif len(yaml_files) > 1:
            raise ValueError("Multiple otoole config YAML files found in the directory, only 1 required")
        yaml_file = yaml_files[0]

        # Read in otoole config yaml data
        with open(os.path.join(root_dir, yaml_file), 'r') as file:
            yaml_data = yaml.safe_load(file)

        # Create default value dictionary for all parameters
        default_values_dict = {}
        for key in yaml_data.keys():
            if "default" in yaml_data[key]:
                default_values_dict[key]=yaml_data[key]["default"]

        return cls(
            id="DefaultValues",
            # TODO
            long_name=None,
            description=None,
            values=StringData(data=default_values_dict),
            )

    