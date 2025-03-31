from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_re_production(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):
    RateOfProductionByTechnologyByModeRE = m["RateOfActivity"] * ds["OutputActivityRatio"].where(
        ds["OutputActivityRatio"].notnull() & (ds["RETagTechnology"] == 1), drop=False
    )
    RateOfProductionByTechnologyByModeRERegionGroup = m["RateOfActivity"] * ds["OutputActivityRatio"].where(
       ds["OutputActivityRatio"].notnull() & (ds["RETagTechnology"] == 1) & (ds["RegionGroupTagRegion"] == 1), drop=False
    )
    RateOfProductionByTechnologyRE = RateOfProductionByTechnologyByModeRE.where(
        ds["OutputActivityRatio"].sum("MODE_OF_OPERATION") != 0, drop=False
    ).sum(dims="MODE_OF_OPERATION")
    RateOfProductionByTechnologyRERegionGroup = RateOfProductionByTechnologyByModeRERegionGroup.where(
       ds["OutputActivityRatio"].sum("MODE_OF_OPERATION") != 0, drop=False
    ).sum(dims="MODE_OF_OPERATION")    
    RateOfProductionRE = RateOfProductionByTechnologyRE.sum(dims="TECHNOLOGY")
    RateOfProductionRERegionGroup = RateOfProductionByTechnologyRERegionGroup.sum(dims="TECHNOLOGY")
    ProductionByTechnologyRE = RateOfProductionByTechnologyRE * ds["YearSplit"]
    ProductionByTechnologyRERegionGroup = RateOfProductionByTechnologyRERegionGroup * ds["YearSplit"]
    ProductionRE = RateOfProductionRE * ds["YearSplit"]
    ProductionRERegionGroup = RateOfProductionRERegionGroup * ds["YearSplit"]
    ProductionAnnualRE = ProductionRE.sum(dims="TIMESLICE")
    ProductionAnnualRERegionGroup = ProductionRERegionGroup.sum(dims="TIMESLICE")
    ProductionAnnualRERegionGroupAggregate = ProductionAnnualRERegionGroup.sum(dims="REGION").where(
        ds["RegionGroupTagRegion"] == 1, drop=False
    )

    lex.update(
        {
            "RateOfProductionByTechnologyByModeRE": RateOfProductionByTechnologyByModeRE,
            "RateOfProductionByTechnologyByModeRERegionGroup": 
                RateOfProductionByTechnologyByModeRERegionGroup,
            "RateOfProductionByTechnologyRE": RateOfProductionByTechnologyRE,
            "RateOfProductionByTechnologyRERegionGroup": RateOfProductionByTechnologyRERegionGroup,
            "RateOfProductionRE": RateOfProductionRE,
            "RateOfProductionRERegionGroup": RateOfProductionRERegionGroup,
            "ProductionRE": ProductionRE,
            "ProductionRERegionGroup": ProductionRERegionGroup,
            "ProductionByTechnologyRE": ProductionByTechnologyRE,
            "ProductionByTechnologyRERegionGroup": ProductionByTechnologyRERegionGroup,            
            "ProductionAnnualRE": ProductionAnnualRE,
            "ProductionAnnualRERegionGroup": ProductionAnnualRERegionGroup,
            "ProductionAnnualRERegionGroupAggregate": ProductionAnnualRERegionGroupAggregate,
        }
    )
