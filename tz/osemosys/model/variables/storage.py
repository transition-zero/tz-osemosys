import xarray as xr
from linopy import Model
from numpy import inf


def add_storage_variables(ds: xr.Dataset, m: Model) -> Model:
    """Add storage variables to the model

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
    RSY = [ds.coords["REGION"], ds.coords["STORAGE"], ds.coords["YEAR"]]

    m.add_variables(lower=0, upper=inf, coords=RSY, name="NewStorageCapacity", integer=False)
    return m
