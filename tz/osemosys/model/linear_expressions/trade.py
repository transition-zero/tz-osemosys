from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_trade(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):

    # Capacity #
    NewTradeCapacity = m["NewTradeCapacity"].rename(YEAR="BUILDYEAR")
    mask = (ds.YEAR - NewTradeCapacity.data.BUILDYEAR >= 0) & (
        ds.YEAR - NewTradeCapacity.data.BUILDYEAR < ds.OperationalLifeTrade
    )
    AccumulatedNewTradeCapacity = NewTradeCapacity.where(mask).sum("BUILDYEAR")
    GrossTradeCapacity = AccumulatedNewTradeCapacity + ds["ResidualTradeCapacity"].fillna(0)

    # Activity #
    NetTrade = (
        ((m["Export"] / (1 - ds["TradeLossBetweenRegions"])) - m["Import"])
        .where(ds["TradeRoute"].notnull())
        .sum("_REGION")
        .fillna(0)
    )
    NetTradeAnnual = NetTrade.sum("TIMESLICE")

    # Discounting #
    DiscountFactorTrade = (1 + ds["DiscountRateTrade"]) ** (
        ds.coords["YEAR"] - min(ds.coords["YEAR"])
    )

    DiscountFactorSalvageTrade = (1 + ds["DiscountRateTrade"]) ** (
        1 + max(ds.coords["YEAR"]) - min(ds.coords["YEAR"])
    )

    PVAnnuityTrade = (
        (1 - (1 + ds["DiscountRateTrade"]) ** (-(ds["OperationalLifeTrade"])))
        * (1 + ds["DiscountRateTrade"])
        / ds["DiscountRateTrade"]
    )

    CapitalRecoveryFactorTrade = (1 - (1 + ds["DiscountRateTrade"]) ** (-1)) / (
        1 - (1 + ds["DiscountRateTrade"]) ** (-(ds["OperationalLifeTrade"]))
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

    # Financials #
    CapitalInvestmentTrade = (
        ds["CapitalCostTrade"].fillna(0)
        * m["NewTradeCapacity"]
        * CapitalRecoveryFactorTrade
        * PVAnnuityTrade
    )

    DiscountedCapitalInvestmentTrade = CapitalInvestmentTrade / DiscountFactorTrade

    # salvage value factors (trade)
    SV1CostTrade = ds["CapitalCostTrade"].fillna(0) * (
        1 - (SV1NumeratorTrade / SV1DenominatorTrade)
    )

    SV2CostTrade = ds["CapitalCostTrade"].fillna(0) * (
        1 - (SV2NumeratorTrade / SV2DenominatorTrade)
    )

    # salvage value (trade)
    SalvageValueTrade = (
        m["NewTradeCapacity"] * SV1CostTrade.where(sv1_trade_mask)
        + m["NewTradeCapacity"] * SV2CostTrade.where(sv2_trade_mask)
    ).fillna(0)

    DiscountedSalvageValueTrade = SalvageValueTrade / DiscountFactorSalvageTrade

    TotalDiscountedCostTrade = DiscountedCapitalInvestmentTrade + DiscountedSalvageValueTrade

    lex.update(
        {
            "NewTradeCapacity": NewTradeCapacity,
            "AccumulatedNewTradeCapacity": AccumulatedNewTradeCapacity,
            "GrossTradeCapacity": GrossTradeCapacity,
            "NetTrade": NetTrade,
            "NetTradeAnnual": NetTradeAnnual,
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
            "SV1CostTrade": SV1CostTrade,
            "SV2CostTrade": SV2CostTrade,
            "SalvageValueTrade": SalvageValueTrade,
            "CapitalInvestmentTrade": CapitalInvestmentTrade,
            "DiscountedCapitalInvestmentTrade": DiscountedCapitalInvestmentTrade,
            "DiscountedSalvageValueTrade": DiscountedSalvageValueTrade,
            "TotalDiscountedCostTrade": TotalDiscountedCostTrade,
        }
    )
