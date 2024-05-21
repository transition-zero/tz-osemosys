from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_storage(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):

    DiscountFactorStorage = (1 + ds["DiscountRateStorage"]) ** (
        1 + ds.coords["YEAR"][-1] - ds.coords["YEAR"][0]
    )

    ds["Conversionlh"] * ds["Conversionld"] * ds["Conversionls"]

    RateOfStorageCharge = (
        (ds["TechnologyToStorage"] * m["RateOfActivity"]).where(
            (ds["TechnologyToStorage"].notnull()) & (ds["TechnologyToStorage"] != 0)
        )
    ).sum(["TECHNOLOGY", "MODE_OF_OPERATION"])

    RateOfStorageDischarge = (
        (ds["TechnologyFromStorage"] * m["RateOfActivity"]).where(
            (ds["TechnologyFromStorage"].notnull()) & (ds["TechnologyFromStorage"] != 0)
        )
    ).sum(["TECHNOLOGY", "MODE_OF_OPERATION"])

    NetCharge = ds["YearSplit"] * (RateOfStorageCharge - RateOfStorageDischarge)

    NetChargeReshape = NetCharge.stack(YRTS=["YEAR", "TIMESLICE"])

    StorageLevel = NetChargeReshape.cumsum("YRTS") + ds.get("StorageLevelStart", 0.0)

    NewStorageCapacity = m["NewStorageCapacity"].rename(YEAR="BUILDYEAR")

    # mask to handle operating life of storage
    mask = (ds.YEAR - NewStorageCapacity.data.BUILDYEAR >= 0) & (
        ds.YEAR - NewStorageCapacity.data.BUILDYEAR < ds.OperationalLifeStorage
    )

    AccumulatedNewStorageCapacity = NewStorageCapacity.where(mask).sum("BUILDYEAR")

    GrossStorageCapacity = AccumulatedNewStorageCapacity + ds["ResidualStorageCapacity"]

    CapitalInvestmentStorage = ds["CapitalCostStorage"] * m["NewStorageCapacity"]
    DiscountedCapitalInvestmentStorage = CapitalInvestmentStorage / lex["DiscountFactor"]

    SV1CostStorage = ds["CapitalCostStorage"].fillna(0) * (
        1 - (lex["SV1Numerator"] / lex["SV1Denominator"])
    )

    SV2CostStorage = ds["CapitalCostStorage"].fillna(0) * (
        1 - (lex["SV2Numerator"] / lex["SV2Denominator"])
    )

    SalvageValueStorage = (
        m["NewStorageCapacity"] * SV1CostStorage.where(lex["sv1_mask"])
        + m["NewStorageCapacity"] * SV2CostStorage.where(lex["sv2_mask"])
    ).fillna(0)

    DiscountedSalvageValueStorage = SalvageValueStorage / DiscountFactorStorage

    TotalDiscountedStorageCost = DiscountedCapitalInvestmentStorage - DiscountedSalvageValueStorage

    lex.update(
        {
            "RateOfStorageCharge": RateOfStorageCharge,
            "RateOfStorageDischarge": RateOfStorageDischarge,
            "NetCharge": NetCharge,
            "StorageLevel": StorageLevel,
            "NewStorageCapacity": NewStorageCapacity,
            "AccumulatedNewStorageCapacity": AccumulatedNewStorageCapacity,
            "GrossStorageCapacity": GrossStorageCapacity,
            "CapitalInvestmentStorage": CapitalInvestmentStorage,
            "DiscountedCapitalInvestmentStorage": DiscountedCapitalInvestmentStorage,
            "TotalDiscountedStorageCost": TotalDiscountedStorageCost,
        }
    )
