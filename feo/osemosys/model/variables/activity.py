import xarray as xr
from linopy import Model
from numpy import inf


def add_activity_variables(ds: xr.Dataset, m: Model) -> Model:
    """Add activity variables to the model

    Arguments
    ---------
    ds: xarray.Dataset
        The parameters dataset
    m: linopy.Model
        A linopy model

    Returns
    -------
    linopy.Model
    """
    # Add indices
    RRTiFY = [
        ds.coords["REGION"],
        ds.coords["_REGION"],
        ds.coords["TIMESLICE"],
        ds.coords["FUEL"],
        ds.coords["YEAR"],
    ]
    RRFY = [ds.coords["REGION"], ds.coords["_REGION"], ds.coords["FUEL"], ds.coords["YEAR"]]
    RFY = [ds.coords["REGION"], ds.coords["FUEL"], ds.coords["YEAR"]]
    RTiFY = [ds.coords["REGION"], ds.coords["TIMESLICE"], ds.coords["FUEL"], ds.coords["YEAR"]]
    RTiTeFY = [
        ds.coords["REGION"],
        ds.coords["TIMESLICE"],
        ds.coords["TECHNOLOGY"],
        ds.coords["FUEL"],
        ds.coords["YEAR"],
    ]
    RTiTeMY = [
        ds.coords["REGION"],
        ds.coords["TIMESLICE"],
        ds.coords["TECHNOLOGY"],
        ds.coords["MODE_OF_OPERATION"],
        ds.coords["YEAR"],
    ]
    RTiTeMFY = [
        ds.coords["REGION"],
        ds.coords["TIMESLICE"],
        ds.coords["TECHNOLOGY"],
        ds.coords["MODE_OF_OPERATION"],
        ds.coords["FUEL"],
        ds.coords["YEAR"],
    ]
    RTeY = [ds.coords["REGION"], ds.coords["TECHNOLOGY"], ds.coords["YEAR"]]

    # Add masks
    iac_mask = ds["InputActivityRatio"].notnull()
    iac_mask_m = ds["InputActivityRatio"].sum("MODE_OF_OPERATION") != 0
    oac_mask = ds["OutputActivityRatio"].notnull()
    oac_mask_m = ds["OutputActivityRatio"].sum("MODE_OF_OPERATION") != 0

    m.add_variables(lower=0, upper=inf, coords=RTiTeMY, name="RateOfActivity", integer=False)
    coords = [
        ds.coords["REGION"],
        ds.coords["TECHNOLOGY"],
        ds.coords["TIMESLICE"],
        ds.coords["YEAR"],
    ]
    m.add_variables(lower=0, upper=inf, coords=coords, name="RateOfTotalActivity", integer=False)
    m.add_variables(
        lower=0, upper=inf, coords=RTeY, name="TotalTechnologyAnnualActivity", integer=False
    )
    coords = [
        ds.coords["REGION"],
        ds.coords["TECHNOLOGY"],
        ds.coords["MODE_OF_OPERATION"],
        ds.coords["YEAR"],
    ]
    m.add_variables(
        lower=0, upper=inf, coords=coords, name="TotalAnnualTechnologyActivityByMode", integer=False
    )
    coords = [ds.coords["REGION"], ds.coords["TECHNOLOGY"]]
    m.add_variables(
        lower=-inf,
        upper=inf,
        coords=coords,
        name="TotalTechnologyModelPeriodActivity",
        integer=False,
    )
    m.add_variables(
        lower=0,
        upper=inf,
        coords=RTiTeMFY,
        name="RateOfProductionByTechnologyByMode",
        integer=False,
        mask=oac_mask,
    )
    m.add_variables(
        lower=0,
        upper=inf,
        coords=RTiTeFY,
        name="RateOfProductionByTechnology",
        integer=False,
        mask=oac_mask_m,
    )
    m.add_variables(
        lower=0,
        upper=inf,
        coords=RTiTeFY,
        name="ProductionByTechnology",
        integer=False,
        mask=oac_mask_m,
    )
    coords = [ds.coords["REGION"], ds.coords["TECHNOLOGY"], ds.coords["FUEL"], ds.coords["YEAR"]]
    m.add_variables(
        lower=0,
        upper=inf,
        coords=coords,
        name="ProductionByTechnologyAnnual",
        integer=False,
        mask=oac_mask_m,
    )
    m.add_variables(lower=0, upper=inf, coords=RTiFY, name="RateOfProduction", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RTiFY, name="Production", integer=False)
    m.add_variables(
        lower=0,
        upper=inf,
        coords=RTiTeMFY,
        name="RateOfUseByTechnologyByMode",
        integer=False,
        mask=iac_mask,
    )
    m.add_variables(
        lower=0,
        upper=inf,
        coords=RTiTeFY,
        name="RateOfUseByTechnology",
        integer=False,
        mask=iac_mask_m,
    )
    coords = [ds.coords["REGION"], ds.coords["TECHNOLOGY"], ds.coords["FUEL"], ds.coords["YEAR"]]
    m.add_variables(
        lower=0,
        upper=inf,
        coords=coords,
        name="UseByTechnologyAnnual",
        integer=False,
        mask=iac_mask_m,
    )
    m.add_variables(lower=0, upper=inf, coords=RTiFY, name="RateOfUse", integer=False)
    m.add_variables(
        lower=0, upper=inf, coords=RTiTeFY, name="UseByTechnology", integer=False, mask=iac_mask_m
    )
    m.add_variables(lower=0, upper=inf, coords=RTiFY, name="Use", integer=False)
    m.add_variables(lower=-inf, upper=inf, coords=RRTiFY, name="Trade", integer=False)
    m.add_variables(lower=-inf, upper=inf, coords=RRFY, name="TradeAnnual", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RFY, name="ProductionAnnual", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RFY, name="UseAnnual", integer=False)

    return m
