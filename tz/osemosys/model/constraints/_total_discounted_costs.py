from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_total_discounted_costs_constraints(
    ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]
) -> Model:
    """Add Total Discounted Costs constraints to the model.
    Calculates the total discounted costs of the entire system across the entire model period.

    Arguments
    ---------
    ds: xarray.Dataset
        The parameters dataset
    m: linopy.Model
        A linopy model
    lex: Dict[str, LinearExpression]


    Returns
    -------
    linopy.Model


    Notes
    -----
    ```ampl
    s.t. TDC1_TotalDiscountedCostByTechnology{
        r in REGION, t in TECHNOLOGY, y in YEAR}:
        DiscountedOperatingCost[r,t,y] +
        DiscountedCapitalInvestment[r,t,y]
        + DiscountedTechnologyEmissionsPenalty[r,t,y] -
        DiscountedSalvageValue[r,t,y] = TotalDiscountedCostByTechnology[r,t,y];

    s.t. TDC2_TotalDiscountedCost{
        r in REGION, y in YEAR}:
        sum{t in TECHNOLOGY} TotalDiscountedCostByTechnology[r,t,y] +
        sum{s in STORAGE} TotalDiscountedStorageCost[r,s,y]
        = TotalDiscountedCost[r,y];
    ```
    """

    # NOTE: These constraints have all been replaced by linear expressions in other constraints
    #       This file remains just for reference

    return m
