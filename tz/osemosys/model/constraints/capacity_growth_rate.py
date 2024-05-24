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
    if (
        ds["CapacityAdditionalMaxFloor"].notnull().any()
        and ds["CapacityAdditionalMaxGrowthRate"].notnull().any()
    ):

        # pull m["OR_GrowthRateFloor"] DOWN (==0) if (GrossCapacity * GrowthRate) >= MaxFloor # NOQA E501
        con = (
            m["OR_GrowthRateFloor"]
            <= (lex["GrossCapacity"].shift(YEAR=-1) * ds["CapacityAdditionalMaxGrowthRate"])
            / ds["CapacityAdditionalMaxFloor"]
        )
        mask = (
            ds["CapacityAdditionalMaxFloor"].notnull()
            & ds["CapacityAdditionalMaxGrowthRate"].notnull()
        )
        m.add_constraints(con, name="OR_GrowthRateFloor_pull_down", mask=mask)

        # BIG M notation
        # https://or.stackexchange.com/questions/135/what-is-the-big-m-method-and-are-there-two-of-them
        # pick a large value for 'M'
        M = ds["AccumulatedAnnualDemand"].max().values * 1000

        # as m[0,1] -> 0, NewCapacity <= CapacityAdditionalMaxFloor
        # m['NewCapacity'] <= M * m['OR_GrowthRateFloor'] + ds["CapacityAdditionalMaxFloor"]
        con = m["NewCapacity"] <= M * m["OR_GrowthRateFloor"] + ds[
            "CapacityAdditionalMaxFloor"
        ].fillna(0)
        m.add_constraints(con, name="OR_GrowthRateFloor_lte_floor", mask=mask)

        # as m[0,1] -> 1, NewCapacity <= GrossCapacity * CapacityAdditionalMaxGrowthRate
        # m['NewCapacity'] <= M * (1 - m['OR_GrowthRateFloor'])
        #    + lex['GrossCapacity'].shift(YEAR=1) * ds['CapacityAdditionalMaxGrowthRate']
        con = (
            m["NewCapacity"]
            <= M * (-1 * m["OR_GrowthRateFloor"] + 1)
            + lex["GrossCapacity"].shift(YEAR=1) * ds["CapacityAdditionalMaxGrowthRate"]
        )
        m.add_constraints(con, name="OR_GrowthRateFloor_lte_growthrate", mask=mask)

    elif ds["CapacityAdditionalMaxGrowthRate"].notnull().any():
        # we just have a growth rate constraint by itself
        con = (
            m["NewCapacity"]
            <= lex["GrossCapacity"].shift(YEAR=1) * ds["CapacityAdditionalMaxGrowthRate"]
        )
        mask = ds["CapacityAdditionalMaxGrowthRate"].notnull()
        m.add_constraints(con, name="GrowthRateMax", mask=mask)

    if ds["CapacityAdditionalMinGrowthRate"].notnull().any():
        con = (
            m["NewCapacity"]
            >= lex["GrossCapacity"].shift(YEAR=1) * ds["CapacityAdditionalMinGrowthRate"]
        )
        mask = ds["CapacityAdditionalMinGrowthRate"].notnull()
        m.add_constraints(con, name="GrowthRateMin", mask=mask)

    return m
