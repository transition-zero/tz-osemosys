import xarray as xr
from linopy import Model


def add_total_capacity_constraints(ds: xr.Dataset, m: Model) -> Model:
    """Add Total Capacity constraints to the model.
    Constrains capacity (new and existing) of a technology based on user-defined lower and upper
    limits.

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
    s.t. TCC1_TotalAnnualMaxCapacityConstraint{
        r in REGION, t in TECHNOLOGY, y in YEAR:
        TotalAnnualMaxCapacity[r,t,y] <> -1}:
        TotalCapacityAnnual[r,t,y] <= TotalAnnualMaxCapacity[r,t,y];

    s.t. TCC2_TotalAnnualMinCapacityConstraint{
        r in REGION, t in TECHNOLOGY, y in YEAR:
        TotalAnnualMinCapacity[r,t,y]>0}:
        TotalCapacityAnnual[r,t,y] >= TotalAnnualMinCapacity[r,t,y];
    ```
    """

    con = m["TotalCapacityAnnual"] <= ds["TotalAnnualMaxCapacity"]
    mask = ds["TotalAnnualMaxCapacity"] >= 0
    m.add_constraints(con, name="TCC1_TotalAnnualMaxCapacityConstraint", mask=mask)

    con = m["TotalCapacityAnnual"] >= ds["TotalAnnualMinCapacity"]
    mask = ds["TotalAnnualMinCapacity"] > 0
    m.add_constraints(con, name="TCC2_TotalAnnualMinCapacityConstraint", mask=mask)
    return m
