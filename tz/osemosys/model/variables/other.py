import xarray as xr
from linopy import Model
from numpy import inf


def add_cost_variables(ds: xr.Dataset, m: Model) -> Model:
    """Add all variables to the model

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

    coords = [ds.coords["REGION"]]
    m.add_variables(
        lower=0, upper=inf, coords=coords, name="ModelPeriodCostByRegion", integer=False
    )

    return m


def add_margin_variables(ds: xr.Dataset, m: Model) -> Model:
    RY = [ds.coords["REGION"], ds.coords["YEAR"]]

    # Reserve Margin

    m.add_variables(
        lower=0, upper=inf, coords=RY, name="TotalCapacityInReserveMargin", integer=False
    )
    coords = [ds.coords["REGION"], ds.coords["TIMESLICE"], ds.coords["YEAR"]]
    m.add_variables(
        lower=0, upper=inf, coords=coords, name="DemandNeedingReserveMargin", integer=False
    )
    return m


def add_re_variables(ds: xr.Dataset, m: Model) -> Model:
    RY = [ds.coords["REGION"], ds.coords["YEAR"]]

    # RE Gen Target

    m.add_variables(lower=-inf, upper=inf, coords=RY, name="TotalREProductionAnnual", integer=False)
    m.add_variables(
        lower=-inf, upper=inf, coords=RY, name="RETotalProductionOfTargetFuelAnnual", integer=False
    )

    return m
