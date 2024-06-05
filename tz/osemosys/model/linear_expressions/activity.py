from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_activity(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):
    RateOfTotalActivity = m["RateOfActivity"].sum(dims="MODE_OF_OPERATION")
    TotalTechnologyAnnualActivity = (RateOfTotalActivity * ds["YearSplit"]).sum("TIMESLICE")
    TotalAnnualTechnologyActivityByMode = (m["RateOfActivity"] * ds["YearSplit"]).sum("TIMESLICE")
    TotalTechnologyModelPeriodActivity = TotalTechnologyAnnualActivity.sum(dims="YEAR")
    NetTrade = (
        ((m["Export"] / (1 - ds["TradeLossBetweenRegions"])) - m["Import"])
        .where(ds["TradeRoute"].notnull())
        .sum("_REGION")
        .fillna(0)
    )
    NetTradeAnnual = NetTrade.sum("TIMESLICE")

    lex.update(
        {
            "RateOfTotalActivity": RateOfTotalActivity,
            "TotalTechnologyAnnualActivity": TotalTechnologyAnnualActivity,
            "TotalAnnualTechnologyActivityByMode": TotalAnnualTechnologyActivityByMode,
            "TotalTechnologyModelPeriodActivity": TotalTechnologyModelPeriodActivity,
            "NetTrade": NetTrade,
            "NetTradeAnnual": NetTradeAnnual,
        }
    )
