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

    m.add_variables(lower=0, upper=inf, coords=RSY, name="StorageLevelYearStart", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RSY, name="StorageLevelYearFinish", integer=False)
    coords = [ds.coords["REGION"], ds.coords["STORAGE"], ds.coords["SEASON"], ds.coords["YEAR"]]
    m.add_variables(
        lower=0, upper=inf, coords=coords, name="StorageLevelSeasonStart", integer=False
    )
    coords = [
        ds.coords["REGION"],
        ds.coords["STORAGE"],
        ds.coords["SEASON"],
        ds.coords["DAYTYPE"],
        ds.coords["YEAR"],
    ]
    m.add_variables(
        lower=0, upper=inf, coords=coords, name="StorageLevelDayTypeStart", integer=False
    )
    coords = [
        ds.coords["REGION"],
        ds.coords["STORAGE"],
        ds.coords["SEASON"],
        ds.coords["DAYTYPE"],
        ds.coords["YEAR"],
    ]
    m.add_variables(
        lower=0, upper=inf, coords=coords, name="StorageLevelDayTypeFinish", integer=False
    )
    m.add_variables(lower=0, upper=inf, coords=RSY, name="StorageLowerLimit", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RSY, name="StorageUpperLimit", integer=False)
    m.add_variables(
        lower=0, upper=inf, coords=RSY, name="AccumulatedNewStorageCapacity", integer=False
    )
    m.add_variables(lower=0, upper=inf, coords=RSY, name="NewStorageCapacity", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RSY, name="CapitalInvestmentStorage", integer=False)
    m.add_variables(
        lower=0, upper=inf, coords=RSY, name="DiscountedCapitalInvestmentStorage", integer=False
    )
    m.add_variables(lower=0, upper=inf, coords=RSY, name="SalvageValueStorage", integer=False)
    m.add_variables(
        lower=0, upper=inf, coords=RSY, name="DiscountedSalvageValueStorage", integer=False
    )
    m.add_variables(
        lower=0, upper=inf, coords=RSY, name="TotalDiscountedStorageCost", integer=False
    )
    return m
