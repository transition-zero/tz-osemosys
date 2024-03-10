import xarray as xr
from linopy import Model


def add_capital_costs_constraints(
    ds: xr.Dataset,
    m: Model,
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

    discount_factor = (1 + ds["DiscountRate"]) ** (ds.coords["YEAR"] - min(ds.coords["YEAR"]))

    pv_annuity = (
        (1 - (1 + ds["DiscountRateIdv"]) ** (-(ds["OperationalLife"])))
        * (1 + ds["DiscountRateIdv"])
        / ds["DiscountRateIdv"]
    )

    capital_recovery_factor = (1 - (1 + ds["DiscountRateIdv"]) ** (-1)) / (
        1 - (1 + ds["DiscountRateIdv"]) ** (-(ds["OperationalLife"]))
    )

    CapitalInvestment = (
        ds["CapitalCost"].fillna(0) * m["NewCapacity"] * capital_recovery_factor * pv_annuity
    )

    con = (CapitalInvestment / discount_factor) - m["DiscountedCapitalInvestment"] == 0
    m.add_constraints(con, name="CC2_DiscountingCapitalInvestment")
    return m
