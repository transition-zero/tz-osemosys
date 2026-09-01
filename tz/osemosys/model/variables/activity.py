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
        ds.indexes["REGION"],
        ds.indexes["_REGION"],
        ds.indexes["TIMESLICE"],
        ds.indexes["FUEL"],
        ds.indexes["YEAR"],
    ]
    RTeMYTi = [
        ds.indexes["REGION"],
        ds.indexes["TECHNOLOGY"],
        ds.indexes["MODE_OF_OPERATION"],
        ds.indexes["YEAR"],
        ds.indexes["TIMESLICE"],
    ]

    mask = (
        ds["InputActivityRatio"].notnull().any(dim="FUEL")
        | ds["OutputActivityRatio"].notnull().any(dim="FUEL")
        | ds["EmissionActivityRatio"].notnull().any(dim="EMISSION")
        | ds["TechnologyToStorage"].notnull().any(dim="STORAGE")
        | ds["TechnologyFromStorage"].notnull().any(dim="STORAGE")
    )
    m.add_variables(
        lower=0, upper=inf, coords=RTeMYTi, name="RateOfActivity", integer=False, mask=mask
    )

    mask = ds["TradeRoute"] == 1
    m.add_variables(lower=0, upper=inf, coords=RRTiFY, name="Export", integer=False, mask=mask)
    m.add_variables(
        lower=0,
        upper=inf,
        coords=RRTiFY,
        name="Import",
        integer=False,
        mask=mask.rename({"REGION": "_REGION", "_REGION": "REGION"}),
    )

    return m
