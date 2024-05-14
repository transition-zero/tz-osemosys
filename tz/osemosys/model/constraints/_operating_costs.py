from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_operating_costs_constraints(
    ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]
) -> Model:
    """Add Operating Costs constraint to the model.
    Calculates the total operating expenditure - both discounted and undiscounted - of total (new
    and existing) capacity.

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
    s.t. OC1_OperatingCostsVariable{
        r in REGION, t in TECHNOLOGY, y in YEAR:
        sum{m in MODE_OF_OPERATION} VariableCost[r,t,m,y] <> 0}:
        sum{m in MODE_OF_OPERATION}
        TotalAnnualTechnologyActivityByMode[r,t,m,y] * VariableCost[r,t,m,y]
        =
        AnnualVariableOperatingCost[r,t,y];

    s.t. OC2_OperatingCostsFixedAnnual{
        r in REGION, t in TECHNOLOGY, y in YEAR}:
        TotalCapacityAnnual[r,t,y]*FixedCost[r,t,y]
        =
        AnnualFixedOperatingCost[r,t,y];

    s.t. OC3_OperatingCostsTotalAnnual{
        r in REGION, t in TECHNOLOGY, y in YEAR}:
        AnnualFixedOperatingCost[r,t,y] + AnnualVariableOperatingCost[r,t,y]
        =
        OperatingCost[r,t,y];

    s.t. OC4_DiscountedOperatingCostsTotalAnnual{
        r in REGION, t in TECHNOLOGY, y in YEAR}:
        OperatingCost[r,t,y] / DiscountFactorMid[r, y]
        =
        DiscountedOperatingCost[r,t,y];
    ```
    """

    # NOTE: These constraints have all been replaced by linear expressions in other constraints
    #       This file remains just for reference

    return m
