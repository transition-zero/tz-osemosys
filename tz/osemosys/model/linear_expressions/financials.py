from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_financials(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):

    CapitalInvestment = (
        ds["CapitalCost"].fillna(0)
        * m["NewCapacity"]
        * lex["CapitalRecoveryFactor"]
        * lex["PVAnnuity"]
    )

    DiscountedCapitalInvestment = CapitalInvestment / lex["DiscountFactor"]

    # costs
    AnnualVariableOperatingCost = (
        (lex["TotalAnnualTechnologyActivityByMode"] * ds["VariableCost"].fillna(0))
        .sum(dims="MODE_OF_OPERATION")
        .where(
            (ds["VariableCost"].sum(dim="MODE_OF_OPERATION") != 0)
            & (~ds["VariableCost"].sum(dim="MODE_OF_OPERATION").isnull())
        )
    )
    AnnualFixedOperatingCost = lex["GrossCapacity"] * ds["FixedCost"].fillna(0)
    OperatingCost = AnnualVariableOperatingCost + AnnualFixedOperatingCost

    # salvage value
    SV1Cost = ds["CapitalCost"].fillna(0) * (1 - (lex["SV1Numerator"] / lex["SV1Denominator"]))

    SV2Cost = ds["CapitalCost"].fillna(0) * (1 - (lex["SV2Numerator"] / lex["SV2Denominator"]))

    # costs
    DiscountedOperatingCost = OperatingCost / lex["DiscountFactorMid"]

    DiscountedCapitalInvestment = CapitalInvestment / lex["DiscountFactor"]

    SalvageValue = (
        m["NewCapacity"] * SV1Cost.where(lex["sv1_mask"])
        + m["NewCapacity"] * SV2Cost.where(lex["sv2_mask"])
    ).fillna(0)

    DiscountedSalvageValue = SalvageValue / lex["DiscountFactorSalvage"]

    # Total discounted costs
    TotalDiscountedCostByTechnology = (
        DiscountedCapitalInvestment + DiscountedOperatingCost - DiscountedSalvageValue
    )

    if ds["EMISSION"].size > 0:
        DiscountedTechnologyEmissionsPenalty = (
            lex["AnnualTechnologyEmissionsPenalty"] / lex["DiscountFactorMid"]
        )

        TotalDiscountedCostByTechnology = (
            TotalDiscountedCostByTechnology + DiscountedTechnologyEmissionsPenalty
        )

        lex.update(
            {
                "DiscountedTechnologyEmissionsPenalty": DiscountedTechnologyEmissionsPenalty,
            }
        )

    TotalDiscountedCost = TotalDiscountedCostByTechnology.sum("TECHNOLOGY")
    if ds["STORAGE"].size > 0:
        TotalDiscountedCost = TotalDiscountedCost + lex["TotalDiscountedStorageCost"].sum(
            ["STORAGE", "TECHNOLOGY"]
        )
    if ds["TradeRoute"].notnull().any():
        TotalDiscountedCost = TotalDiscountedCost + lex["TotalDiscountedCostTrade"].sum(
            ["FUEL", "_REGION"]
        )

    lex.update(
        {
            "CapitalInvestment": CapitalInvestment,
            "AnnualVariableOperatingCost": AnnualVariableOperatingCost,
            "AnnualFixedOperatingCost": AnnualFixedOperatingCost,
            "OperatingCost": OperatingCost,
            "DiscountedOperatingCost": DiscountedOperatingCost,
            "DiscountedCapitalInvestment": DiscountedCapitalInvestment,
            "DiscountedSalvageValue": DiscountedSalvageValue,
            "TotalDiscountedCostByTechnology": TotalDiscountedCostByTechnology,
            "TotalDiscountedCost": TotalDiscountedCost,
            "SV1Cost": SV1Cost,
            "SV2Cost": SV2Cost,
            "SalvageValue": SalvageValue,
        }
    )
