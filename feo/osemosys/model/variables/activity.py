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
    RTiTeMY = [
        ds.coords["REGION"],
        ds.coords["TIMESLICE"],
        ds.coords["TECHNOLOGY"],
        ds.coords["MODE_OF_OPERATION"],
        ds.coords["YEAR"],
    ]

    m.add_variables(lower=0, upper=inf, coords=RTiTeMY, name="RateOfActivity", integer=False)
    coords = [
        ds.coords["REGION"],
        ds.coords["TECHNOLOGY"],
        ds.coords["TIMESLICE"],
        ds.coords["YEAR"],
    ]
    coords = [ds.coords["REGION"], ds.coords["TECHNOLOGY"]]
    m.add_variables(
        lower=0,
        upper=inf,
        coords=coords,
        name="TotalTechnologyModelPeriodActivity",
        integer=False,
    )
    m.add_variables(lower=-inf, upper=inf, coords=RRTiFY, name="Trade", integer=False)
    m.add_variables(lower=-inf, upper=inf, coords=RRFY, name="TradeAnnual", integer=False)

    return m
