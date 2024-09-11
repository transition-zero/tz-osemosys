from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_energy_balance_a_constraints(
    ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]
) -> Model:
    """Add Energy Balance A constraints to the model.
    Ensures that energy balances of all commodities are maintained for each timeslice.

    Arguments
    ---------
    ds: xarray.Dataset
        The parameters dataset
    m: linopy.Model
        A linopy model
    lex: Dict[str, LinearExpression]
        A dictionary of linear expressions, persisted after solve

    Returns
    -------
    linopy.Model


    Notes
    -----
    ```ampl
    s.t. EBa1_RateOfFuelProduction1{
        r in REGION, l in TIMESLICE, f in FUEL, t in TECHNOLOGY, m in MODE_OF_OPERATION, y in YEAR:
        OutputActivityRatio[r,t,f,m,y] <> 0}:
        RateOfActivity[r,l,t,m,y] * OutputActivityRatio[r,t,f,m,y]
        =
        RateOfProductionByTechnologyByMode[r,l,t,m,f,y];

    s.t. EBa2_RateOfFuelProduction2{
        r in REGION, l in TIMESLICE, f in FUEL, t in TECHNOLOGY, y in YEAR}:
        sum{m in MODE_OF_OPERATION: OutputActivityRatio[r,t,f,m,y] <> 0}
        RateOfProductionByTechnologyByMode[r,l,t,m,f,y]
        =
        RateOfProductionByTechnology[r,l,t,f,y];

    s.t. EBa3_RateOfFuelProduction3{
        r in REGION, l in TIMESLICE, f in FUEL, y in YEAR:
        (sum{t in TECHNOLOGY, m in MODE_OF_OPERATION} OutputActivityRatio[r,t,f,m,y]) <> 0}:
        sum{t in TECHNOLOGY} RateOfProductionByTechnology[r,l,t,f,y]
        =
        RateOfProduction[r,l,f,y];

    s.t. EBa4_RateOfFuelUse1{
        r in REGION, l in TIMESLICE, f in FUEL, t in TECHNOLOGY, m in MODE_OF_OPERATION, y in YEAR:
        InputActivityRatio[r,t,f,m,y] <> 0}:
        RateOfActivity[r,l,t,m,y] * InputActivityRatio[r,t,f,m,y]
        =
        RateOfUseByTechnologyByMode[r,l,t,m,f,y];

    s.t. EBa5_RateOfFuelUse2{
        r in REGION, l in TIMESLICE, f in FUEL, t in TECHNOLOGY, y in YEAR:
        sum{m in MODE_OF_OPERATION} InputActivityRatio[r,t,f,m,y] <> 0}:
        sum{m in MODE_OF_OPERATION: InputActivityRatio[r,t,f,m,y] <> 0}
        RateOfUseByTechnologyByMode[r,l,t,m,f,y]
        =
        RateOfUseByTechnology[r,l,t,f,y];

    s.t. EBa6_RateOfFuelUse3{
        r in REGION, l in TIMESLICE, f in FUEL, y in YEAR:
        sum{t in TECHNOLOGY, m in MODE_OF_OPERATION} InputActivityRatio[r,t,f,m,y] <> 0}:
        sum{t in TECHNOLOGY} RateOfUseByTechnology[r,l,t,f,y]
        =
        RateOfUse[r,l,f,y];

    s.t. EBa7_EnergyBalanceEachTS1{
        r in REGION, l in TIMESLICE, f in FUEL, y in YEAR:
        (sum{t in TECHNOLOGY, m in MODE_OF_OPERATION} OutputActivityRatio[r,t,f,m,y]) <> 0}:
        RateOfProduction[r,l,f,y] * YearSplit[l,y]
        =
        Production[r,l,f,y];

    s.t. EBa8_EnergyBalanceEachTS2{
        r in REGION, l in TIMESLICE, f in FUEL, y in YEAR:
        (sum{t in TECHNOLOGY, m in MODE_OF_OPERATION} InputActivityRatio[r,t,f,m,y]) <> 0}:
        RateOfUse[r,l,f,y] * YearSplit[l,y]
        =
        Use[r,l,f,y];

    s.t. EBa9_EnergyBalanceEachTS3{
        r in REGION, l in TIMESLICE, f in FUEL, y in YEAR:
        SpecifiedAnnualDemand[r,f,y] <> 0}:
        RateOfDemand[r,l,f,y] * YearSplit[l,y]
        =
        Demand[r,l,f,y];

    s.t. EBa10_EnergyBalanceEachTS4{
        r in REGION, rr in REGION, l in TIMESLICE, f in FUEL, y in YEAR:
        TradeRoute[r,rr,f,y] <> 0}:
        Trade[r,rr,l,f,y]
        =
        -Trade[rr,r,l,f,y];

    s.t. EBa11_EnergyBalanceEachTS5{
        r in REGION, l in TIMESLICE, f in FUEL, y in YEAR}:
        Production[r,l,f,y]
        >=
        Demand[r,l,f,y] + Use[r,l,f,y] + sum{rr in REGION} Trade[r,rr,l,f,y] * TradeRoute[r,rr,f,y];

    s.t. EBa12_EnergyBalanceEachTS5{
        r in REGION, l in TIMESLICE, f in FUEL, y in YEAR}:
        Production[r,l,f,y]
        >=
        Demand[r,l,f,y] + Use[r,l,f,y] + sum{rr in REGION} Trade[r,rr,l,f,y] * TradeRoute[r,rr,f,y];

    ```
    """

    # Constraint
    con = (
        lex["Production"]
        - (ds["SpecifiedAnnualDemand"] * ds["SpecifiedDemandProfile"])
        - lex["Use"]
        - lex["NetTrade"]
    ) >= 0
    m.add_constraints(con, name="EBa11_EnergyBalanceEachTS5_trn")
    return m
