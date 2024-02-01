import xarray as xr
from linopy import Model


def add_energy_balance_b_constraints(ds: xr.Dataset, m: Model) -> Model:
    """Add Energy Balance B constraints to the model.
    Ensures that energy balances of all commodities are maintained for each year.

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
    s.t. EBb1_EnergyBalanceEachYear1{
        r in REGION, f in FUEL, y in YEAR}:
        sum{l in TIMESLICE} Production[r,l,f,y]
        =
        ProductionAnnual[r,f,y];

    s.t. EBb2_EnergyBalanceEachYear2{
        r in REGION, f in FUEL, y in YEAR}:
        sum{l in TIMESLICE} Use[r,l,f,y]
        =
        UseAnnual[r,f,y];

    s.t. EBb3_EnergyBalanceEachYear3{
        r in REGION, rr in REGION, f in FUEL, y in YEAR}:
        sum{l in TIMESLICE} Trade[r,rr,l,f,y]
        =
        TradeAnnual[r,rr,f,y];

    s.t. EBb4_EnergyBalanceEachYear4{
        r in REGION, f in FUEL, y in YEAR}:
        ProductionAnnual[r,f,y]
        >=
        UseAnnual[r,f,y] +
        sum{rr in REGION} TradeAnnual[r,rr,f,y] * TradeRoute[r,rr,f,y] +
        AccumulatedAnnualDemand[r,f,y];
    ```
    """
    con = m["Production"].sum(dims="TIMESLICE") - m["ProductionAnnual"] == 0
    m.add_constraints(con, name="EBb1_EnergyBalanceEachYear1")

    con = m["Use"].sum("TIMESLICE") - m["UseAnnual"] == 0
    m.add_constraints(con, name="EBb2_EnergyBalanceEachYear2")

    con = m["Trade"].sum("TIMESLICE") - m["TradeAnnual"] == 0
    mask = ds.coords["REGION"] != ds.coords["_REGION"]
    m.add_constraints(con, name="EBb3_EnergyBalanceEachYear3", mask=mask)

    con = m["ProductionAnnual"] - m["UseAnnual"] - (
        m["TradeAnnual"].sum("_REGION") * ds["TradeRoute"].sum("_REGION")
    ) >= ds["AccumulatedAnnualDemand"].fillna(0)
    m.add_constraints(con, name="EBb4_EnergyBalanceEachYear4")
    return m
