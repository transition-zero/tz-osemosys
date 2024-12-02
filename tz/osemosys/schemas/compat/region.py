import os
from pathlib import Path
from typing import TYPE_CHECKING, List, ClassVar, Dict, Union

import pandas as pd
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from tz.osemosys.defaults import defaults
    from tz.osemosys.schemas.region import Region, RegionGroup
    from tz.osemosys.schemas.base import OSeMOSYSData
    from tz.osemosys.schemas.compat.base import OtooleCfg
    from tz.osemosys.utils import flatten, group_to_json    

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
    #otoole_cfg = OtooleCfg(empty_dfs=[])
    otoole_stems: ClassVar[dict[str : dict[str : Union[str, list[str]]]]] = {
         "RegionGroupTagRegion": {
             "attribute": "include_in_region_group",
             "columns": ["REGIONGROUP", "REGION", "YEAR", "VALUE"],
         },
    }
    
    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["RegionGroup"]:

        df_regionsgroup = pd.read_csv(os.path.join(root_dir, "REGIONGROUP.csv"))

        dfs = {}

        otoole_cfg = OtooleCfg(empty_dfs=[])
        for key, params in list(cls.otoole_stems.items()):
            try:
                dfs[key] = pd.read_csv(Path(root_dir) / f"{key}.csv")
                if dfs[key].empty:
                    otoole_cfg.empty_dfs.append(key)
                else:
                    otoole_cfg.non_default_idx[key] = (
                        dfs[key].set_index([c for c in params["columns"] if c != "VALUE"]).index
                    )
            except FileNotFoundError:
                otoole_cfg.empty_dfs.append(key)
        
        #####################
        # Basic Data Checks #
        #####################

        # Check no duplicates in TECHNOLOGY.csv
        if len(df_regionsgroup) != len(df_regionsgroup["VALUE"].unique()):
            raise ValueError("REGIONGROUP.csv must not contain duplicate values")

        # Check technology names are consistent with those in TECHNOLOGY.csv
        for df in dfs.keys():
            for region_group in dfs[df]["REGIONGROUP"].unique():
                if region_group not in list(df_regionsgroup["VALUE"]):
                    raise ValueError(f"{region_group} given in {df}.csv but not in REGIONGROUP.csv")
                

        region_group_instances = []

        include_in_region_group = (
            OSeMOSYSData.RGRY.Bool(
                group_to_json(
                    g=dfs["RegionGroupTagRegion"].loc[dfs["RegionGroupTagRegion"]["REGION"] == region_group],
                    root_column="REGION",
                    data_columns=["REGIONGROUP", "YEAR"],
                    target_column="VALUE",
                    )
                )
                if region_group in dfs["RegionGroupTagRegion"]["REGION"].values
                else OSeMOSYSData.RGRY(defaults.include_in_region_group)
            )

        for region_group in df_regionsgroup["VALUE"].values.tolist():
            region_group_instances.append(
                cls(
                    id=region_group["VALUE"],
                    otoole_cfg=otoole_cfg,
                    include_in_region_group=include_in_region_group,
                ),
            )

        return region_group_instances 

    @classmethod
    def to_dataframes(cls, regionsgroup: List["RegionGroup"]) -> Dict[str, pd.DataFrame]:
        # collect dataframes
        dfs = {}
        
        # SETS
        dfs["REGIONGROUP"] = pd.DataFrame({"VALUE": [rg.id for rg in regionsgroup]})

        include_in_region_group_dfs = []

        for region_group in regionsgroup:

            if region_group.include_in_region_group is not None:
                df = pd.json_normalize(region_group.include_in_region_group.data).T.rename(
                    columns={0: "VALUE"}
                )
                #df["REGIONGROUP"] = region_group.id
                df[["REGIONGROUP", "REGION", "YEAR"]] = pd.DataFrame(
                    df.index.str.split(".").to_list(), index=df.index.unique()              
                )
                df["VALUE"] = df["VALUE"].map({True: 1, False: 0})
                include_in_region_group_dfs.append(df)  

        dfs["RegionGroupTagRegion"] = (
            pd.concat(include_in_region_group_dfs)
            if include_in_region_group_dfs
            else pd.DataFrame(columns=cls.otoole_stems["RegionGroupTagRegion"]["columns"])
        )

        return dfs    

    @classmethod
    def to_otoole_csv(cls, regionsgroup: List["RegionGroup"], output_directory: str):
        """Write a number of Region objects to otoole-organised csvs.

        Args:
            regions (List[Region]): A list of Region instances
            output_directory (str): Path to the root of the otoole csv directory
        """

        dfs = cls.to_dataframes(regionsgroup=regionsgroup)

        # Sets
        dfs["REGIONGROUP"].to_csv(os.path.join(output_directory, "REGIONGROUP.csv"), index=False)

        for stem, _params in cls.otoole_stems.items():
            if any([(stem not in region_group.otoole_cfg.empty_dfs) for region_group in regionsgroup]):
                dfs[stem].to_csv(os.path.join(output_directory, f"{stem}.csv"), index=False)

        return True    