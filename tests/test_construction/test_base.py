import pytest

from tz.osemosys.schemas.base import OSeMOSYSBase, OSeMOSYSData

PASSING_BASE = dict(
    # nameplate params inherited from key
    all_params=dict(id="abc", long_name="basic long name", description="a basic descripion"),
    id_only=dict(id="abc"),
)

FAILING_BASE = dict(
    no_id=dict(long_name="a long name"),
)

PASSING_BASE_INT = dict(
    just_an_int=dict(data=1),
    string_int=dict(data="1"),
    dict_of_int=dict(data={"a": 1, "b": 2}),
    dict_of_castable_int=dict(data={"a": "1", "b": "2"}),
)

FAILING_BASE_INT = dict(
    str_non_int=dict(data="hello"),
    dict_of_noncastable_int=dict(data={"a": "1", "b": "2."}),
)

PASSING_BASE_BOOL = dict(
    just_a_bool=dict(data=True),
    string_bool=dict(data="false"),
    dict_of_bool=dict(data={"a": True, "b": False}),
    dict_of_castable_int=dict(data={"a": "True", "b": "true"}),
)

FAILING_BASE_BOOL = dict(
    str_non_bool=dict(data="hello"),
    dict_of_noncastable_bool=dict(data={"a": "0", "b": "not a bool"}),
)

PASSING_BASE_DM = dict(
    cast=dict(data="sinking-fund"),
    dict_of_dm=dict(data={"a": "sinking-fund", "b": "straight-line"}),
)

FAILING_BASE_DM = dict(
    wrong_class_str=dict(data="hello"),
    dict_of_noncastable_str=dict(data={"a": "sinking-fund", "b": "hello"}),
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


def test_base_int_construction():
    for _name, params in PASSING_BASE_INT.items():
        OSeMOSYSData.ANY.Int(**params)


def test_base_int_construction_failcases():
    for _name, params in FAILING_BASE_INT.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            OSeMOSYSData.ANY.Int(**params)


def test_base_bool_construction():
    for _name, params in PASSING_BASE_BOOL.items():
        OSeMOSYSData.ANY.Bool(**params)


def test_base_bool_construction_failcases():
    for _name, params in FAILING_BASE_BOOL.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            OSeMOSYSData.ANY.Bool(**params)


def test_base_dm_construction():
    for _name, params in PASSING_BASE_DM.items():
        OSeMOSYSData.R.DM(**params)


def test_base_dm_construction_failcases():
    for _name, params in FAILING_BASE_DM.items():
        with pytest.raises(ValueError) as e:  # noqa: F841
            OSeMOSYSData.R.DM(**params)
