import xarray as xr
from linopy import Model


def add_re_targets_constraints(ds: xr.Dataset, m: Model) -> Model:
    """Add Renewable Energy target constraints to the model

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
    s.t. RE1_FuelProductionByTechnologyAnnual{
        r in REGION, t in TECHNOLOGY, f in FUEL, y in YEAR}:
        sum{l in TIMESLICE} ProductionByTechnology[r,l,t,f,y] =
        ProductionByTechnologyAnnual[r,t,f,y];

    s.t. RE2_TechIncluded{
        r in REGION, y in YEAR}:
        sum{t in TECHNOLOGY, f in FUEL}
        ProductionByTechnologyAnnual[r,t,f,y]*RETagTechnology[r,t,y] =
        TotalREProductionAnnual[r,y];

    s.t. RE3_FuelIncluded{
        r in REGION, y in YEAR}:
        sum{l in TIMESLICE, f in FUEL}
        RateOfProduction[r,l,f,y]*YearSplit[l,y]*RETagFuel[r,f,y] =
        RETotalProductionOfTargetFuelAnnual[r,y];

    s.t. RE4_EnergyConstraint{
        r in REGION, y in YEAR}:
        REMinProductionTarget[r,y] * RETotalProductionOfTargetFuelAnnual[r,y] <=
        TotalREProductionAnnual[r,y];

    s.t. RE5_FuelUseByTechnologyAnnual{
        r in REGION, t in TECHNOLOGY, f in FUEL, y in YEAR}:
        sum{l in TIMESLICE} RateOfUseByTechnology[r,l,t,f,y] * YearSplit[l,y] =
        UseByTechnologyAnnual[r,t,f,y];
    ```
    """
    con = m["ProductionByTechnology"].sum("TIMESLICE") - m["ProductionByTechnologyAnnual"] == 0
    mask = ds["OutputActivityRatio"].sum("MODE_OF_OPERATION") != 0
    m.add_constraints(con, name="RE1_FuelProductionByTechnologyAnnual", mask=mask)

    con = (
        m["ProductionByTechnologyAnnual"] * ds["RETagTechnology"].fillna(0)
        - m["TotalREProductionAnnual"]
        == 0
    )
    mask = ds["RETagTechnology"] == 1
    m.add_constraints(con, name="RE2_TechIncluded", mask=mask)

    con = (
        m["RateOfProduction"] * ds["YearSplit"] * ds["RETagFuel"].fillna(0)
        - m["RETotalProductionOfTargetFuelAnnual"]
        == 0
    )
    mask = ds["RETagFuel"] == 1
    m.add_constraints(con, name="RE3_FuelIncluded", mask=mask)

    con = (
        m["RETotalProductionOfTargetFuelAnnual"] * ds["REMinProductionTarget"].fillna(0)
        - m["TotalREProductionAnnual"]
        <= 0
    )
    mask = ds["REMinProductionTarget"] > 0
    m.add_constraints(con, name="RE4_EnergyConstraint", mask=mask)

    con = (ds["YearSplit"] * m["RateOfUseByTechnology"]).sum("TIMESLICE") - m[
        "UseByTechnologyAnnual"
    ] == 0
    mask = ds["InputActivityRatio"].sum("MODE_OF_OPERATION") > 0
    m.add_constraints(con, name="RE5_FuelUseByTechnologyAnnual", mask=mask)

    return m
