# functionality for writing model to .yaml
import inspect
import yaml
from tz.osemosys.schemas.base import OSeMOSYSBase


def dump_resource(resource: OSeMOSYSBase) -> str:
    cls = resource.__class__
    fields = inspect.signature(cls).parameters.keys()
    return yaml.dump(
        {field: getattr(resource, field) for field in fields},
        default_flow_style=False,
        sort_keys=False,
    )
