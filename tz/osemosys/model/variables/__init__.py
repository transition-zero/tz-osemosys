import xarray as xr
from linopy import Model

from .activity import add_activity_variables
from .capacity import add_capacity_variables
from .storage import add_storage_variables


def add_variables(ds: xr.Dataset, m: Model) -> Model:
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

    m = add_storage_variables(ds, m)
    m = add_capacity_variables(ds, m)
    m = add_activity_variables(ds, m)

    return m
