from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_regiongroup(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):

    # EMISSIONS

    AnnualTechnologyEmissionByModeRegionGroup = (
        (ds["EmissionActivityRatio"] * ds["YearSplit"] * m["RateOfActivity"]).sum("TIMESLICE")
    ).where(
        ds["EmissionActivityRatio"].notnull() & (ds["RegionGroupTagRegion"] == 1),
        drop=False,
    )

    AnnualTechnologyEmissionRegionGroup = AnnualTechnologyEmissionByModeRegionGroup.sum(
        dims="MODE_OF_OPERATION"
    ).where(ds["EmissionActivityRatio"].sum("MODE_OF_OPERATION") != 0, drop=False)

    AnnualEmissionsRegionGroupTag = AnnualTechnologyEmissionRegionGroup.sum(dims="TECHNOLOGY")
    AnnualEmissionsRegionGroup = AnnualEmissionsRegionGroupTag.sum(dims="REGION")

    # PRODUCTION

    RateOfProductionByTechnologyByModeRG = m["RateOfActivity"] * ds["OutputActivityRatio"].where(
        ds["OutputActivityRatio"].notnull() & (ds["RegionGroupTagRegion"] == 1), drop=False
    )
    RateOfProductionByTechnologyRegionGroup = RateOfProductionByTechnologyByModeRG.where(
        ds["OutputActivityRatio"].sum("MODE_OF_OPERATION") != 0, drop=False
    ).sum(dims="MODE_OF_OPERATION")
    RateOfProductionRegionGroup = RateOfProductionByTechnologyRegionGroup.sum(dims="TECHNOLOGY")
    ProductionByTechnologyRegionGroup = RateOfProductionByTechnologyRegionGroup * ds["YearSplit"]
    ProductionRegionGroup = RateOfProductionRegionGroup * ds["YearSplit"]
    ProductionAnnualRegionGroup = ProductionRegionGroup.sum(dims="TIMESLICE")
    ProductionAnnualRegionGroupAggregate = ProductionAnnualRegionGroup.sum(dims="REGION").where(
        ds["RegionGroupTagRegion"] == 1, drop=False
    )

    # RE PRODUCTION
    RateOfProductionByTechnologyByModeRERG = m["RateOfActivity"] * ds["OutputActivityRatio"].where(
        ds["OutputActivityRatio"].notnull()
        & (ds["RETagTechnology"] == 1)
        & (ds["RegionGroupTagRegion"] == 1),
        drop=False,
    )
    RateOfProductionByTechnologyRERegionGroup = RateOfProductionByTechnologyByModeRERG.where(
        ds["OutputActivityRatio"].sum("MODE_OF_OPERATION") != 0, drop=False
    ).sum(dims="MODE_OF_OPERATION")
    RateOfProductionRERegionGroup = RateOfProductionByTechnologyRERegionGroup.sum(dims="TECHNOLOGY")
    ProductionByTechnologyRERegionGroup = (
        RateOfProductionByTechnologyRERegionGroup * ds["YearSplit"]
    )
    ProductionRERegionGroup = RateOfProductionRERegionGroup * ds["YearSplit"]
    ProductionAnnualRERegionGroup = ProductionRERegionGroup.sum(dims="TIMESLICE")
    ProductionAnnualRERegionGroupAggregate = ProductionAnnualRERegionGroup.sum(dims="REGION").where(
        ds["RegionGroupTagRegion"] == 1, drop=False
    )

    lex.update(
        {
            "AnnualTechnologyEmissionByModeRegionGroup": AnnualTechnologyEmissionByModeRegionGroup,
            "AnnualTechnologyEmissionRegionGroup": AnnualTechnologyEmissionRegionGroup,
            "AnnualEmissionsRegionGroupTag": AnnualEmissionsRegionGroupTag,
            "AnnualEmissionsRegionGroup": AnnualEmissionsRegionGroup,
            "RateOfProductionByTechnologyByModeRG": RateOfProductionByTechnologyByModeRG,
            "RateOfProductionByTechnologyRegionGroup": RateOfProductionByTechnologyRegionGroup,
            "RateOfProductionRegionGroup": RateOfProductionRegionGroup,
            "ProductionRegionGroup": ProductionRegionGroup,
            "ProductionByTechnologyRegionGroup": ProductionByTechnologyRegionGroup,
            "ProductionAnnualRegionGroup": ProductionAnnualRegionGroup,
            "ProductionAnnualRegionGroupAggregate": ProductionAnnualRegionGroupAggregate,
            "RateOfProductionByTechnologyByModeRERG": RateOfProductionByTechnologyByModeRERG,
            "RateOfProductionByTechnologyRERegionGroup": RateOfProductionByTechnologyRERegionGroup,
            "RateOfProductionRERegionGroup": RateOfProductionRERegionGroup,
            "ProductionRERegionGroup": ProductionRERegionGroup,
            "ProductionByTechnologyRERegionGroup": ProductionByTechnologyRERegionGroup,
            "ProductionAnnualRERegionGroup": ProductionAnnualRERegionGroup,
            "ProductionAnnualRERegionGroupAggregate": ProductionAnnualRERegionGroupAggregate,
        }
    )
