from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_capacity_adequacy_b_constraints(
    ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]
) -> Model:
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

    mask = ds["AvailabilityFactor"] < 1
    con = (lex["RateOfTotalActivity"] * ds["YearSplit"]).sum(dims="TIMESLICE") - (
        (
            lex["GrossCapacity"].assign_coords(
                {"TIMESLICE": ds["CapacityFactor"].coords["TIMESLICE"]}
            )
            * ds["CapacityFactor"]
            * ds["YearSplit"]
        ).sum(dims="TIMESLICE")
        * ds["AvailabilityFactor"]
        * ds["CapacityToActivityUnit"]
    ) <= 0
    m.add_constraints(con, name="CAb1_PlannedMaintenance", mask=mask)

    return m
