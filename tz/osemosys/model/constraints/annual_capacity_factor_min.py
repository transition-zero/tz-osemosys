from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_annual_capacity_factor_min_constraints(
    ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]
) -> Model:
    """Add annual capacity factor constraints to the model.
    Constrains annual activity of a technology based on
    user-defined minimum utilisation rates.

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
    s.t ACF1_TotalAnnualMinCapacityFactor{
        r in REGION, t in TECHNOLOGY, y in YEAR: TotalAnnualMinCapacityFactor[r,t,y] > 0}:
        TotalTechnologyAnnualActivity[r,t,y] >=
        (GrossCapacity[r,t,y] * AvailabilityFactor[r,t,y] * CapacityToActivityUnit[r,t])
        * TotalAnnualMinCapacityFactor[r,t,y];
    ```
    """
    con = lex["TotalTechnologyAnnualActivity"] >= ds["TotalAnnualMinCapacityFactor"] * (
        lex["GrossCapacity"] * ds["AvailabilityFactor"] * ds["CapacityToActivityUnit"]
    )

    m.add_constraints(con, name="ACF1_TotalAnnualMinCapacityFactor")

    return m
