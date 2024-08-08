from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_re_production(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):
    # ProductionRE
    RateOfProductionByTechnologyByModeRE = m["RateOfActivity"] * ds["OutputActivityRatio"].where(
        ds["OutputActivityRatio"].notnull()
        & (ds["RETagTechnology"] == 1)
    )
    RateOfProductionByTechnologyRE = RateOfProductionByTechnologyByModeRE.where(
        ds["OutputActivityRatio"].sum("MODE_OF_OPERATION") != 0
    ).sum(dims="MODE_OF_OPERATION")
    RateOfProductionRE = RateOfProductionByTechnologyRE.sum(dims="TECHNOLOGY")
    ProductionByTechnologyRE = RateOfProductionByTechnologyRE * ds["YearSplit"]
    ProductionRE = RateOfProductionRE * ds["YearSplit"]
    ProductionAnnualRE = ProductionRE.sum(dims="TIMESLICE")

    # RateOfUseByTechnologyByModeRE = m["RateOfActivity"] * ds["InputActivityRatio"].where(
    #     ds["InputActivityRatio"].notnull()
    #     & (ds["RETagTechnology"] == 1)
    # )
    # RateOfUseByTechnologyRE = RateOfUseByTechnologyByModeRE.where(
    #     ds["InputActivityRatio"].sum("MODE_OF_OPERATION") != 0
    # ).sum(dims="MODE_OF_OPERATION")
    # RateOfUseRE = RateOfUseByTechnologyRE.sum(dims="TECHNOLOGY")
    # UseRE = RateOfUseRE * ds["YearSplit"]
    # UseAnnualRE = UseRE.sum(dims="TIMESLICE")

    lex.update(
        {
            "RateOfProductionByTechnologyByModeRE": RateOfProductionByTechnologyByModeRE,
            "RateOfProductionByTechnologyRE": RateOfProductionByTechnologyRE,
            "RateOfProductionRE": RateOfProductionRE,
            "ProductionRE": ProductionRE,
            "ProductionByTechnologyRE": ProductionByTechnologyRE,
            "ProductionAnnualRE": ProductionAnnualRE,
            # "RateOfUseByTechnologyByModeRE": RateOfUseByTechnologyByModeRE,
            # "RateOfUseByTechnologyRE": RateOfUseByTechnologyRE,
            # "RateOfUseRE": RateOfUseRE,
            # "UseRE": UseRE,
            # "UseAnnualRE": UseAnnualRE,
        }
    )
