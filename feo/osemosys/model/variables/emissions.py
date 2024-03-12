import xarray as xr
from linopy import Model
from numpy import inf


def add_emission_variables(ds: xr.Dataset, m: Model) -> Model:
    """Add emisison variables to the model

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
    # Create the required indexes
    RTeY = [ds.coords["REGION"], ds.coords["TECHNOLOGY"], ds.coords["YEAR"]]

    m.add_variables(
        lower=0, upper=inf, coords=RTeY, name="DiscountedTechnologyEmissionsPenalty", integer=False
    )

    return m
