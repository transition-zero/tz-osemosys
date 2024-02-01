import xarray as xr
from linopy import Model


def add_capital_costs_constraints(
    ds: xr.Dataset,
    m: Model,
    capital_recovery_factor: float,
    pv_annuity: float,
    discount_factor: float,
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
    con = (
        ds["CapitalCost"].fillna(0) * m["NewCapacity"] * capital_recovery_factor * pv_annuity
        - m["CapitalInvestment"]
        == 0
    )
    m.add_constraints(con, name="CC1_UndiscountedCapitalInvestment")

    con = (m["CapitalInvestment"] / discount_factor) - m["DiscountedCapitalInvestment"] == 0
    m.add_constraints(con, name="CC2_DiscountingCapitalInvestment")
    return m
