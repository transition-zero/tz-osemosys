import xarray as xr
from linopy import Model


def add_operating_costs_constraints(ds: xr.Dataset, m: Model) -> Model:
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

    discount_factor_mid = (1 + ds["DiscountRate"]) ** (
        ds.coords["YEAR"] - min(ds.coords["YEAR"]) + 0.5
    )

    TotalAnnualTechnologyActivityByMode = (m["RateOfActivity"] * ds["YearSplit"]).sum("TIMESLICE")
    AnnualVariableOperatingCost = (
        (TotalAnnualTechnologyActivityByMode * ds["VariableCost"].fillna(0))
        .sum(dims="MODE_OF_OPERATION")
        .where(
            (ds["VariableCost"].sum(dim="MODE_OF_OPERATION") != 0)
            & (~ds["VariableCost"].sum(dim="MODE_OF_OPERATION").isnull())
        )
    )
    AnnualFixedOperatingCost = m["TotalCapacityAnnual"] * ds["FixedCost"].fillna(0)
    OperatingCost = AnnualVariableOperatingCost + AnnualFixedOperatingCost

    con = (OperatingCost / discount_factor_mid) - m["DiscountedOperatingCost"] == 0
    m.add_constraints(con, name="OC4_DiscountedOperatingCostsTotalAnnual")
    return m
