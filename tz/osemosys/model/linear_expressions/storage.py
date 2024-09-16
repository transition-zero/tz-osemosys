from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_storage(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):
    DiscountFactorStorage = (1 + ds["DiscountRateStorage"]) ** (
        1 + ds.coords["YEAR"][-1] - ds.coords["YEAR"][0]
    )

    RateOfStorageCharge = (
        (ds["TechnologyToStorage"] * m["RateOfActivity"]).where(
            (ds["TechnologyToStorage"].notnull()) & (ds["TechnologyToStorage"] != 0), drop=True
        )
    ).sum(["TECHNOLOGY", "MODE_OF_OPERATION"])

    StorageChargeDaily = (
        (
            ds["DaySplit"]
            * ds["TechnologyToStorage"]
            * (
                ds["Conversionlh"].fillna(0)
                * ds["Conversionls"].fillna(0)
                * ds["Conversionld"].fillna(0)
            ).sum(dim="DAILYTIMEBRACKET")
            * m["RateOfActivity"]
        ).where(
            (ds["TechnologyToStorage"].notnull())
            & (ds["StorageBalanceDay"] != 0)
            & (ds["Conversionls"] != 0),
            drop=False,
        )
    ).sum(["TECHNOLOGY", "MODE_OF_OPERATION", "TIMESLICE"])

    RateOfStorageDischarge = (
        (ds["TechnologyFromStorage"] * m["RateOfActivity"]).where(
            (ds["TechnologyFromStorage"].notnull()) & (ds["TechnologyFromStorage"] != 0), drop=True
        )
    ).sum(["TECHNOLOGY", "MODE_OF_OPERATION"])

    StorageDischargeDaily = (
        (
            ds["DaySplit"]
            * ds["TechnologyFromStorage"]
            * (
                ds["Conversionlh"].fillna(0)
                * ds["Conversionls"].fillna(0)
                * ds["Conversionld"].fillna(0)
            ).sum(dim="DAILYTIMEBRACKET")
            * m["RateOfActivity"]
        ).where(
            (ds["TechnologyFromStorage"].notnull())
            & (ds["StorageBalanceDay"] != 0)
            & (ds["Conversionls"] != 0),
            drop=False,
        )
    ).sum(["TECHNOLOGY", "MODE_OF_OPERATION", "TIMESLICE"])

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
        m["NewStorageCapacity"] * SV1CostStorage.where(lex["sv1_mask"], drop=False)
        + m["NewStorageCapacity"] * SV2CostStorage.where(lex["sv2_mask"], drop=False)
    ).fillna(0)

    DiscountedSalvageValueStorage = SalvageValueStorage / DiscountFactorStorage

    TotalDiscountedStorageCost = DiscountedCapitalInvestmentStorage - DiscountedSalvageValueStorage

    lex.update(
        {
            "RateOfStorageCharge": RateOfStorageCharge,
            "RateOfStorageDischarge": RateOfStorageDischarge,
            "StorageChargeDaily": StorageChargeDaily,
            "StorageDischargeDaily": StorageDischargeDaily,
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
