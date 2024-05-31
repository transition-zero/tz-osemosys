from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_discounting(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):

    # discounting
    DiscountFactor = (1 + ds["DiscountRate"]) ** (ds.coords["YEAR"] - min(ds.coords["YEAR"]))

    DiscountFactorTrade = (1 + ds["DiscountRateTrade"]) ** (
        ds.coords["YEAR"] - min(ds.coords["YEAR"])
    )

    DiscountFactorMid = (1 + ds["DiscountRate"]) ** (
        ds.coords["YEAR"] - min(ds.coords["YEAR"]) + 0.5
    )

    DiscountFactorSalvage = (1 + ds["DiscountRateIdv"]) ** (
        1 + max(ds.coords["YEAR"]) - min(ds.coords["YEAR"])
    )

    DiscountFactorSalvageTrade = (1 + ds["DiscountRateTrade"]) ** (
        1 + max(ds.coords["YEAR"]) - min(ds.coords["YEAR"])
    )

    PVAnnuity = (
        (1 - (1 + ds["DiscountRateIdv"]) ** (-(ds["OperationalLife"])))
        * (1 + ds["DiscountRateIdv"])
        / ds["DiscountRateIdv"]
    )

    PVAnnuityTrade = (
        (1 - (1 + ds["DiscountRateTrade"]) ** (-(ds["OperationalLifeTrade"])))
        * (1 + ds["DiscountRateTrade"])
        / ds["DiscountRateTrade"]
    )

    CapitalRecoveryFactor = (1 - (1 + ds["DiscountRateIdv"]) ** (-1)) / (
        1 - (1 + ds["DiscountRateIdv"]) ** (-(ds["OperationalLife"]))
    )

    CapitalRecoveryFactorTrade = (1 - (1 + ds["DiscountRateTrade"]) ** (-1)) / (
        1 - (1 + ds["DiscountRateTrade"]) ** (-(ds["OperationalLifeTrade"]))
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

    SV1NumeratorTrade = (1 + ds["DiscountRateTrade"]) ** (
        max(ds.coords["YEAR"]) - ds.coords["YEAR"] + 1
    ) - 1

    SV1DenominatorTrade = (1 + ds["DiscountRateTrade"]) ** ds["OperationalLifeTrade"] - 1

    SV2NumeratorTrade = max(ds.coords["YEAR"]) - ds.coords["YEAR"] + 1

    SV2DenominatorTrade = ds["OperationalLifeTrade"]

    sv1_trade_mask = (
        (ds["DepreciationMethod"] == 1)
        & ((ds.coords["YEAR"] + ds["OperationalLifeTrade"] - 1) > max(ds.coords["YEAR"]))
        & (ds["DiscountRateTrade"] > 0)
    )
    sv2_trade_mask = (
        (ds["DepreciationMethod"] == 1)
        & ((ds.coords["YEAR"] + ds["OperationalLifeTrade"] - 1) > max(ds.coords["YEAR"]))
        & (ds["DiscountRateTrade"] == 0)
    ) | (
        (ds["DepreciationMethod"] == 2)
        & ((ds.coords["YEAR"] + ds["OperationalLifeTrade"] - 1) > max(ds.coords["YEAR"]))
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
            "SV1NumeratorTrade": SV1NumeratorTrade,
            "SV1DenominatorTrade": SV1DenominatorTrade,
            "SV2NumeratorTrade": SV2NumeratorTrade,
            "SV2DenominatorTrade": SV2DenominatorTrade,
            "sv1_trade_mask": sv1_trade_mask,
            "sv2_trade_mask": sv2_trade_mask,
            "DiscountFactorTrade": DiscountFactorTrade,
            "DiscountFactorSalvageTrade": DiscountFactorSalvageTrade,
            "PVAnnuityTrade": PVAnnuityTrade,
            "CapitalRecoveryFactorTrade": CapitalRecoveryFactorTrade,
        }
    )
