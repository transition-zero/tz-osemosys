from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_annual_activity_constraints(
    ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]
) -> Model:
    """Add Annual Activity constraints to the model.
    Constrains annual activity of a technology based on user-defined lower and upper limits.

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
    s.t. AAC1_TotalAnnualTechnologyActivity{
        r in REGION, t in TECHNOLOGY, y in YEAR}:
        sum{l in TIMESLICE} RateOfTotalActivity[r,t,l,y]*YearSplit[l,y] =
        TotalTechnologyAnnualActivity[r,t,y];

    s.t. AAC2_TotalAnnualTechnologyActivityUpperLimit{
        r in REGION, t in TECHNOLOGY, y in YEAR:
        TotalTechnologyAnnualActivityUpperLimit[r,t,y] <> -1}:
        TotalTechnologyAnnualActivity[r,t,y] <= TotalTechnologyAnnualActivityUpperLimit[r,t,y] ;

    s.t. AAC3_TotalAnnualTechnologyActivityLowerLimit{
        r in REGION, t in TECHNOLOGY, y in YEAR:
        TotalTechnologyAnnualActivityLowerLimit[r,t,y]>0}:
        TotalTechnologyAnnualActivity[r,t,y] >= TotalTechnologyAnnualActivityLowerLimit[r,t,y] ;
    ```
    """

    con = lex["TotalTechnologyAnnualActivity"] <= ds["TotalTechnologyAnnualActivityUpperLimit"]
    mask = ds["TotalTechnologyAnnualActivityUpperLimit"] >= 0
    m.add_constraints(con, name="AAC2_TotalAnnualTechnologyActivityUpperLimit", mask=mask)

    con = lex["TotalTechnologyAnnualActivity"] >= ds["TotalTechnologyAnnualActivityLowerLimit"]
    mask = ds["TotalTechnologyAnnualActivityLowerLimit"] > 0
    m.add_constraints(con, name="AAC3_TotalAnnualTechnologyActivityLowerLimit", mask=mask)
    return m
