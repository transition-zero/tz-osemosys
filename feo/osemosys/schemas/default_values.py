import os

import yaml

from .base import OSeMOSYSBase, OSeMOSYSData


class DefaultValues(OSeMOSYSBase):
    """
    Class to contain all default values
    """

    values: OSeMOSYSData

    @classmethod
    def from_otoole_yaml(cls, root_dir) -> "DefaultValues":
        """Instantiate a single DefaultValues object from config.yaml file

        Args:
            root_dir (str): Path to the root of the otoole csv directory

        Returns:
            DefaultValues: A single DefaultValues instance
        """

        # ###########
        # Load Data #
        # ###########

        # Find otoole config yaml file in root_dir
        yaml_files = [
            file for file in os.listdir(root_dir) if file.endswith(".yaml") or file.endswith(".yml")
        ]
        if len(yaml_files) == 0:
            raise FileNotFoundError("No otoole config YAML file found in the directory")
        elif len(yaml_files) > 1:
            raise ValueError(">1 otoole config YAML files found in the directory, only 1 required")
        yaml_file = yaml_files[0]

        # Read in otoole config yaml data
        with open(os.path.join(root_dir, yaml_file)) as file:
            yaml_data = yaml.safe_load(file)

        # Create default value dictionary for all parameters
        default_values_dict = {}
        for key in yaml_data.keys():
            if "default" in yaml_data[key]:
                default_values_dict[key] = yaml_data[key]["default"]

        # #######################
        # Define class instance #
        # #######################

        return cls(
            id="DefaultValues",
            # TODO
            long_name=None,
            description=None,
            values=OSeMOSYSData(data=default_values_dict),
        )
