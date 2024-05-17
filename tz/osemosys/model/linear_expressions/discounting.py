from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_discounting(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):

    # discounting
    DiscountFactor = (1 + ds["DiscountRate"]) ** (ds.coords["YEAR"] - min(ds.coords["YEAR"]))

    DiscountFactorMid = (1 + ds["DiscountRate"]) ** (
        ds.coords["YEAR"] - min(ds.coords["YEAR"]) + 0.5
    )

    DiscountFactorSalvage = (1 + ds["DiscountRateIdv"]) ** (
        1 + max(ds.coords["YEAR"]) - min(ds.coords["YEAR"])
    )

    PVAnnuity = (
        (1 - (1 + ds["DiscountRateIdv"]) ** (-(ds["OperationalLife"])))
        * (1 + ds["DiscountRateIdv"])
        / ds["DiscountRateIdv"]
    )

    CapitalRecoveryFactor = (1 - (1 + ds["DiscountRateIdv"]) ** (-1)) / (
        1 - (1 + ds["DiscountRateIdv"]) ** (-(ds["OperationalLife"]))
    )

    # salvage value
    SV1Numerator = (1 + ds["DiscountRateIdv"]) ** (
        max(ds.coords["YEAR"]) - ds.coords["YEAR"] + 1
    ) - 1

    SV1Denominator = (1 + ds["DiscountRateIdv"]) ** ds["OperationalLife"] - 1

    SV2Numerator = max(ds.coords["YEAR"]) - ds.coords["YEAR"] + 1

    SV2Denominator = ds["OperationalLife"]

    sv1_mask = (
        (ds["DepreciationMethod"] == 1)
        & ((ds.coords["YEAR"] + ds["OperationalLife"] - 1) > max(ds.coords["YEAR"]))
        & (ds["DiscountRateIdv"] > 0)
    )
    sv2_mask = (
        (ds["DepreciationMethod"] == 1)
        & ((ds.coords["YEAR"] + ds["OperationalLife"] - 1) > max(ds.coords["YEAR"]))
        & (ds["DiscountRateIdv"] == 0)
    ) | (
        (ds["DepreciationMethod"] == 2)
        & ((ds.coords["YEAR"] + ds["OperationalLife"] - 1) > max(ds.coords["YEAR"]))
    )

    lex.update(
        {
            "DiscountFactor": DiscountFactor,
            "DiscountFactorMid": DiscountFactorMid,
            "DiscountFactorSalvage": DiscountFactorSalvage,
            "PVAnnuity": PVAnnuity,
            "CapitalRecoveryFactor": CapitalRecoveryFactor,
            "SV1Numerator": SV1Numerator,
            "SV1Denominator": SV1Denominator,
            "SV2Numerator": SV2Numerator,
            "SV2Denominator": SV2Denominator,
            "sv1_mask": sv1_mask,
            "sv2_mask": sv2_mask,
        }
    )
