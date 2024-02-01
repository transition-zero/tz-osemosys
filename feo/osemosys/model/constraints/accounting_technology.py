import xarray as xr
from linopy import Model


def add_accounting_technology_constraints(ds: xr.Dataset, m: Model) -> Model:
    """Add accounting_technology constraints to the model.
    Creates intermediate results variables that are not strictly needed for the optimisation but
    are useful when analysing results. E.g. 'ProductionByTechnology' and 'UseByTechnology'.

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
    s.t. Acc1_FuelProductionByTechnology{
        r in REGION, l in TIMESLICE, t in TECHNOLOGY, f in FUEL, y in YEAR}:
        RateOfProductionByTechnology[r,l,t,f,y] * YearSplit[l,y]
        =
        ProductionByTechnology[r,l,t,f,y];

    s.t. Acc2_FuelUseByTechnology{
        r in REGION, l in TIMESLICE, t in TECHNOLOGY, f in FUEL, y in YEAR}:
        RateOfUseByTechnology[r,l,t,f,y] * YearSplit[l,y]
        =
        UseByTechnology[r,l,t,f,y];

    s.t. Acc3_AverageAnnualRateOfActivity{
        r in REGION, t in TECHNOLOGY, m in MODE_OF_OPERATION, y in YEAR}:
        sum{l in TIMESLICE} RateOfActivity[r,l,t,m,y]*YearSplit[l,y]
        =
        TotalAnnualTechnologyActivityByMode[r,t,m,y];

    s.t. Acc4_ModelPeriodCostByRegion{
        r in REGION}:
        sum{y in YEAR}TotalDiscountedCost[r,y] = ModelPeriodCostByRegion[r];
    ```
    """
    con = (m["RateOfProductionByTechnology"] * ds["YearSplit"]) - m["ProductionByTechnology"] == 0
    mask = ds["OutputActivityRatio"].sum("MODE_OF_OPERATION") != 0
    m.add_constraints(con, name="Acc1_FuelProductionByTechnology", mask=mask)

    con = (m["RateOfUseByTechnology"] * ds["YearSplit"]) - m["UseByTechnology"] == 0
    mask = ds["InputActivityRatio"].sum("MODE_OF_OPERATION") != 0
    m.add_constraints(con, name="Acc2_FuelUseByTechnology", mask=mask)

    con = (m["RateOfActivity"] * ds["YearSplit"]).sum("TIMESLICE") - m[
        "TotalAnnualTechnologyActivityByMode"
    ] == 0
    m.add_constraints(con, name="Acc3_AverageAnnualRateOfActivity")

    con = m["TotalDiscountedCost"].sum("YEAR") - m["ModelPeriodCostByRegion"] == 0
    m.add_constraints(con, name="Acc4_ModelPeriodCostByRegion")
    return m
