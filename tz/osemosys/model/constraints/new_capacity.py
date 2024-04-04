from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_new_capacity_constraints(
    ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]
) -> Model:
    """Add New Capacity constraints to the model.
    Constrains new capacity of a technology for each year based on user-defined lower and upper
    limits.

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
    s.t. NCC1_TotalAnnualMaxNewCapacityConstraint{
        r in REGION, t in TECHNOLOGY, y in YEAR:
        TotalAnnualMaxCapacityInvestment[r,t,y] <> -1}:
        NewCapacity[r,t,y] <=
        TotalAnnualMaxCapacityInvestment[r,t,y];
    s.t. NCC2_TotalAnnualMinNewCapacityConstraint{
        r in REGION, t in TECHNOLOGY, y in YEAR:
        TotalAnnualMinCapacityInvestment[r,t,y]>0}:
        NewCapacity[r,t,y] >=
        TotalAnnualMinCapacityInvestment[r,t,y];

    ```
    """
    con = m["NewCapacity"] <= ds["TotalAnnualMaxCapacityInvestment"]
    mask = ds["TotalAnnualMaxCapacityInvestment"] >= 0
    m.add_constraints(con, name="NCC1_TotalAnnualMaxNewCapacityConstraint", mask=mask)

    con = m["NewCapacity"] >= ds["TotalAnnualMinCapacityInvestment"]
    mask = ds["TotalAnnualMinCapacityInvestment"] > 0
    m.add_constraints(con, name="NCC2_TotalAnnualMinNewCapacityConstraint", mask=mask)
    return m
