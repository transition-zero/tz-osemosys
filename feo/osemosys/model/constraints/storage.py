import xarray as xr
from linopy import Model


def add_storage_constraints(ds: xr.Dataset, m: Model) -> Model:
    """Add Storage constraints to the model.
    Representation of storage technologies, ensuring that storage levels, charge/discharge rates
    are maintained for each daily time bracket, day type, and season.


    Arguments
    ---------
    ds: xarray.Dataset
        The parameters dataset
    m: linopy.Model
        A linopy model

    Returns
    -------
    linopy.Model


    Notes
    -----
    ```ampl
    s.t.
    ```
    """

    return m
