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
    RTeMYTi = [
        ds.coords["REGION"],
        ds.coords["TECHNOLOGY"],
        ds.coords["MODE_OF_OPERATION"],
        ds.coords["YEAR"],
        ds.coords["TIMESLICE"],
    ]

    m.add_variables(lower=0, upper=inf, coords=RTeMYTi, name="RateOfActivity", integer=False)

    m.add_variables(lower=0, upper=inf, coords=RRTiFY, name="Export", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RRTiFY, name="Import", integer=False)

    return m
