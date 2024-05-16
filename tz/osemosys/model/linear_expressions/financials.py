from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_financials(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):

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

    CapitalRecoveryFactor = (1 - (1 + ds["DiscountRateIdv"]) ** (-1)) / (
        1 - (1 + ds["DiscountRateIdv"]) ** (-(ds["OperationalLife"]))
    )

    CapitalInvestment = (
        ds["CapitalCost"].fillna(0) * m["NewCapacity"] * CapitalRecoveryFactor * PVAnnuity
    )

    PVAnnuityTrade = (
        (1 - (1 + ds["DiscountRateTrade"]) ** (-(ds["OperationalLifeTrade"])))
        * (1 + ds["DiscountRateTrade"])
        / ds["DiscountRateTrade"]
    )

    CapitalRecoveryFactorTrade = (1 - (1 + ds["DiscountRateTrade"]) ** (-1)) / (
        1 - (1 + ds["DiscountRateTrade"]) ** (-(ds["OperationalLifeTrade"]))
    )
    CapitalInvestmentTrade = (
        ds["CapitalCostTrade"].fillna(0)
        * m["NewCapacityTrade"]
        * CapitalRecoveryFactorTrade
        * PVAnnuityTrade
    )

    DiscountedCapitalInvestment = CapitalInvestment / DiscountFactor

    DiscountedCapitalInvestmentTrade = CapitalInvestmentTrade / DiscountFactorTrade

    # operating costs
    AnnualVariableOperatingCost = (
        (lex["TotalAnnualTechnologyActivityByMode"] * ds["VariableCost"].fillna(0))
        .sum(dims="MODE_OF_OPERATION")
        .where(
            (ds["VariableCost"].sum(dim="MODE_OF_OPERATION") != 0)
            & (~ds["VariableCost"].sum(dim="MODE_OF_OPERATION").isnull())
        )
    )
    AnnualFixedOperatingCost = lex["TotalCapacityAnnual"] * ds["FixedCost"].fillna(0)
    OperatingCost = AnnualVariableOperatingCost + AnnualFixedOperatingCost

    DiscountedOperatingCost = OperatingCost / DiscountFactorMid

    # salvage value factors (non-trade)
    SV1Numerator = (1 + ds["DiscountRateIdv"]) ** (
        max(ds.coords["YEAR"]) - ds.coords["YEAR"] + 1
    ) - 1

    SV1Denominator = (1 + ds["DiscountRateIdv"]) ** ds["OperationalLife"] - 1

    SV1Cost = ds["CapitalCost"].fillna(0) * (1 - (SV1Numerator / SV1Denominator))

    SV2Numerator = max(ds.coords["YEAR"]) - ds.coords["YEAR"] + 1

    SV2Denominator = ds["OperationalLife"]

    SV2Cost = ds["CapitalCost"].fillna(0) * (1 - (SV2Numerator / SV2Denominator))

    # salvage value (non-trade)

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

    SalvageValue = (
        m["NewCapacity"] * SV1Cost.where(sv1_mask) + m["NewCapacity"] * SV2Cost.where(sv2_mask)
    ).fillna(0)

    DiscountedSalvageValue = SalvageValue / DiscountFactorSalvage

    # salvage value factors (trade)
    SV1NumeratorTrade = (1 + ds["DiscountRateTrade"]) ** (
        max(ds.coords["YEAR"]) - ds.coords["YEAR"] + 1
    ) - 1

    SV1DenominatorTrade = (1 + ds["DiscountRateTrade"]) ** ds["OperationalLifeTrade"] - 1

    SV1CostTrade = ds["CapitalCostTrade"].fillna(0) * (
        1 - (SV1NumeratorTrade / SV1DenominatorTrade)
    )

    SV2NumeratorTrade = max(ds.coords["YEAR"]) - ds.coords["YEAR"] + 1

    SV2DenominatorTrade = ds["OperationalLifeTrade"]

    SV2CostTrade = ds["CapitalCostTrade"].fillna(0) * (
        1 - (SV2NumeratorTrade / SV2DenominatorTrade)
    )

    # salvage value (trade)
    sv1_mask = (
        (ds["DepreciationMethod"] == 1)
        & ((ds.coords["YEAR"] + ds["OperationalLifeTrade"] - 1) > max(ds.coords["YEAR"]))
        & (ds["DiscountRateTrade"] > 0)
    )
    sv2_mask = (
        (ds["DepreciationMethod"] == 1)
        & ((ds.coords["YEAR"] + ds["OperationalLifeTrade"] - 1) > max(ds.coords["YEAR"]))
        & (ds["DiscountRateTrade"] == 0)
    ) | (
        (ds["DepreciationMethod"] == 2)
        & ((ds.coords["YEAR"] + ds["OperationalLifeTrade"] - 1) > max(ds.coords["YEAR"]))
    )

    SalvageValueTrade = (
        m["NewCapacityTrade"] * SV1CostTrade.where(sv1_mask)
        + m["NewCapacityTrade"] * SV2CostTrade.where(sv2_mask)
    ).fillna(0)

    DiscountedSalvageValueTrade = SalvageValueTrade / DiscountFactorSalvageTrade

    # Total discounted costs
    TotalDiscountedCostByTechnology = (
        DiscountedCapitalInvestment + DiscountedOperatingCost - DiscountedSalvageValue
    )

    TotalDiscountedCostTrade = DiscountedCapitalInvestmentTrade + DiscountedSalvageValueTrade

    if ds["EMISSION"].size > 0:
        DiscountedTechnologyEmissionsPenalty = (
            lex["AnnualTechnologyEmissionsPenalty"] / DiscountFactorMid
        )

        TotalDiscountedCostByTechnology = (
            TotalDiscountedCostByTechnology
            + DiscountedTechnologyEmissionsPenalty
            + TotalDiscountedCostTrade
        )

        lex.update(
            {
                "DiscountedTechnologyEmissionsPenalty": DiscountedTechnologyEmissionsPenalty,
            }
        )

    if ds["STORAGE"].size > 0:
        # total costs with storage
        TotalDiscountedCost = (
            TotalDiscountedCostByTechnology.sum("TECHNOLOGY")
            + m["TotalDiscountedStorageCost"].sum("STORAGE")
            + TotalDiscountedCostTrade
        )

    else:
        # total costs without storage
        TotalDiscountedCost = (
            TotalDiscountedCostByTechnology.sum("TECHNOLOGY") + TotalDiscountedCostTrade
        )

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
            "DiscountFactorTrade": DiscountFactorTrade,
            "DiscountFactorSalvageTrade": DiscountFactorSalvageTrade,
            "PVAnnuityTrade": PVAnnuityTrade,
            "CapitalRecoveryFactorTrade": CapitalRecoveryFactorTrade,
            "CapitalInvestmentTrade": CapitalInvestmentTrade,
            "DiscountedCapitalInvestmentTrade": DiscountedCapitalInvestmentTrade,
            "DiscountedSalvageValueTrade": DiscountedSalvageValueTrade,
            "TotalDiscountedCostTrade": TotalDiscountedCostTrade,
        }
    )
