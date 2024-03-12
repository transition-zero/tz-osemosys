import xarray as xr
from linopy import Model


def add_capacity_adequacy_b_constraints(ds: xr.Dataset, m: Model) -> Model:
    """Add Capacity Adequacy B constraints to the model.
    Ensures that there is sufficient capacity of technologies to meet demand(s) in each year,
    taking planned maintainence into consideration.

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
    s.t. CAb1_PlannedMaintenance{
        r in REGION, t in TECHNOLOGY, y in YEAR: AvailabilityFactor[r,t,y] < 1}:
        sum{l in TIMESLICE} RateOfTotalActivity[r,t,l,y] * YearSplit[l,y]
        <=
        sum{l in TIMESLICE} (TotalCapacityAnnual[r,t,y] * CapacityFactor[r,t,l,y] *
        YearSplit[l,y]) * AvailabilityFactor[r,t,y] * CapacityToActivityUnit[r,t];
    ```
    """
    RateOfTotalActivity = m["RateOfActivity"].sum(dims="MODE_OF_OPERATION")

    mask = ds["AvailabilityFactor"] < 1
    con = (RateOfTotalActivity * ds["YearSplit"]).sum(dims="TIMESLICE") - (
        (m["TotalCapacityAnnual"] * ds["CapacityFactor"] * ds["YearSplit"]).sum(dims="TIMESLICE")
        * ds["AvailabilityFactor"]
        * ds["CapacityToActivityUnit"]
    ) <= 0
    m.add_constraints(con, name="CAb1_PlannedMaintenance", mask=mask)

    return m
