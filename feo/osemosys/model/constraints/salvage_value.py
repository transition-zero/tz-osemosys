import xarray as xr
from linopy import Model


def add_salvage_value_constraints(ds: xr.Dataset, m: Model) -> Model:
    """Add Salvage Value constraints to the model.
    Calculates the value of a technology if it's retired before the end of its operational life.

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

    def numerator_sv1(y: int):
        return (1 + ds["DiscountRateIdv"]) ** (max(ds.coords["YEAR"]) - y + 1) - 1

    def denominator_sv1():
        return (1 + ds["DiscountRateIdv"]) ** ds["OperationalLife"] - 1

    def salvage_cost_sv1(ds):
        return ds["CapitalCost"].fillna(0) * (
            1 - (numerator_sv1(ds.coords["YEAR"]) / denominator_sv1())
        )

    con = m["SalvageValue"] - (m["NewCapacity"] * salvage_cost_sv1(ds)) == 0
    mask = (
        (ds["DepreciationMethod"] == 1)
        & ((ds.coords["YEAR"] + ds["OperationalLife"] - 1) > max(ds.coords["YEAR"]))
        & (ds["DiscountRateIdv"] > 0)
    )
    m.add_constraints(con, name="SV1_SalvageValueAtEndOfPeriod1", mask=mask)

    def numerator_sv2(y: int):
        return max(ds.coords["YEAR"]) - y + 1

    def denominator_sv2():
        return ds["OperationalLife"]

    def salvage_cost_sv2(ds):
        return ds["CapitalCost"].fillna(0) * (
            1 - (numerator_sv2(ds.coords["YEAR"]) / denominator_sv2())
        )

    con = m["SalvageValue"] - (m["NewCapacity"] * salvage_cost_sv2(ds)) == 0
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

    def discounting(ds):
        return (1 + ds["DiscountRateIdv"]) ** (1 + max(ds.coords["YEAR"]) - min(ds.coords["YEAR"]))

    con = m["DiscountedSalvageValue"] - m["SalvageValue"] / discounting(ds) == 0
    m.add_constraints(con, name="SV4_SalvageValueDiscountedToStartYear")

    return m
