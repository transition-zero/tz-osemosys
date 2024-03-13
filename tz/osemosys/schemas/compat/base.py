import os
from typing import Dict, List, Union

import pandas as pd
import yaml
from pydantic import BaseModel, Field

from tz.osemosys.schemas.base import OSeMOSYSBase


class OtooleCfg(BaseModel):
    """
    Paramters needed to round-trip csvs from otoole
    """

    empty_dfs: List[str] | None
    non_default_idx: Dict[str, pd.Index] | None = Field(None)

    class Config:
        arbitrary_types_allowed = True


class DefaultsOtoole(OSeMOSYSBase):
    """
    Class to contain all data from from otoole config yaml, including default values
    """

    values: Dict[str, Dict[str, Union[str, int, float, List]]]

    @classmethod
    def from_otoole_yaml(cls, root_dir):
        """Instantiate a single DefaultsOtoole dict from config.yaml file

        Contains information for each parameter on:
        indices - column names
        type - param
        dtype - data type
        default - default values
        (short_name - optional shortened parameter name)

        And information for each set on:
        dtype - data type
        type - set

        Args:
            root_dir (str): Path to the root of the otoole csv directory

        Returns:
            DefaultsOtoole: A single DefaultsOtoole instance
        """

        # ###########
        # Load Data #
        # ###########

        # Find otoole config yaml file in root_dir
        yaml_files = [
            file for file in os.listdir(root_dir) if file.endswith(".yaml") or file.endswith(".yml")
        ]
        if len(yaml_files) == 0:
            return None
        elif len(yaml_files) > 1:
            raise ValueError(">1 otoole config YAML files found in the directory, only 1 required")
        yaml_file = yaml_files[0]

        # Read in otoole config yaml data
        with open(os.path.join(root_dir, yaml_file)) as file:
            yaml_data = yaml.safe_load(file)

        # #######################
        # Define class instance #
        # #######################

        return cls(
            id="DefaultValues",
            # TODO
            long_name=None,
            description=None,
            values=yaml_data,
        )
