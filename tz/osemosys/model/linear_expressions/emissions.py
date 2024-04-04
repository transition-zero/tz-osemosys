from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_emissions(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):
    AnnualTechnologyEmissionByMode = (
        (ds["EmissionActivityRatio"] * ds["YearSplit"] * m["RateOfActivity"])
        .sum("TIMESLICE")
        .where(ds["EmissionActivityRatio"].notnull())
    )

    AnnualTechnologyEmission = AnnualTechnologyEmissionByMode.sum(dims="MODE_OF_OPERATION").where(
        ds["EmissionActivityRatio"].sum("MODE_OF_OPERATION") != 0
    )

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

    lex.update(
        {
            "AnnualTechnologyEmissionByMode": AnnualTechnologyEmissionByMode,
            "AnnualTechnologyEmission": AnnualTechnologyEmission,
            "AnnualTechnologyEmissionPenaltyByEmission": AnnualTechnologyEmissionPenaltyByEmission,
            "AnnualTechnologyEmissionsPenalty": AnnualTechnologyEmissionsPenalty,
            "AnnualEmissions": AnnualEmissions,
            "ModelPeriodEmissions": ModelPeriodEmissions,
        }
    )
