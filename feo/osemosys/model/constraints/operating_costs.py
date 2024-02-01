import xarray as xr
from linopy import Model


def add_operating_costs_constraints(ds: xr.Dataset, m: Model, discount_factor_mid: float) -> Model:
    """Add Operating Costs constraint to the model.
    Calculates the total operating expenditure - both discounted and undiscounted - of total (new
    and existing) capacity.

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
    con = (m["TotalAnnualTechnologyActivityByMode"] * ds["VariableCost"].fillna(0)).sum(
        dims="MODE_OF_OPERATION"
    ) - m["AnnualVariableOperatingCost"] == 0
    mask = (ds["VariableCost"].sum(dim="MODE_OF_OPERATION") != 0) & (
        ~ds["VariableCost"].sum(dim="MODE_OF_OPERATION").isnull()
    )
    m.add_constraints(con, name="OC1_OperatingCostsVariable", mask=mask)

    con = (m["TotalCapacityAnnual"] * ds["FixedCost"].fillna(0)) - m[
        "AnnualFixedOperatingCost"
    ] == 0
    # mask = ~ds['FixedCost'].isnull()
    m.add_constraints(con, name="OC2_OperatingCostsFixedAnnual")

    con = m["AnnualFixedOperatingCost"] + m["AnnualVariableOperatingCost"] - m["OperatingCost"] == 0
    # mask = (ds['VariableCost'].sum(dim='MODE_OF_OPERATION') != 0) & (~ds['FixedCost'].isnull())
    m.add_constraints(con, name="OC3_OperatingCostsTotalAnnual")

    con = (m["OperatingCost"] / discount_factor_mid) - m["DiscountedOperatingCost"] == 0
    m.add_constraints(con, name="OC4_DiscountedOperatingCostsTotalAnnual")
    return m
