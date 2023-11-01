import os
from typing import Optional

import pandas as pd

from feo.osemosys.utils import *

from .base import *

# ##############
# ### REGION ###
# ##############


class Region(OSeMOSYSBase):
    neighbours: Optional[List[str]]
    TradeRoute: TradeRoute | None

    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["cls"]:
        """
        Instantiate a number of Region objects from otoole-organised csvs.

        Parameters
        ----------
        root_dir: str
            Path to the root of the otoole csv directory

        Returns
        -------
        List[Region]
            A list of Region instances that can be used downstream or dumped to json/yaml
        """

        src_regions = pd.read_csv(os.path.join(root_dir, "REGION.csv"))
        dst_regions = pd.read_csv(os.path.join(root_dir, "_REGION.csv"))
        routes = pd.read_csv(os.path.join(root_dir, "TradeRoute.csv"))

        assert src_regions.equals(dst_regions), "Source and destination regions not equal."
        assert (
            routes["REGION"].isin(src_regions["VALUE"]).all()
        ), "REGION in TradeRoutes missing from REGION.csv"
        assert (
            routes["_REGION"].isin(dst_regions["VALUE"]).all()
        ), "_REGION in TradeRoutes missing from _REGION.csv"

        region_instances = []
        for index, region in src_regions.iterrows():
            region_instances.append(
                cls(
                    id=region["VALUE"],
                    neighbours=routes.loc[
                        routes["REGION"] == region["VALUE"], "_REGION"
                    ].values.tolist(),
                    TradeRoute = (TradeRoute(data=group_to_json(
                        g=routes.loc[routes["REGION"] ==  region["VALUE"]],
                        data_columns=["REGION", "_REGION","FUEL", "YEAR"],
                        target_column="VALUE",
                    ))
                    if region["VALUE"] in routes["REGION"].values
                    else None),
                    # TODO
                    long_name=None,
                    description=None,
                )
            )

        return region_instances


    def to_otoole_csv(self, comparison_directory) -> "CSVs":

        # TradeRoute
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.TradeRoute, 
                         id=self.id, 
                         column_structure=["REGION", "_REGION","FUEL", "YEAR", "VALUE"], 
                         id_column="REGION", 
                         output_csv_name="TradeRoute.csv")