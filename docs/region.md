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

# RegionGroup

The Region Group class contains data related to region groups. One Region group instance
is given for a user defined selection of regions. This class is used to implement emissions targets
and renewable energy targets for a given selection of regions. Region Group Emissions targets per
region group are specified on the relevant impact (emission) class. Renewable energy targets per
Region Group are specified on the Model class, alongside whole model renewable energy targets.

In this way, national climate policies/
national renewable energy targets can be taken into account with sub-national
nodal representation. For example, a country-level NDC commitment can be implemented in a
multi-node national model by grouping all nodes in a country and the decision as to the
distribution of emissions across nodes will be determined endogenously.

## Parameters

`id` `(str)`: Used to represent the region group name.

`include_in_region_group` `(region{year:float})` - OSeMOSYS style name RegionGroupTagRegion.
Tag regions into a group for RE target and emissions constriants.
Optional, defaults to `None`.

## Examples

A simple example of how a region group ("RG1") with all regions assigned to it might be defined as
is given below, along with how it can be used to create an instance of the RegionGroup class:

```python
from tz.osemosys.schemas.region import RegionGroup

basic_region_group = dict(
    id="RG1",
    include_in_region_group=True,
)

RegionGroup(**basic_region_group)
```
