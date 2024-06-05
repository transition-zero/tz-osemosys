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
