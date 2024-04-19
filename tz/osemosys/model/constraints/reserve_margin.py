from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_reserve_margin_constraints(
    ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]
) -> Model:
    """Add Reserve Margin constraints to the model.
    Ensures that adequate additional capacity, i.e. reserve margin, is available for relevant
    technologies.

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
    s.t. RM1_ReserveMargin_TechnologiesIncluded_In_Activity_Units{
        r in REGION, l in TIMESLICE, y in YEAR: ReserveMargin[r,y] > 0}:
        sum {t in TECHNOLOGY}
        TotalCapacityAnnual[r,t,y] * ReserveMarginTagTechnology[r,t,y] * CapacityToActivityUnit[r,t]
        =
        TotalCapacityInReserveMargin[r,y];

    s.t. RM2_ReserveMargin_FuelsIncluded{
        r in REGION, l in TIMESLICE, y in YEAR: ReserveMargin[r,y] > 0}:
        sum {f in FUEL}
        RateOfProduction[r,l,f,y] * ReserveMarginTagFuel[r,f,y]
        =
        DemandNeedingReserveMargin[r,l,y];

    s.t. RM3_ReserveMargin_Constraint{
        r in REGION, l in TIMESLICE, y in YEAR: ReserveMargin[r,y] > 0}:
        DemandNeedingReserveMargin[r,l,y] * ReserveMargin[r,y]
        <=
        TotalCapacityInReserveMargin[r,y];
    ```
    """

    con = (
        ds["ReserveMargin"] * lex["DemandNeedingReserveMargin"]
        - lex["TotalCapacityInReserveMargin"]
        <= 0
    )
    m.add_constraints(con, name="RM3_ReserveMargin_Constraint")

    return m
