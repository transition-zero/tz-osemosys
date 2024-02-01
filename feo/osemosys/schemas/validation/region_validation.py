from feo.osemosys.utils import json_dict_to_dataframe


def region_validation(values):
    discount_rate = values.get("discount_rate")
    discount_rate_idv = values.get("discount_rate_idv")
    discount_rate_storage = values.get("discount_rate_storage")
    reserve_margin = values.get("reserve_margin")
    reserve_margin_tag_fuel = values.get("reserve_margin_tag_fuel")
    reserve_margin_tag_technology = values.get("reserve_margin_tag_technology")

    # Failed to fully describe reserve_margin
    if reserve_margin is not None and reserve_margin_tag_fuel is None:
        raise ValueError("If defining reserve_margin, reserve_margin_tag_fuel must be defined")
    if reserve_margin is not None and reserve_margin_tag_technology is None:
        raise ValueError(
            "If defining reserve_margin, reserve_margin_tag_technology must be defined"
        )

    # Check discount rates are in decimals
    if discount_rate is not None:
        df = json_dict_to_dataframe(discount_rate.data).iloc[:, -1]
        assert (df.abs() < 1).all(), "discount_rate should take decimal values"
    if discount_rate_idv is not None:
        df = json_dict_to_dataframe(discount_rate_idv.data).iloc[:, -1]
        assert (df.abs() < 1).all(), "discount_rate_idv should take decimal values"
    if discount_rate_storage is not None:
        df = json_dict_to_dataframe(discount_rate_storage.data).iloc[:, -1]
        assert (df.abs() < 1).all(), "discount_rate_storage should take decimal values"

    return values
