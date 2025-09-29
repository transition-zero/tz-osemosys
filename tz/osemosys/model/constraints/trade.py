from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_trade_constraints(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]) -> Model:
    """Add Trade constraints to the model.
    Constrains capacity of trade between user-defined regions.

    Arguments
    ---------
    ds: xarray.Dataset
        The parameters dataset
    m: linopy.Model
        A linopy model
    lex: Dict[str, LinearExpression]

    Returns
    -------
    linopy.Model


    Notes
    -----
    ```ampl
    s.t. TC1a_TradeConstraint_Export{
        r in REGION, rr in REGION f in FUEL, l in TIMESLICE, y in YEAR}:
        TotalTradeCapacityAnnual[r,rr,f,y]
        * (1 + TradeLostBetweenRegions[r,rr,f,y])
        >=
        Export[r,rr,f,l,y] *
        / (CapacityToActivityUnit[r,t] * YearSplit[l,y]);

    s.t. TC1b_TradeConstraint_Import{
        r in REGION, rr in REGION f in FUEL, l in TIMESLICE, y in YEAR}:
        TotalTradeCapacityAnnual[r,rr,f,y]
        * (1 + TradeLostBetweenRegions[r,rr,f,y])
        >=
        Import[rr,r,f,l,y]
        / (CapacityToActivityUnit[r,t] * YearSplit[l,y]);

    s.t. TC4_TradeConstraint{
        r in REGION, rr in REGION f in FUEL, y in YEAR}:
        NewTradeCapacity[r,rr,f,y]
        <=
        TotalAnnualMaxTradeInvestment
        * TradeRoute[r,rr,f,y];
    ```
    """

    if (mask_ := ds["TradeRoute"] == 1).any():
        # Energy Balance
        con = (
            m["Export"]
            - m["Import"].rename({"REGION": "_REGION", "_REGION": "REGION"}) * ds["TradeRoute"]
            == 0
        )
        m.add_constraints(con, name="EBa10_EnergyBalanceEachTS4_trn", mask=mask_)

        # Capacity
        con = lex["GrossTradeCapacity"] * ds["TradeRoute"] * (
            1 - ds["TradeLossBetweenRegions"]
        ) >= m["Export"] / (ds["TradeCapacityToActivityUnit"] * ds["YearSplit"])
        m.add_constraints(con, name="TC1a_TradeConstraint_Export", mask=mask_)

        con = lex["GrossTradeCapacity"] * ds["TradeRoute"] * (
            1 - ds["TradeLossBetweenRegions"]
        ) >= m["Import"].rename({"REGION": "_REGION", "_REGION": "REGION"}) / (
            ds["TradeCapacityToActivityUnit"] * ds["YearSplit"]
        )
        m.add_constraints(con, name="TC1b_TradeConstraint_Import", mask=mask_)

        con = m["NewTradeCapacity"] <= ds["TotalAnnualMaxTradeInvestment"] * ds["TradeRoute"]
        mask = mask_ & ds["TotalAnnualMaxTradeInvestment"].notnull()
        m.add_constraints(con, name="TC4_TradeConstraint", mask=mask)

        # Activity constraints
        # absolute annual activity constraints:
        con = lex["NetTradeAnnual"] <= ds["TotalTradeAnnualActivityUpperLimit"] * ds["TradeRoute"]
        mask = mask_ & ds["TotalTradeAnnualActivityUpperLimit"].notnull()
        m.add_constraints(con, name="TradeConstraint_TotalTradeAnnualActivityUpperLimit", mask=mask)
        con = lex["NetTradeAnnual"] >= ds["TotalTradeAnnualActivityLowerLimit"] * ds["TradeRoute"]
        mask = mask_ & ds["TotalTradeAnnualActivityLowerLimit"].notnull()
        m.add_constraints(con, name="TradeConstraint_TotalTradeAnnualActivityLowerLimit", mask=mask)
        # availability factor constraints:
        con = (
            lex["NetTradeAnnual"]
            <= lex["GrossTradeCapacity"]
            * ds["TradeRoute"]
            * ds["AvailabilityFactorTrade"]
            * ds["TradeCapacityToActivityUnit"]
        )
        mask = mask_ & ds["AvailabilityFactorTrade"].notnull()
        m.add_constraints(con, name="TradeConstraint_AvailabilityFactor", mask=mask)
        con = (
            lex["NetTradeAnnual"]
            >= lex["GrossTradeCapacity"]
            * ds["TradeRoute"]
            * ds["TotalAnnualMinCapacityFactorTrade"]
            * ds["TradeCapacityToActivityUnit"]
        )
        mask = mask_ & ds["TotalAnnualMinCapacityFactorTrade"].notnull()
        m.add_constraints(con, name="TradeConstraint_AvailabilityFactorMin", mask=mask)

    return m
