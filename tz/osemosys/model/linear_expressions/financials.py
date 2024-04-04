from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_financials(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):

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

    CapitalInvestment = (
        ds["CapitalCost"].fillna(0) * m["NewCapacity"] * CapitalRecoveryFactor * PVAnnuity
    )

    # costs
    AnnualVariableOperatingCost = (
        (lex["TotalAnnualTechnologyActivityByMode"] * ds["VariableCost"].fillna(0))
        .sum(dims="MODE_OF_OPERATION")
        .where(
            (ds["VariableCost"].sum(dim="MODE_OF_OPERATION") != 0)
            & (~ds["VariableCost"].sum(dim="MODE_OF_OPERATION").isnull())
        )
    )
    AnnualFixedOperatingCost = m["TotalCapacityAnnual"] * ds["FixedCost"].fillna(0)
    OperatingCost = AnnualVariableOperatingCost + AnnualFixedOperatingCost

    # salvage value
    SV1Numerator = (1 + ds["DiscountRateIdv"]) ** (
        max(ds.coords["YEAR"]) - ds.coords["YEAR"] + 1
    ) - 1

    SV1Denominator = (1 + ds["DiscountRateIdv"]) ** ds["OperationalLife"] - 1

    SV1Cost = ds["CapitalCost"].fillna(0) * (1 - (SV1Numerator / SV1Denominator))

    SV2Numerator = max(ds.coords["YEAR"]) - ds.coords["YEAR"] + 1

    SV2Denominator = ds["OperationalLife"]

    SV2Cost = ds["CapitalCost"].fillna(0) * (1 - (SV2Numerator / SV2Denominator))

    lex.update(
        {
            "DiscountFactor": DiscountFactor,
            "DiscountFactorMid": DiscountFactorMid,
            "DiscountFactorSalvage": DiscountFactorSalvage,
            "PVAnnuity": PVAnnuity,
            "CapitalRecoveryFactor": CapitalRecoveryFactor,
            "CapitalInvestment": CapitalInvestment,
            "AnnualVariableOperatingCost": AnnualVariableOperatingCost,
            "AnnualFixedOperatingCost": AnnualFixedOperatingCost,
            "OperatingCost": OperatingCost,
            "SV1Cost": SV1Cost,
            "SV2Cost": SV2Cost,
        }
    )
