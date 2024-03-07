import xarray as xr
from linopy import Model


def add_capacity_adequacy_a_constraints(ds: xr.Dataset, m: Model) -> Model:
    """Add Capacity Adequacy A constraints to the model
    Ensures that there is sufficient capacity of technologies to meet demand(s) in each timeslice.

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
    s.t. CAa1_TotalNewCapacity{
        r in REGION, t in TECHNOLOGY, y in YEAR}:
        AccumulatedNewCapacity[r,t,y]
        =
        sum{yy in YEAR: y-yy < OperationalLife[r,t] && y - yy >= 0} NewCapacity[r,t,yy];

    s.t. CAa2_TotalAnnualCapacity{
        r in REGION, t in TECHNOLOGY, y in YEAR}:
        AccumulatedNewCapacity[r,t,y] + ResidualCapacity[r,t,y]
        =
        TotalCapacityAnnual[r,t,y];

    s.t. CAa3_TotalActivityOfEachTechnology{
        r in REGION, t in TECHNOLOGY, l in TIMESLICE, y in YEAR}:
        sum{m in MODE_OF_OPERATION} RateOfActivity[r,l,t,m,y]
        =
        RateOfTotalActivity[r,t,l,y];

    s.t. CAa4_Constraint_Capacity{
        r in REGION, l in TIMESLICE, t in TECHNOLOGY, y in YEAR}:
        RateOfTotalActivity[r,t,l,y]
        <=
        TotalCapacityAnnual[r,t,y] * CapacityFactor[r,t,l,y] * CapacityToActivityUnit[r,t];

    s.t. CAa5_TotalNewCapacity{
        r in REGION, t in TECHNOLOGY, y in YEAR: CapacityOfOneTechnologyUnit[r,t,y]<>0}:
        CapacityOfOneTechnologyUnit[r,t,y] * NumberOfNewTechnologyUnits[r,t,y]
        =
        NewCapacity[r,t,y];
    ```
    """
    new_cap = m["NewCapacity"].rename(YEAR="BUILDYEAR")
    mask = (ds.YEAR - new_cap.data.BUILDYEAR >= 0) & (
        ds.YEAR - new_cap.data.BUILDYEAR < ds.OperationalLife
    )
    con = m["AccumulatedNewCapacity"] - new_cap.where(mask).sum("BUILDYEAR") == 0
    m.add_constraints(con, name="CAa1_TotalNewCapacity")

    con = m["TotalCapacityAnnual"] - m["AccumulatedNewCapacity"] == ds["ResidualCapacity"].fillna(0)
    m.add_constraints(con, name="CAa2_TotalAnnualCapacity")

    RateOfTotalActivity = m["RateOfActivity"].sum(dims="MODE_OF_OPERATION")

    con = (
        RateOfTotalActivity
        - (m["TotalCapacityAnnual"] * ds["CapacityFactor"] * ds["CapacityToActivityUnit"])
        <= 0
    )
    mask = ~ds["CapacityFactor"].isnull()
    m.add_constraints(con, name="CAa4_Constraint_Capacity", mask=mask)

    con = (
        ds["CapacityOfOneTechnologyUnit"] * m["NumberOfNewTechnologyUnits"] - m["NewCapacity"] == 0
    )
    mask = ds["CapacityOfOneTechnologyUnit"].notnull()
    m.add_constraints(con, name="CAa5_TotalNewCapacity", mask=mask)

    return m
