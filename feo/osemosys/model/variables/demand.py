import xarray as xr
from linopy import Model
from numpy import inf


def add_demand_variables(ds: xr.Dataset, m: Model) -> Model:
    """Add demand variables to the model

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
    RTiFY = [ds.coords["REGION"], ds.coords["TIMESLICE"], ds.coords["FUEL"], ds.coords["YEAR"]]

    # mask = ds['SpecifiedAnnualDemand'].expand_dims('TIMESLICE').notnull()
    m.add_variables(lower=0, upper=inf, coords=RTiFY, name="RateOfDemand", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RTiFY, name="Demand", integer=False)
    return m
