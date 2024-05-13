from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_re_targets_constraints(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]) -> Model:
    """Add Renewable Energy target constraints to the model.
    Sets user-defined renewable energy constraints for specific years and technologies.

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

    # TODO

    return m
