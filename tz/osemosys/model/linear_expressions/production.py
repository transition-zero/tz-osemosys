from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_quantities(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):
    # Production
    RateOfProductionByTechnologyByMode = m["RateOfActivity"] * ds["OutputActivityRatio"].where(
        ds["OutputActivityRatio"].notnull()
    )
    RateOfProductionByTechnology = RateOfProductionByTechnologyByMode.where(
        ds["OutputActivityRatio"].sum("MODE_OF_OPERATION") != 0
    ).sum(dims="MODE_OF_OPERATION")
    RateOfProduction = RateOfProductionByTechnology.sum(dims="TECHNOLOGY")
    ProductionByTechnology = RateOfProductionByTechnology * ds["YearSplit"]
    Production = RateOfProduction * ds["YearSplit"]
    ProductionAnnual = Production.sum(dims="TIMESLICE")

    RateOfUseByTechnologyByMode = m["RateOfActivity"] * ds["InputActivityRatio"].where(
        ds["InputActivityRatio"].notnull()
    )
    RateOfUseByTechnology = RateOfUseByTechnologyByMode.where(
        ds["InputActivityRatio"].sum("MODE_OF_OPERATION") != 0
    ).sum(dims="MODE_OF_OPERATION")
    RateOfUse = RateOfUseByTechnology.sum(dims="TECHNOLOGY")
    Use = RateOfUse * ds["YearSplit"]
    UseAnnual = Use.sum(dims="TIMESLICE")

    lex.update(
        {
            "RateOfProductionByTechnologyByMode": RateOfProductionByTechnologyByMode,
            "RateOfProductionByTechnology": RateOfProductionByTechnology,
            "RateOfProduction": RateOfProduction,
            "Production": Production,
            "ProductionByTechnology": ProductionByTechnology,
            "ProductionAnnual": ProductionAnnual,
            "RateOfUseByTechnologyByMode": RateOfUseByTechnologyByMode,
            "RateOfUseByTechnology": RateOfUseByTechnology,
            "RateOfUse": RateOfUse,
            "Use": Use,
            "UseAnnual": UseAnnual,
        }
    )
