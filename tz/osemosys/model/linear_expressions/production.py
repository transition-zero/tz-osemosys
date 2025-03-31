from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_quantities(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):
    # Production
    RateOfProductionByTechnologyByMode = m["RateOfActivity"] * ds["OutputActivityRatio"].where(
        ds["OutputActivityRatio"].notnull(), drop=False
    )
    RateOfProductionByTechnologyByModeRegionGroup = m["RateOfActivity"] * ds["OutputActivityRatio"].where(
       ds["OutputActivityRatio"].notnull() & (ds["RegionGroupTagRegion"] == 1), drop=False
    )
    RateOfProductionByTechnology = RateOfProductionByTechnologyByMode.where(
        ds["OutputActivityRatio"].sum("MODE_OF_OPERATION") != 0, drop=False
    ).sum(dims="MODE_OF_OPERATION")
    RateOfProductionByTechnologyRegionGroup = RateOfProductionByTechnologyByModeRegionGroup.where(
       ds["OutputActivityRatio"].sum("MODE_OF_OPERATION") != 0, drop=False
    ).sum(dims="MODE_OF_OPERATION")    
    RateOfProduction = RateOfProductionByTechnology.sum(dims="TECHNOLOGY")
    RateOfProductionRegionGroup = RateOfProductionByTechnologyRegionGroup.sum(dims="TECHNOLOGY")
    ProductionByTechnology = RateOfProductionByTechnology * ds["YearSplit"]
    ProductionByTechnologyRegionGroup = RateOfProductionByTechnologyRegionGroup * ds["YearSplit"]
    Production = RateOfProduction * ds["YearSplit"]
    ProductionRegionGroup = RateOfProductionRegionGroup * ds["YearSplit"]
    ProductionAnnual = Production.sum(dims="TIMESLICE")
    ProductionAnnualRegionGroup = ProductionRegionGroup.sum(dims="TIMESLICE")
    ProductionAnnualRegionGroupAggregate = ProductionAnnualRegionGroup.sum(dims="REGION").where(
        ds["RegionGroupTagRegion"] == 1, drop=False)

    RateOfUseByTechnologyByMode = m["RateOfActivity"] * ds["InputActivityRatio"].where(
        ds["InputActivityRatio"].notnull(), drop=False
    )
    RateOfUseByTechnology = RateOfUseByTechnologyByMode.where(
        ds["InputActivityRatio"].sum("MODE_OF_OPERATION") != 0, drop=False
    ).sum(dims="MODE_OF_OPERATION")
    RateOfUse = RateOfUseByTechnology.sum(dims="TECHNOLOGY")
    Use = RateOfUse * ds["YearSplit"]
    UseAnnual = Use.sum(dims="TIMESLICE")

    lex.update(
        {
            "RateOfProductionByTechnologyByMode": RateOfProductionByTechnologyByMode,
            "RateOfProductionByTechnologyByModeRegionGroup": 
                RateOfProductionByTechnologyByModeRegionGroup,
            "RateOfProductionByTechnology": RateOfProductionByTechnology,
            "RateOfProductionByTechnologyRegionGroup": RateOfProductionByTechnologyRegionGroup,
            "RateOfProduction": RateOfProduction,
            "RateOfProductionRegionGroup": RateOfProductionRegionGroup,
            "Production": Production,
            "ProductionRegionGroup": ProductionRegionGroup,
            "ProductionByTechnology": ProductionByTechnology,
            "ProductionByTechnologyRegionGroup": ProductionByTechnologyRegionGroup,
            "ProductionAnnual": ProductionAnnual,
            "ProductionAnnualRegionGroup": ProductionAnnualRegionGroup,
            "ProductionAnnualRegionGroupAggregate": ProductionAnnualRegionGroupAggregate,
            "RateOfUseByTechnologyByMode": RateOfUseByTechnologyByMode,
            "RateOfUseByTechnology": RateOfUseByTechnology,
            "RateOfUse": RateOfUse,
            "Use": Use,
            "UseAnnual": UseAnnual,
        }
    )
