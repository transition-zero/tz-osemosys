import xarray as xr
from linopy import Model


def add_emissions_constraints(ds: xr.Dataset, m: Model, discount_factor_mid: float) -> Model:
    """Add Emissions constraints to the model.
    Applies (1) user-defined emission limits annually and for the entire model period,
    (2) Emission penalities, and
    (3) Calculates emissions by technology and year

    Arguments
    ---------
    ds: xarray.Dataset
        The parameters dataset
    m: linopy.Model
        A linopy model
    discount_factor_mid: float
        The discount factor for operational costs, taken from the midpoint of the year to account
        for ongoing discounting

    Returns
    -------
    linopy.Model


    Notes
    -----
    ```ampl
    s.t. E1_AnnualEmissionProductionByMode{
        r in REGION, t in TECHNOLOGY, e in EMISSION, m in MODE_OF_OPERATION, y in YEAR:
        EmissionActivityRatio[r,t,e,m,y] <> 0}:
        EmissionActivityRatio[r,t,e,m,y] * TotalAnnualTechnologyActivityByMode[r,t,m,y]
        =
        AnnualTechnologyEmissionByMode[r,t,e,m,y];

    s.t. E2_AnnualEmissionProduction{
        r in REGION, t in TECHNOLOGY, e in EMISSION, y in YEAR}:
        sum{m in MODE_OF_OPERATION}
        AnnualTechnologyEmissionByMode[r,t,e,m,y]
        =
        AnnualTechnologyEmission[r,t,e,y];

    s.t. E3_EmissionsPenaltyByTechAndEmission{
        r in REGION, t in TECHNOLOGY, e in EMISSION, y in YEAR: EmissionsPenalty[r,e,y] <> 0}:
        AnnualTechnologyEmission[r,t,e,y] * EmissionsPenalty[r,e,y]
        =
        AnnualTechnologyEmissionPenaltyByEmission[r,t,e,y];

    s.t. E4_EmissionsPenaltyByTechnology{
        r in REGION, t in TECHNOLOGY, y in YEAR}:
        sum{e in EMISSION} AnnualTechnologyEmissionPenaltyByEmission[r,t,e,y]
        =
        AnnualTechnologyEmissionsPenalty[r,t,y];

    s.t. E5_DiscountedEmissionsPenaltyByTechnology{
        r in REGION, t in TECHNOLOGY, y in YEAR}:
        AnnualTechnologyEmissionsPenalty[r,t,y] / DiscountFactorMid[r,y]
        =
        DiscountedTechnologyEmissionsPenalty[r,t,y];

    s.t. E6_EmissionsAccounting1{
        r in REGION, e in EMISSION, y in YEAR}:
        sum{t in TECHNOLOGY}
        AnnualTechnologyEmission[r,t,e,y]
        =
        AnnualEmissions[r,e,y];

    s.t. E7_EmissionsAccounting2{
        r in REGION, e in EMISSION}:
        sum{y in YEAR} AnnualEmissions[r,e,y]
        =
        ModelPeriodEmissions[r,e] - ModelPeriodExogenousEmission[r,e];

    s.t. E8_AnnualEmissionsLimit{
        r in REGION, e in EMISSION, y in YEAR: AnnualEmissionLimit[r, e, y] <> -1}:
        AnnualEmissions[r,e,y] + AnnualExogenousEmission[r,e,y]
        <=
        AnnualEmissionLimit[r,e,y];

    s.t. E9_ModelPeriodEmissionsLimit{
        r in REGION, e in EMISSION: ModelPeriodEmissionLimit[r, e] <> -1}:
        ModelPeriodEmissions[r,e]
        <=
        ModelPeriodEmissionLimit[r,e];
        ```
    """
    mask = ds["EmissionActivityRatio"].notnull()
    con = (
        ds["EmissionActivityRatio"] * m["TotalAnnualTechnologyActivityByMode"]
        - m["AnnualTechnologyEmissionByMode"]
        == 0
    )
    m.add_constraints(con, name="E1_AnnualEmissionProductionByMode", mask=mask)

    if ds["EMISSION"].size > 0:
        mask = ds["EmissionActivityRatio"].sum("MODE_OF_OPERATION") != 0
        con = (
            m["AnnualTechnologyEmissionByMode"].sum(dims="MODE_OF_OPERATION")
            - m["AnnualTechnologyEmission"]
            == 0
        )
        m.add_constraints(con, name="E2_AnnualEmissionProduction", mask=mask)

    mask = (ds["EmissionsPenalty"].notnull()) & (
        ds["EmissionActivityRatio"].sum("MODE_OF_OPERATION") != 0
    )
    con = (m["AnnualTechnologyEmission"] * ds["EmissionsPenalty"]) - m[
        "AnnualTechnologyEmissionPenaltyByEmission"
    ] == 0
    m.add_constraints(con, name="E3_EmissionsPenaltyByTechAndEmission", mask=mask)

    con = (
        m["AnnualTechnologyEmissionPenaltyByEmission"].sum("EMISSION")
        - m["AnnualTechnologyEmissionsPenalty"]
        == 0
    )
    m.add_constraints(con, name="E4_EmissionsPenaltyByTechnology")

    con = (
        m["AnnualTechnologyEmissionsPenalty"] / discount_factor_mid
        - m["DiscountedTechnologyEmissionsPenalty"]
        == 0
    )
    m.add_constraints(con, name="E5_DiscountedEmissionsPenaltyByTechnology")

    if ds["EMISSION"].size > 0:
        con = m["AnnualTechnologyEmission"].sum(dims=["TECHNOLOGY"]) - m["AnnualEmissions"] == 0
        m.add_constraints(con, name="E6_EmissionsAccounting1")

    if ds["EMISSION"].size > 0:
        con = m["ModelPeriodEmissions"] - m["AnnualEmissions"].sum("YEAR") == ds[
            "ModelPeriodExogenousEmission"
        ].fillna(0)
        m.add_constraints(con, name="E7_EmissionsAccounting2")

    if "E8_AnnualEmissionsLimit" in m.constraints:
        m.remove_constraints("E8_AnnualEmissionsLimit")

    con = m["AnnualEmissions"] <= ds["AnnualEmissionLimit"] - ds["AnnualExogenousEmission"].fillna(
        0
    )
    mask = ds["AnnualEmissionLimit"] != -1
    m.add_constraints(con, name="E8_AnnualEmissionsLimit", mask=mask)

    con = m["ModelPeriodEmissions"] <= ds["ModelPeriodEmissionLimit"]
    mask = ds["ModelPeriodEmissionLimit"] != -1
    m.add_constraints(con, name="E9_ModelPeriodEmissionsLimit", mask=mask)

    return m
