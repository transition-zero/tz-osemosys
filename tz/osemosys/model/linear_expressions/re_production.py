from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_re_production(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):
    RateOfProductionByTechnologyByModeRE = m["RateOfActivity"] * ds["OutputActivityRatio"].where(
        ds["OutputActivityRatio"].notnull() & (ds["RETagTechnology"] == 1), drop=False
    )
    RateOfProductionByTechnologyRE = RateOfProductionByTechnologyByModeRE.where(
        ds["OutputActivityRatio"].sum("MODE_OF_OPERATION") != 0, drop=False
    ).sum(dims="MODE_OF_OPERATION")
    RateOfProductionRE = RateOfProductionByTechnologyRE.sum(dims="TECHNOLOGY")
    ProductionByTechnologyRE = RateOfProductionByTechnologyRE * ds["YearSplit"]
    ProductionRE = RateOfProductionRE * ds["YearSplit"]
    ProductionAnnualRE = ProductionRE.sum(dims="TIMESLICE")

    lex.update(
        {
            "RateOfProductionByTechnologyByModeRE": RateOfProductionByTechnologyByModeRE,
            "RateOfProductionByTechnologyRE": RateOfProductionByTechnologyRE,
            "RateOfProductionRE": RateOfProductionRE,
            "ProductionRE": ProductionRE,
            "ProductionByTechnologyRE": ProductionByTechnologyRE,
            "ProductionAnnualRE": ProductionAnnualRE,
        }
    )
