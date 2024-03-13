import xarray as xr
from linopy import Model


def add_total_discounted_costs_constraints(ds: xr.Dataset, m: Model) -> Model:
    """Add Total Discounted Costs constraints to the model.
    Calculates the total discounted costs of the entire system across the entire model period.

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
    con = (
        m["DiscountedOperatingCost"]
        + m["DiscountedCapitalInvestment"]
        + m["DiscountedTechnologyEmissionsPenalty"]
        - m["DiscountedSalvageValue"]
        - m["TotalDiscountedCostByTechnology"]
        == 0
    )
    m.add_constraints(con, name="TDC1_TotalDiscountedCostByTechnology")

    try:
        con = (
            m["TotalDiscountedCostByTechnology"].sum("TECHNOLOGY")
            + m["TotalDiscountedStorageCost"].sum("STORAGE")
            - m["TotalDiscountedCost"]
            == 0
        )
    except KeyError:
        con = m["TotalDiscountedCostByTechnology"].sum("TECHNOLOGY") - m["TotalDiscountedCost"] == 0
    finally:
        m.add_constraints(con, name="TDC2_TotalDiscountedCost")

    return m
