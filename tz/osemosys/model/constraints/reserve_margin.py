import xarray as xr
from linopy import Model


def add_reserve_margin_constraints(ds: xr.Dataset, m: Model) -> Model:
    """Add Reserve Margin constraints to the model.
    Ensures that adequate additional capacity, i.e. reserve margin, is available for relevant
    technologies.

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
    TotalCapacityInReserveMargin = (
        ds["ReserveMarginTagTechnology"] * ds["CapacityToActivityUnit"] * m["TotalCapacityAnnual"]
    ).where((ds["ReserveMargin"] > 0) & (ds["ReserveMarginTagTechnology"] == 1))

    # Production
    RateOfProductionByTechnologyByMode = m["RateOfActivity"] * ds["OutputActivityRatio"].where(
        (ds["OutputActivityRatio"].notnull())
        & (ds["ReserveMargin"] > 0)
        & (ds["ReserveMarginTagFuel"] == 1)
        & (ds["ReserveMarginTagTechnology"] == 1)
    )
    RateOfProductionByTechnology = RateOfProductionByTechnologyByMode.where(
        (ds["OutputActivityRatio"].notnull())
        & (ds["ReserveMargin"] > 0)
        & (ds["ReserveMarginTagFuel"] == 1)
        & (ds["ReserveMarginTagTechnology"] == 1)
    ).sum(dims="MODE_OF_OPERATION")

    RateOfProduction = RateOfProductionByTechnology.where(
        (ds["OutputActivityRatio"].notnull())
        & (ds["ReserveMargin"] > 0)
        & (ds["ReserveMarginTagFuel"] == 1)
        & (ds["ReserveMarginTagTechnology"] == 1)
    ).sum(dims="TECHNOLOGY")

    DemandNeedingReserveMargin = (RateOfProduction * ds["ReserveMarginTagFuel"]).where(
        (ds["ReserveMargin"] > 0) & (ds["ReserveMarginTagFuel"] == 1)
    )

    con = (ds["ReserveMargin"] * DemandNeedingReserveMargin - TotalCapacityInReserveMargin) <= 0
    mask = (
        (ds["ReserveMargin"] > 0)
        & (ds["ReserveMarginTagFuel"] == 1)
        & (ds["ReserveMarginTagTechnology"] == 1)
    )

    m.add_constraints(con, name="RM3_ReserveMargin_Constraint", mask=mask)

    return m
