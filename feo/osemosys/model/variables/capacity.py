import xarray as xr
from linopy import Model
from numpy import inf


def add_capacity_variables(ds: xr.Dataset, m: Model) -> Model:
    """Add capacity variables to the model

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
    # Create the required index
    RTeY = [ds.coords["REGION"], ds.coords["TECHNOLOGY"], ds.coords["YEAR"]]

    # masks
    mask = ds["CapacityOfOneTechnologyUnit"].notnull()

    m.add_variables(
        lower=0, upper=inf, coords=RTeY, name="NumberOfNewTechnologyUnits", integer=True, mask=mask
    )
    m.add_variables(lower=0, upper=inf, coords=RTeY, name="NewCapacity", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RTeY, name="AccumulatedNewCapacity", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RTeY, name="TotalCapacityAnnual", integer=False)
    return m
