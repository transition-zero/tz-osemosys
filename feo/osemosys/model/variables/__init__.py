import xarray as xr
from linopy import Model

from .activity import add_activity_variables
from .capacity import add_capacity_variables
from .demand import add_demand_variables
from .emissions import add_emission_variables
from .other import add_cost_variables, add_margin_variables, add_re_variables


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

    m = add_demand_variables(ds, m)
    # m = add_storage_variables(ds, m)
    m = add_capacity_variables(ds, m)
    m = add_activity_variables(ds, m)
    m = add_cost_variables(ds, m)
    m = add_re_variables(ds, m)
    m = add_margin_variables(ds, m)
    m = add_emission_variables(ds, m)

    return m
