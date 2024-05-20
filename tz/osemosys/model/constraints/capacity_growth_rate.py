from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_capacity_growthrate_constraints(
    ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]
) -> Model:
    """Add Annual Activity constraints to the model.
    Constrains annual activity of a technology based on user-defined lower and upper limits.

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
    s.t. AAC1_TotalAnnualTechnologyActivity{
        r in REGION, t in TECHNOLOGY, y in YEAR}:
        sum{l in TIMESLICE} RateOfTotalActivity[r,t,l,y]*YearSplit[l,y] =
        TotalTechnologyAnnualActivity[r,t,y];

    s.t. AAC2_TotalAnnualTechnologyActivityUpperLimit{
        r in REGION, t in TECHNOLOGY, y in YEAR:
        TotalTechnologyAnnualActivityUpperLimit[r,t,y] <> -1}:
        TotalTechnologyAnnualActivity[r,t,y] <= TotalTechnologyAnnualActivityUpperLimit[r,t,y] ;

    s.t. AAC3_TotalAnnualTechnologyActivityLowerLimit{
        r in REGION, t in TECHNOLOGY, y in YEAR:
        TotalTechnologyAnnualActivityLowerLimit[r,t,y]>0}:
        TotalTechnologyAnnualActivity[r,t,y] >= TotalTechnologyAnnualActivityLowerLimit[r,t,y] ;
    ```
    """
    if ("CapacityAdditionalMaxFloor" in ds.data_vars) and (
        "CapacityAdditionalMaxGrowthRate" in ds.data_vars
    ):
        # pull m["OR_CapacityAdditionalFloor_OR_GR"] DOWN (==0) if (GrossCapacity * GrowthRate) >= MaxFloor # NOQA E501
        # if (GrossCapacity * GrowthRate) < MaxFloor, then m["OR_CapacityAdditionalFloor_OR_GR"] -> 0 # NOQA E501
        con = (
            m["OR_CapacityAdditionalFloor_OR_GR"]
            <= (lex["GrossCapacity"].shift(YEAR=-1) * ds["CapacityAdditionalMaxGrowthRate"])
            / ds["CapacityAdditionalMaxFloor"]
        )
        m.add_constraints(con, name="CapAdditionalMaxFloor")

        # pull m["OR_CapacityAdditionalFloor_OR_GR"] UP (==1) if NewCapacity.shift(YEAR=-1) < MaxFloor # NOQA E501
        # If both MaxFloor and MaxGrowthRate are defined, then pick the min of either of them using Big M notation # NOQA E501
        con = (
            m["NewCapacity"]
            <= (1 - m["OR_CapacityAdditionalFloor_OR_GR"]) * ds["CapacityAdditionalMaxFloor"]
            + m["OR_CapacityAdditionalFloor_OR_GR"]
            * lex["GrossCapacity"].shift(YEAR=-1)
            * ds["CapacityAdditionalMaxGrowthRate"]
        )
        m.add_constraints(con, name="AAC1_MinStorageCharge", mask=ds["MinStorageCharge"] > 0)

    return m
