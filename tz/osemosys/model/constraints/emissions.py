from typing import Any

import xarray as xr
from linopy import LinearExpression, Model
from linopy.common import as_dataarray


def passthrough_mul(expr: LinearExpression, other: Any):
    # Linopy has a hard check on the dimensions of the multiplier,
    # and doesn't allow casting up dimensions
    multiplier = as_dataarray(other, coords=expr.coords, dims=expr.coord_dims)
    coeffs = expr.coeffs * multiplier
    # assert set(coeffs.shape) == set(expr.coeffs.shape)
    const = expr.const * multiplier
    return expr.assign(coeffs=coeffs, const=const)


def add_emissions_constraints(ds: xr.Dataset, m: Model) -> Model:
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

    discount_factor_mid = (1 + ds["DiscountRate"]) ** (
        ds.coords["YEAR"] - min(ds.coords["YEAR"]) + 0.5
    )

    if ds["EMISSION"].size > 0:
        TotalAnnualTechnologyActivityByMode = (m["RateOfActivity"] * ds["YearSplit"]).sum(
            "TIMESLICE"
        )

        # AnnualTechnologyEmissionByMode = (
        #     ds["EmissionActivityRatio"] * TotalAnnualTechnologyActivityByMode
        # ).where(ds["EmissionActivityRatio"].notnull())

        AnnualTechnologyEmissionByMode = (
            passthrough_mul(TotalAnnualTechnologyActivityByMode, ds["EmissionActivityRatio"])
        ).where(ds["EmissionActivityRatio"].notnull())

        AnnualTechnologyEmission = AnnualTechnologyEmissionByMode.sum(
            dims="MODE_OF_OPERATION"
        ).where(ds["EmissionActivityRatio"].sum("MODE_OF_OPERATION") != 0)
        AnnualTechnologyEmissionPenaltyByEmission = (
            AnnualTechnologyEmission * ds["EmissionsPenalty"]
        ).where(
            ds["EmissionsPenalty"].notnull()
            & (ds["EmissionActivityRatio"].sum("MODE_OF_OPERATION") != 0)
        )
        AnnualTechnologyEmissionsPenalty = AnnualTechnologyEmissionPenaltyByEmission.sum(
            dims="EMISSION"
        )

        AnnualEmissions = AnnualTechnologyEmission.sum(dims="TECHNOLOGY")
        ModelPeriodEmissions = AnnualEmissions.sum(dims="YEAR") + ds[
            "ModelPeriodExogenousEmission"
        ].fillna(0)

        con = (
            AnnualTechnologyEmissionsPenalty / discount_factor_mid
            - m["DiscountedTechnologyEmissionsPenalty"]
            == 0
        )
        m.add_constraints(con, name="E5_DiscountedEmissionsPenaltyByTechnology")

        con = AnnualEmissions.fillna(0) <= ds["AnnualEmissionLimit"] - ds[
            "AnnualExogenousEmission"
        ].fillna(0)
        mask = (ds["AnnualEmissionLimit"] != -1) & (ds["AnnualEmissionLimit"].notnull())

        m.add_constraints(con, name="E8_AnnualEmissionsLimit", mask=mask)

        con = ModelPeriodEmissions.fillna(0) <= ds["ModelPeriodEmissionLimit"]
        mask = (ds["ModelPeriodEmissionLimit"] != -1) & (ds["ModelPeriodEmissionLimit"].notnull())
        m.add_constraints(con, name="E9_ModelPeriodEmissionsLimit", mask=mask)

    return m
