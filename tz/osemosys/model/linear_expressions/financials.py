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
    CapitalInvestmentTrade = (
        ds["CapitalCostTrade"].fillna(0)
        * m["NewTradeCapacity"]
        * lex["CapitalRecoveryFactorTrade"]
        * lex["PVAnnuityTrade"]
    )

    DiscountedCapitalInvestment = CapitalInvestment / lex["DiscountFactor"]

    DiscountedCapitalInvestmentTrade = CapitalInvestmentTrade / lex["DiscountFactorTrade"]

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

    # salvage value factors (trade)
    SV1CostTrade = ds["CapitalCostTrade"].fillna(0) * (
        1 - (lex["SV1NumeratorTrade"] / lex["SV1DenominatorTrade"])
    )

    SV2CostTrade = ds["CapitalCostTrade"].fillna(0) * (
        1 - (lex["SV2NumeratorTrade"] / lex["SV2DenominatorTrade"])
    )

    # salvage value (trade)
    SalvageValueTrade = (
        m["NewTradeCapacity"] * SV1CostTrade.where(lex["sv1_trade_mask"])
        + m["NewTradeCapacity"] * SV2CostTrade.where(lex["sv2_trade_mask"])
    ).fillna(0)

    DiscountedSalvageValueTrade = SalvageValueTrade / lex["DiscountFactorSalvageTrade"]

    # Total discounted costs
    TotalDiscountedCostByTechnology = (
        DiscountedCapitalInvestment + DiscountedOperatingCost - DiscountedSalvageValue
    )

    TotalDiscountedCostTrade = DiscountedCapitalInvestmentTrade + DiscountedSalvageValueTrade

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

    if ds["STORAGE"].size > 0:

        # total costs with storage
        TotalDiscountedCost = TotalDiscountedCostByTechnology.sum("TECHNOLOGY") + lex[
            "TotalDiscountedStorageCost"
        ].sum(["STORAGE", "TECHNOLOGY"])

    else:
        # total costs without storage
        TotalDiscountedCost = TotalDiscountedCostByTechnology.sum(
            "TECHNOLOGY"
        ) + TotalDiscountedCostTrade.sum(["FUEL", "_REGION"])

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
            "SV1CostTrade": SV1CostTrade,
            "SV2CostTrade": SV2CostTrade,
            "SalvageValueTrade": SalvageValueTrade,
            "CapitalInvestmentTrade": CapitalInvestmentTrade,
            "DiscountedCapitalInvestmentTrade": DiscountedCapitalInvestmentTrade,
            "DiscountedSalvageValueTrade": DiscountedSalvageValueTrade,
            "TotalDiscountedCostTrade": TotalDiscountedCostTrade,
        }
    )
