import os
from typing import Dict, List, Union

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings

from feo.osemosys.schemas.base import OSeMOSYSBase, OSeMOSYSData


class DefaultsLinopy(BaseSettings):
    """
    Class to contain hard coded default values, for use with xarray/Linopy
    """

    availability_factor: OSeMOSYSData = Field(default=OSeMOSYSData(data=1))
    capacity_factor: OSeMOSYSData = Field(default=OSeMOSYSData(data=1))
    capacity_activity_unit_ratio: OSeMOSYSData = Field(default=OSeMOSYSData(data=1))
    timeslice_in_timebracket: OSeMOSYSData = Field(default=OSeMOSYSData(data=0))
    timeslice_in_daytype: OSeMOSYSData = Field(default=OSeMOSYSData(data=0))
    timeslice_in_season: OSeMOSYSData = Field(default=OSeMOSYSData(data=0))
    depreciation_method: OSeMOSYSData = Field(default=OSeMOSYSData(data="straight-line"))
    discount_rate: OSeMOSYSData = Field(default=OSeMOSYSData(data=0.1))
    input_activity_ratio: OSeMOSYSData = Field(default=OSeMOSYSData(data=0))
    output_activity_ratio: OSeMOSYSData = Field(default=OSeMOSYSData(data=0))
    residual_capacity: OSeMOSYSData = Field(default=OSeMOSYSData(data=0))
    demand_annual: OSeMOSYSData = Field(default=OSeMOSYSData(data=0))
    demand_profile: OSeMOSYSData = Field(default=OSeMOSYSData(data=0))

    otoole_name_defaults: Dict = Field(
        default={
            "AvailabilityFactor": OSeMOSYSData(data=1),
            "CapacityFactor": OSeMOSYSData(data=1),
            "CapacityToActivityUnit": OSeMOSYSData(data=1),
            "Conversionld": OSeMOSYSData(data=0),
            "Conversionlh": OSeMOSYSData(data=0),
            "Conversionls": OSeMOSYSData(data=0),
            "DepreciationMethod": OSeMOSYSData(data="straight-line"),
            "DiscountRate": OSeMOSYSData(data=0.1),
            "InputActivityRatio": OSeMOSYSData(data=0),
            "OutputActivityRatio": OSeMOSYSData(data=0),
            "ResidualCapacity": OSeMOSYSData(data=0),
            "SpecifiedAnnualDemand": OSeMOSYSData(data=0),
            "SpecifiedDemandProfile": OSeMOSYSData(data=0),
        }
    )


defaults = DefaultsLinopy()


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
