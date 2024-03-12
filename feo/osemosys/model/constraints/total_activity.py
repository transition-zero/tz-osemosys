import xarray as xr
from linopy import Model


def add_total_activity_constraints(ds: xr.Dataset, m: Model) -> Model:
    """Add Total Activity constraints to the model.
    Constrains model period activity of a technology based on user-defined lower and upper limits.

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
    s.t. TAC1_TotalModelHorizonTechnologyActivity{
        r in REGION, t in TECHNOLOGY}:
        sum{y in YEAR} TotalTechnologyAnnualActivity[r,t,y] =
        TotalTechnologyModelPeriodActivity[r,t];

    s.t. TAC2_TotalModelHorizonTechnologyActivityUpperLimit{
        r in REGION, t in TECHNOLOGY:
        TotalTechnologyModelPeriodActivityUpperLimit[r,t]<>-1}:
        TotalTechnologyModelPeriodActivity[r,t] <=
        TotalTechnologyModelPeriodActivityUpperLimit[r,t] ;

    s.t. TAC3_TotalModelHorizenTechnologyActivityLowerLimit{
        r in REGION, t in TECHNOLOGY:
        TotalTechnologyModelPeriodActivityLowerLimit[r,t]>0}:
        TotalTechnologyModelPeriodActivity[r,t] >=
        TotalTechnologyModelPeriodActivityLowerLimit[r,t] ;
    ```
    """
    RateOfTotalActivity = m["RateOfActivity"].sum(dims="MODE_OF_OPERATION")
    TotalTechnologyAnnualActivity = (RateOfTotalActivity * ds["YearSplit"]).sum("TIMESLICE")
    TotalTechnologyModelPeriodActivity = TotalTechnologyAnnualActivity.sum(dims="YEAR")

    con = TotalTechnologyModelPeriodActivity <= ds["TotalTechnologyModelPeriodActivityUpperLimit"]
    mask = ds["TotalTechnologyModelPeriodActivityUpperLimit"] >= 0
    m.add_constraints(con, name="TAC2_TotalModelHorizonTechnologyActivityUpperLimit", mask=mask)

    con = TotalTechnologyModelPeriodActivity >= ds["TotalTechnologyModelPeriodActivityLowerLimit"]
    mask = ds["TotalTechnologyModelPeriodActivityLowerLimit"] > 0
    m.add_constraints(con, name="TAC3_TotalModelHorizenTechnologyActivityLowerLimit", mask=mask)

    return m
