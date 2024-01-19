import xarray as xr
from linopy import Model


def add_energy_balance_a_constraints(ds: xr.Dataset, m: Model) -> Model:
    """Add Energy Balance A constraints to the model

    Arguments
    ---------
    ds: xarray.Dataset
        The parameters dataset
    m: linopy.Model
        A linopy model

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
    ```
    """
    mask = ds["OutputActivityRatio"].notnull()
    con = (
        m["RateOfActivity"] * ds["OutputActivityRatio"] - m["RateOfProductionByTechnologyByMode"]
        == 0
    )
    m.add_constraints(con, name="EBa1_RateOfFuelProduction1", mask=mask)

    mask = ds["OutputActivityRatio"].sum("MODE_OF_OPERATION") != 0
    con = (
        m["RateOfProductionByTechnologyByMode"].where(mask).sum(dims="MODE_OF_OPERATION")
        - m["RateOfProductionByTechnology"]
        == 0
    )
    m.add_constraints(con, name="EBa2_RateOfFuelProduction2", mask=mask)

    mask = ds["OutputActivityRatio"].sum(dim=["TECHNOLOGY", "MODE_OF_OPERATION"]) != 0
    con = m["RateOfProductionByTechnology"].sum(dims="TECHNOLOGY") - m["RateOfProduction"] == 0
    m.add_constraints(con, name="EBa3_RateOfFuelProduction3", mask=mask)

    mask = ds["InputActivityRatio"].notnull()
    con = m["RateOfActivity"] * ds["InputActivityRatio"] - m["RateOfUseByTechnologyByMode"] == 0
    m.add_constraints(con, name="EBa4_RateOfFuelUse1", mask=mask)

    con = (
        m["RateOfUseByTechnologyByMode"].sum(dims="MODE_OF_OPERATION") - m["RateOfUseByTechnology"]
        == 0
    )
    mask = ds["InputActivityRatio"].sum(dim="MODE_OF_OPERATION") != 0
    m.add_constraints(con, name="EBa5_RateOfFuelUse2", mask=mask)

    con = m["RateOfUseByTechnology"].sum(dims="TECHNOLOGY") - m["RateOfUse"] == 0
    mask = ds["InputActivityRatio"].sum(dim=["TECHNOLOGY", "MODE_OF_OPERATION"]) != 0
    m.add_constraints(con, name="EBa6_RateOfFuelUse3", mask=mask)

    con = (m["RateOfProduction"] * ds["YearSplit"]) - m["Production"] == 0
    mask = ds["OutputActivityRatio"].sum(dim=["TECHNOLOGY", "MODE_OF_OPERATION"]) != 0
    m.add_constraints(con, name="EBa7_EnergyBalanceEachTS1", mask=mask)

    con = (m["RateOfUse"] * ds["YearSplit"]) - m["Use"] == 0
    mask = ds["InputActivityRatio"].sum(dim=["TECHNOLOGY", "MODE_OF_OPERATION"]) != 0
    m.add_constraints(con, name="EBa8_EnergyBalanceEachTS2", mask=mask)

    con = (m["RateOfDemand"] * ds["YearSplit"]) - m["Demand"] == 0
    mask = ds["SpecifiedAnnualDemand"].notnull()
    m.add_constraints(con, name="EBa9_EnergyBalanceEachTS3", mask=mask)

    tr = ds["TradeRoute"]
    from_mask = tr.where(tr.REGION != tr._REGION).notnull()
    to_mask = tr.where(tr._REGION != tr.REGION).notnull()
    con = m["Trade"].where(from_mask) + m["Trade"].where(to_mask) == 0
    m.add_constraints(con, name="EBa10_EnergyBalanceEachTS4")

    con = (
        m["Production"]
        - (m["Demand"] + m["Use"] + (m["Trade"] * ds["TradeRoute"].fillna(0)).sum(dims="_REGION"))
        >= 0
    )
    m.add_constraints(con, name="EBa11_EnergyBalanceEachTS5")
    return m
