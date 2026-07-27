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
        dim="MODE_OF_OPERATION"
    ).where(ds["EmissionActivityRatio"].sum("MODE_OF_OPERATION") != 0, drop=False)

    AnnualEmissionsRegionGroupTag = AnnualTechnologyEmissionRegionGroup.sum(dim="TECHNOLOGY")
    AnnualEmissionsRegionGroup = AnnualEmissionsRegionGroupTag.sum(dim="REGION")

    # PRODUCTION

    RateOfProductionByTechnologyByModeRG = m["RateOfActivity"] * ds["OutputActivityRatio"].where(
        ds["OutputActivityRatio"].notnull() & (ds["RegionGroupTagRegion"] == 1), drop=False
    )
    RateOfProductionByTechnologyRegionGroup = RateOfProductionByTechnologyByModeRG.where(
        ds["OutputActivityRatio"].sum("MODE_OF_OPERATION") != 0, drop=False
    ).sum(dim="MODE_OF_OPERATION")
    RateOfProductionRegionGroup = RateOfProductionByTechnologyRegionGroup.sum(dim="TECHNOLOGY")
    ProductionByTechnologyRegionGroup = RateOfProductionByTechnologyRegionGroup * ds["YearSplit"]
    ProductionRegionGroup = RateOfProductionRegionGroup * ds["YearSplit"]
    ProductionAnnualRegionGroup = ProductionRegionGroup.sum(dim="TIMESLICE")
    ProductionAnnualRegionGroupAggregate = ProductionAnnualRegionGroup.sum(dim="REGION").where(
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
    ).sum(dim="MODE_OF_OPERATION")
    RateOfProductionRERegionGroup = RateOfProductionByTechnologyRERegionGroup.sum(dim="TECHNOLOGY")
    ProductionByTechnologyRERegionGroup = (
        RateOfProductionByTechnologyRERegionGroup * ds["YearSplit"]
    )
    ProductionRERegionGroup = RateOfProductionRERegionGroup * ds["YearSplit"]
    ProductionAnnualRERegionGroup = ProductionRERegionGroup.sum(dim="TIMESLICE")
    ProductionAnnualRERegionGroupAggregate = ProductionAnnualRERegionGroup.sum(dim="REGION").where(
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
