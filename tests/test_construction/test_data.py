import pytest

from tz.osemosys.schemas.base import OSeMOSYSData


def test_data_construction():
    od = OSeMOSYSData(6.0)
    assert od.data == 6.0
    od = OSeMOSYSData(data=6)
    assert od.data == 6.0
    od = OSeMOSYSData({"a": 6.0})
    assert od.data == {"a": 6.0}
    od = OSeMOSYSData(data={"a": 6.0})
    assert od.data == {"a": 6.0}
    od = OSeMOSYSData({"data": {"a": 6.0}})
    assert od.data == {"a": 6.0}


def test_data_construction_failcases():
    # fail on multiple non-'data' root keys
    with pytest.raises(ValueError) as e:  # noqa: F841
        OSeMOSYSData({"data": {"a": 6.0}, "other": 5.0})

    # fail on multiple args
    with pytest.raises(ValueError) as e:  # noqa: F841
        OSeMOSYSData(6.0, 5.0)
