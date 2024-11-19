import os
from typing import TYPE_CHECKING, List

import pandas as pd
from pydantic import BaseModel

if TYPE_CHECKING:
    from tz.osemosys.schemas.region import Region, RegionGroup
    from tz.osemosys.schemas.base import OSeMOSYSData
    # from tz.osemosys.schemas.compat.base import OtooleCfg
    # from tz.osemosys.schemas.compat.base import OtooleCfg
    # from tz.osemosys.utils import flatten, group_to_json    

##########
# REGION #
##########


class OtooleRegion(BaseModel):
    """
    Class to contain methods for converting Region data to and from otoole style CSVs
    """

    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["Region"]:
        """Instantiate a number of Region objects from otoole-organised csvs.

        Args:
            root_dir (str): Path to the root of the otoole csv directory

        Returns:
            List[Region] (list): A list of Region instances,
            that can be used downstream or dumped to json/yaml
        """

        #############
        # Load Data #
        #############

        # Sets
        src_regions = pd.read_csv(os.path.join(root_dir, "REGION.csv"))
        try:
            dst_regions = pd.read_csv(os.path.join(root_dir, "_REGION.csv"))
        except FileNotFoundError:
            dst_regions = None

        #####################
        # Basic Data Checks #
        #####################

        # Assert regions in REGION.csv match those in _REGION.csv
        if dst_regions is not None:
            assert src_regions.equals(dst_regions), "Source and destination regions not equal."

        ##########################
        # Define class instances #
        ##########################

        region_instances = []
        for _index, region in src_regions.iterrows():
            region_instances.append(
                cls(
                    id=region["VALUE"],
                )
            )

        return region_instances
   

    @classmethod
    def to_dataframes(cls, regions: List["Region"]):
        # collect dataframes
        dfs = {}

        # SETS
        dfs["REGION"] = pd.DataFrame({"VALUE": [r.id for r in regions]})
        dfs["_REGION"] = pd.DataFrame({"VALUE": [r.id for r in regions]})

        return dfs

    @classmethod
    def to_otoole_csv(cls, regions: List["Region"], output_directory: str):
        """Write a number of Region objects to otoole-organised csvs.

        Args:
            regions (List[Region]): A list of Region instances
            output_directory (str): Path to the root of the otoole csv directory
        """

        dfs = cls.to_dataframes(regions)

        # Sets
        dfs["REGION"].to_csv(os.path.join(output_directory, "REGION.csv"), index=False)
        dfs["_REGION"].to_csv(os.path.join(output_directory, "_REGION.csv"), index=False)

        return True

class OtooleRegionGroup(BaseModel):
    """
    Class to contain methods for converting RegionGroup data to and from otoole style CSVs
    """
    # otoole_cfg: OtooleCfg | None = Field(None)
    # otoole_stems: ClassVar[dict[str : dict[str : Union[str, list[str]]]]] = {
    #     "RegionGroupTagRegion": {
    #         "attribute": "include_in_region_group",
    #         "columns": ["REGIONGROUP", "REGION", "YEAR", "VALUE"],
    #     },
    # }
    
    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["RegionGroup"]:

        region_group = pd.read_csv(os.path.join(root_dir, "REGIONGROUP.csv"))

        region_group_instances = []
        for _index, region_group in region_group.iterrows():
            region_group_instances.append(
                cls(
                    id=region_group["VALUE"]
                )
            )
        return region_group_instances 

    @classmethod
    def to_dataframes(cls, regionsgroup: List["RegionGroup"]):
        # collect dataframes
        dfs = {}

        # SETS
        dfs["REGIONGROUP"] = pd.DataFrame({"VALUE": [rg.id for rg in regionsgroup]})

        return dfs    

    @classmethod
    def to_otoole_csv(cls, regionsgroup: List["RegionGroup"], output_directory: str):
        """Write a number of Region objects to otoole-organised csvs.

        Args:
            regions (List[Region]): A list of Region instances
            output_directory (str): Path to the root of the otoole csv directory
        """

        dfs = cls.to_dataframes(regionsgroup)

        # Sets
        dfs["REGIONGROUP"].to_csv(os.path.join(output_directory, "REGIONGROUP.csv"), index=False)

        return True    