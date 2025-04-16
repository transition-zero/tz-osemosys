from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_emissions(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):
    AnnualTechnologyEmissionByMode = (
        (ds["EmissionActivityRatio"] * ds["YearSplit"] * m["RateOfActivity"])
        .sum("TIMESLICE")
        .where(ds["EmissionActivityRatio"].notnull(), drop=False)
    )

    AnnualTechnologyEmissionByModeRegionGroup = (
        (ds["EmissionActivityRatio"] * ds["YearSplit"] * m["RateOfActivity"]).sum("TIMESLICE")
    ).where(
        ds["EmissionActivityRatio"].notnull() & (ds["RegionGroupTagRegion"] == 1),
        drop=False,
    )

    AnnualTechnologyEmission = AnnualTechnologyEmissionByMode.sum(dims="MODE_OF_OPERATION").where(
        ds["EmissionActivityRatio"].sum("MODE_OF_OPERATION") != 0, drop=False
    )

    AnnualTechnologyEmissionRegionGroup = AnnualTechnologyEmissionByModeRegionGroup.sum(
        dims="MODE_OF_OPERATION"
    ).where(ds["EmissionActivityRatio"].sum("MODE_OF_OPERATION") != 0, drop=False)

    AnnualTechnologyEmissionPenaltyByEmission = (
        AnnualTechnologyEmission * ds["EmissionsPenalty"]
    ).where(
        ds["EmissionsPenalty"].notnull()
        & (ds["EmissionActivityRatio"].sum("MODE_OF_OPERATION") != 0),
        drop=False,
    )

    AnnualTechnologyEmissionsPenalty = AnnualTechnologyEmissionPenaltyByEmission.sum(
        dims="EMISSION"
    )

    AnnualEmissions = AnnualTechnologyEmission.sum(dims="TECHNOLOGY")
    AnnualEmissionsRegionGroupTag = AnnualTechnologyEmissionRegionGroup.sum(dims="TECHNOLOGY")
    AnnualEmissionsRegionGroup = AnnualEmissionsRegionGroupTag.sum(dims="REGION")

    ModelPeriodEmissions = AnnualEmissions.sum(dims="YEAR") + ds[
        "ModelPeriodExogenousEmission"
    ].fillna(0)

    lex.update(
        {
            "AnnualTechnologyEmissionByMode": AnnualTechnologyEmissionByMode,
            "AnnualTechnologyEmissionByModeRegionGroup": AnnualTechnologyEmissionByModeRegionGroup,
            "AnnualTechnologyEmission": AnnualTechnologyEmission,
            "AnnualTechnologyEmissionRegionGroup": AnnualTechnologyEmissionRegionGroup,
            "AnnualTechnologyEmissionPenaltyByEmission": AnnualTechnologyEmissionPenaltyByEmission,
            "AnnualTechnologyEmissionsPenalty": AnnualTechnologyEmissionsPenalty,
            "AnnualEmissions": AnnualEmissions,
            "AnnualEmissionsRegionGroupTag": AnnualEmissionsRegionGroupTag,
            "AnnualEmissionsRegionGroup": AnnualEmissionsRegionGroup,
            "ModelPeriodEmissions": ModelPeriodEmissions,
        }
    )
