from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_capital_costs_constraints(
    ds: xr.Dataset,
    m: Model,
    lex: Dict[str, LinearExpression],
) -> Model:
    """Add Capital Costs constraint to the model.
    Calculates the total capital expenditure - both discounted and undiscounted - of new technology
    capacity.

    Arguments
    ---------
    ds: xarray.Dataset
        The parameters dataset
    m: linopy.Model
        A linopy model
    capital_recovery_factor: float
        Capital Recovery Factor
    pv_annuity: float
        PV Annuity
    discount_factor: float
        Discount factor

    Returns
    -------
    linopy.Model


    Notes
    -----
    ```ampl
    s.t. CC1_UndiscountedCapitalInvestment{
        r in REGION, t in TECHNOLOGY, y in YEAR}:
        CapitalCost[r,t,y] * NewCapacity[r,t,y] * CapitalRecoveryFactor[r,t] * PvAnnuity[r,t]
        =
        CapitalInvestment[r,t,y];

    s.t. CC2_DiscountingCapitalInvestment{
        r in REGION, t in TECHNOLOGY, y in YEAR}:
        CapitalInvestment[r,t,y]  / DiscountFactor[r,y] = DiscountedCapitalInvestment[r,t,y];
    ```
    """

    # NOTE: These constraints have all been replaced by linear expressions in other constraints
    #       This file remains just for reference

    return m
