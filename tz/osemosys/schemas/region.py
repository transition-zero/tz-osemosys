from typing import List, Any

from pydantic import ConfigDict, Field, model_validator

from tz.osemosys.schemas.base import OSeMOSYSBase, OSeMOSYSData, cast_osemosysdata_value
from tz.osemosys.schemas.compat.region import OtooleRegion, OtooleRegionGroup

##########
# REGION #
##########


class Region(OSeMOSYSBase, OtooleRegion):
    """
    # Region

    The Region class contains data related to regions. One Region instance
    is given for each region.

    ## Parameters

    `id` `(str)`: Used to represent the region name.

    ## Examples

    A simple example of how a region ("R1") might be defined is given below, along with how it can
    be used to create an instance of the Region class:

    ```python
    from tz.osemosys.schemas.region import Region

    basic_region = dict(
        id="R1",
    )

    Region(**basic_region)
    ```
    """

    model_config = ConfigDict(extra="forbid")

    exclude_technologies: List[str] | None = Field(default=None)

    def compose(self, **sets):
        # compose root OSeMOSYSData
        for field, _info in self.model_fields.items():
            field_val = getattr(self, field)

            if field_val is not None:
                if isinstance(field_val, OSeMOSYSData):
                    setattr(
                        self,
                        field,
                        field_val.compose(self.id, field_val.data, **sets),
                    )

        return self


class RegionGroup(OSeMOSYSBase, OtooleRegionGroup):
    """
    # RegionGroup

    The Region Group class contains data related to region groups. One Region group instance
    is given for a user defined selection of regions. In this way, national climate policies/
    national renewable energy targets can be taken into account with sub-national 
    nodal representation. For example, a country-level NDC commitment can be implemented in a
    multi-node national model by grouping all nodes in a country and the decision as to the
    distribution of emissions across nodes will be determined endogenously.

    ## Parameters

    `id` `(str)`: Used to represent the region group name.

    ## Examples

    A simple example of how a region group ("RG1") might be defined is given below, along with
    how it can be used to create an instance of the Region group class:

    ```python
    from tz.osemosys.schemas.region import RegionGroup

    basic_region_group = dict(
        id="RG1",
    )

    `include_in_region_group` `(region{year:float})` - OSeMOSYS RegionGroupTagRegion.

    RegionGroup(**basic_region_group)
    ```
    """

    model_config = ConfigDict(extra="forbid")

    # region group boolean assigning nodes to a group (e.g. at a country level)
    include_in_region_group: OSeMOSYSData.RGRY.Bool | None = Field(None)

    #exclude_technologies: List[str] | None = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def cast_values(cls, values: Any) -> Any:
        for field, info in cls.model_fields.items():
            field_val = values.get(field)

            if field_val is not None:
                values[field] = cast_osemosysdata_value(field_val, info)

        return values    


    def compose(self, **sets):
        # compose root OSeMOSYSData
        for field, _info in self.model_fields.items():
            field_val = getattr(self, field)

            if field_val is not None:
                if isinstance(field_val, OSeMOSYSData):
                    setattr(
                        self,
                        field,
                        field_val.compose(self.id, field_val.data, **sets),
                    )

        return self