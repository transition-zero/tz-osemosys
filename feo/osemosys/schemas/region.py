import os
from typing import ClassVar, List, Union

import pandas as pd
from pydantic import conlist, root_validator

from feo.osemosys.utils import group_to_json

from .base import OSeMOSYSBase, OSeMOSYSDataInt

##########
# REGION #
##########


class Region(OSeMOSYSBase):
    """
    Class to contain all information pertaining to regions and trade routes
    """

    neighbours: conlist(str, min_length=0) | None
    trade_route: OSeMOSYSDataInt | None

    otoole_stems: ClassVar[dict[str : dict[str : Union[str, list[str]]]]] = {
        "TradeRoute": {
            "attribute": "trade_route",
            "column_structure": ["REGION", "_REGION", "FUEL", "YEAR", "VALUE"],
        },
    }

    @root_validator(pre=True)
    def validation(cls, values):
        # TODO: add any relevant validation
        values.get("neighbours")
        values.get("trade_route")

        return values

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

        src_regions = pd.read_csv(os.path.join(root_dir, "REGION.csv"))
        routes = pd.read_csv(os.path.join(root_dir, "TradeRoute.csv"))

        try:
            dst_regions = pd.read_csv(os.path.join(root_dir, "_REGION.csv"))
        except FileNotFoundError:
            dst_regions = None

        #####################
        # Basic Data Checks #
        #####################

        # Assert regions in REGION.csv match those in _REGION.csv
        assert (
            routes["REGION"].isin(src_regions["VALUE"]).all()
        ), "REGION in trade_route missing from REGION.csv"
        if dst_regions is not None:
            assert src_regions.equals(dst_regions), "Source and destination regions not equal."
            assert (
                routes["_REGION"].isin(dst_regions["VALUE"]).all()
            ), "_REGION in trade_route missing from _REGION.csv"

        ##########################
        # Define class instances #
        ##########################

        region_instances = []
        for _index, region in src_regions.iterrows():
            region_instances.append(
                cls(
                    id=region["VALUE"],
                    neighbours=(
                        (routes.loc[routes["REGION"] == region["VALUE"], "_REGION"].values.tolist())
                        if dst_regions is not None
                        else None
                    ),
                    trade_route=(
                        OSeMOSYSDataInt(
                            data=group_to_json(
                                g=routes.loc[routes["REGION"] == region["VALUE"]],
                                data_columns=["REGION", "_REGION", "FUEL", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if region["VALUE"] in routes["REGION"].values
                        else None
                    ),
                    # TODO
                    long_name=None,
                    description=None,
                )
            )

        return region_instances
