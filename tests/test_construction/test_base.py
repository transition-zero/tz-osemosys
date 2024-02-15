import pytest

from feo.osemosys.schemas.base import OSeMOSYSBase

PASSING_BASE = dict(
    # nameplate params inherited from key
    all_params=dict(id="abc", long_name="basic long name", description="a basic descripion"),
    id_only=dict(id="abc"),
)

FAILING_BASE = dict(
    no_id=dict(long_name="a long name"),
)


def test_base_construction():
    for _name, params in PASSING_BASE.items():
        base = OSeMOSYSBase(**params)
        assert isinstance(getattr(base, "id", None), str)
        assert isinstance(getattr(base, "long_name", None), str)
        assert isinstance(getattr(base, "description", None), str)


def test_base_construction_failcases():
    for _name, params in FAILING_BASE.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            OSeMOSYSBase(**params)
