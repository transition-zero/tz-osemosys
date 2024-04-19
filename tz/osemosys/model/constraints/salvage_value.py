from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_salvage_value_constraints(
    ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]
) -> Model:
    """Add Salvage Value constraints to the model.
    Calculates the value of a technology if it's retired before the end of its operational life.

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
    s.t. SV1_SalvageValueAtEndOfPeriod1{
        r in REGION, t in TECHNOLOGY, y in YEAR:
        DepreciationMethod[r]=1 &&
        (y + OperationalLife[r,t]-1) > (max{yy in YEAR} max(yy)) &&
        DiscountRate[r]>0}:
        SalvageValue[r,t,y]
        =
        CapitalCost[r,t,y] * NewCapacity[r,t,y] * CapitalRecoveryFactor[r,t] * PvAnnuity[r,t] *
        (1-(((1+DiscountRate[r])^(max{yy in YEAR} max(yy) - y+1)-1)/
        ((1+DiscountRate[r])^OperationalLife[r,t]-1)));

    s.t. SV2_SalvageValueAtEndOfPeriod2{
        r in REGION, t in TECHNOLOGY, y in YEAR:
        (DepreciationMethod[r]=1 &&
        (y + OperationalLife[r,t]-1) > (max{yy in YEAR} max(yy)) &&
        DiscountRate[r]=0)
        || (DepreciationMethod[r]=2 &&
        (y + OperationalLife[r,t]-1) > (max{yy in YEAR} max(yy)))}:
        SalvageValue[r,t,y] =
        CapitalCost[r,t,y] * NewCapacity[r,t,y] * CapitalRecoveryFactor[r,t] * PvAnnuity[r,t] *
        (1-(max{yy in YEAR} max(yy) - y+1)/OperationalLife[r,t]);

    s.t. SV3_SalvageValueAtEndOfPeriod3{
        r in REGION, t in TECHNOLOGY, y in YEAR:
        (y + OperationalLife[r,t]-1) <= (max{yy in YEAR} max(yy))}:
        SalvageValue[r,t,y] = 0;

    s.t. SV4_SalvageValueDiscountedToStartYear{
        r in REGION, t in TECHNOLOGY, y in YEAR}:
        DiscountedSalvageValue[r,t,y] = SalvageValue[r,t,y]/
        ((1+DiscountRate[r])^(1+max{yy in YEAR} max(yy)-min{yy in YEAR} min(yy)));
    ```
    """

    con = m["SalvageValue"] - (m["NewCapacity"] * lex["SV1Cost"]) == 0
    mask = (
        (ds["DepreciationMethod"] == 1)
        & ((ds.coords["YEAR"] + ds["OperationalLife"] - 1) > max(ds.coords["YEAR"]))
        & (ds["DiscountRateIdv"] > 0)
    )
    m.add_constraints(con, name="SV1_SalvageValueAtEndOfPeriod1", mask=mask)

    con = m["SalvageValue"] - (m["NewCapacity"] * lex["SV2Cost"]) == 0
    mask = (
        (ds["DepreciationMethod"] == 1)
        & ((ds.coords["YEAR"] + ds["OperationalLife"] - 1) > max(ds.coords["YEAR"]))
        & (ds["DiscountRateIdv"] == 0)
    ) | (
        (ds["DepreciationMethod"] == 2)
        & ((ds.coords["YEAR"] + ds["OperationalLife"] - 1) > max(ds.coords["YEAR"]))
    )
    m.add_constraints(con, name="SV2_SalvageValueAtEndOfPeriod2", mask=mask)

    con = m["SalvageValue"] == 0
    mask = (ds.coords["YEAR"] + ds["OperationalLife"] - 1) <= max(ds.coords["YEAR"])
    m.add_constraints(con, name="SV3_SalvageValueAtEndOfPeriod3", mask=mask)

    con = m["DiscountedSalvageValue"] - m["SalvageValue"] / lex["DiscountFactorSalvage"] == 0
    m.add_constraints(con, name="SV4_SalvageValueDiscountedToStartYear")

    return m
