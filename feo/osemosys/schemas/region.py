import pandas as pd

from .base import *



# ##############
# ### REGION ###
# ##############

class Region(OSeMOSYSBase):
    neighbours: List[str]

    @classmethod
    def from_simplicity(cls, root_dir) -> List[cls]:
        """
        Instantiate a number of Region objects from otoole-organised csvs.

        Parameters
        ----------
        root_dir: str
            Path to the root of the simplicity directory

        Returns
        -------
        List[Region]
            A list of Region instances that can be used downstream or dumped to json/yaml
        """

        src_regions = pd.read_csv(os.path.join(root_dir, 'REGION.csv'))
        dst_regions = pd.read_csv(os.path.join(root_dir, '_REGION.csv'))
        routes = pd.read_csv(os.path.join(root_dir, 'TradeRoute.csv'))

        assert pd.testing.assert_frame_equal(src_regions,dst_regions), "Source and destination regions not equal."
        assert routes['REGION'].isin(src_regions['VALUE']).all(), "REGION in TradeRoutes missing from REGION.csv"
        assert routes['_REGION'].isin(dst_regions['VALUE']).all(), "_REGION in TradeRoutes missing from _REGION.csv"

        region_instances = []
        for region in src_regions.iterrows():
            region_instances.append(
                cls(
                    id=region['VALUE'],
                    neighbours = routes.loc[routes['REGION']==region,'_REGION'].values.tolist()
                )
            )

        return region_instances

