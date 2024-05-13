from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_accounting_technology_constraints(
    ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]
) -> Model:
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

    # NOTE: These constraints have all been replaced by linear expressions in other constraints
    #       This file remains just for reference

    return m
