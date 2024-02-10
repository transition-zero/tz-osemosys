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
    s.t. EQ_SpecifiedDemand{r in REGION, l in TIMESLICE, f in FUEL, y in YEAR:
        SpecifiedAnnualDemand[r,f,y] <> 0}:
    SpecifiedAnnualDemand[r,f,y] * SpecifiedDemandProfile[r,f,l,y] / YearSplit[l,y]
    =
    RateOfDemand[r,l,f,y];
    ```
    """
    mask = ds["SpecifiedAnnualDemand"].notnull()
    con = m["RateOfDemand"] == (
        ds["SpecifiedAnnualDemand"] * ds["SpecifiedDemandProfile"] / ds["YearSplit"]
    )
    m.add_constraints(con, name="EQ_SpecifiedDemand", mask=mask)
    return m
