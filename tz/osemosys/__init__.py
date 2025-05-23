from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("tz-osemosys")
except PackageNotFoundError:
    # package is not installed
    pass

from tz.osemosys.io.load_model import load_model
from tz.osemosys.model.model import Model
from tz.osemosys.schemas.commodity import Commodity
from tz.osemosys.schemas.impact import Impact
from tz.osemosys.schemas.region import Region, RegionGroup
from tz.osemosys.schemas.storage import Storage
from tz.osemosys.schemas.technology import OperatingMode, Technology
from tz.osemosys.schemas.time_definition import TimeDefinition

__all__ = [
    "Model",
    "Commodity",
    "Technology",
    "Storage",
    "Impact",
    "Region",
    "RegionGroup",
    "TimeDefinition",
    "OperatingMode",
    "load_model",
]
