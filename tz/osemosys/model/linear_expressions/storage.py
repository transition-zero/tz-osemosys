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
            (
                ds["TechnologyToStorage"]
                * (
                    # DaySplit is the term that maps timeslices to the assigned number of hours in the day,
                    # essentially converting from power to energy volume.
                    ds["DaySplit"]  # dimension: DAILYTIMEBRACKET, YEAR
                    * ds["Conversionlh"].fillna(0)  # dimension: DAILYTIMEBRACKET, TIMESLICE
                    * ds["Conversionls"].fillna(0)  # dimension: SEASON, TIMESLICE
                    * ds["Conversionld"].fillna(0)  # dimension: DAYTYPE, TIMESLICE
                ).sum(dim="DAILYTIMEBRACKET")
            )
            * m["RateOfActivity"]
        )
        .where(
            (ds["TechnologyToStorage"].notnull())
            & (ds["StorageBalanceDay"] != 0)
            & (ds["Conversionls"] != 0),
            drop=False,
        )
        .sum(["TECHNOLOGY", "MODE_OF_OPERATION", "TIMESLICE"])
    )

    StorageChargeSeasonally = (
        (
            (
                ds["TechnologyToStorage"]
                * (
                    # YearSplit is the term that maps timeslices to the assigned number of hours in the year,
                    # essentially converting from power to energy volume.
                    ds["YearSplit"]  # dimension: TIMESLICE, YEAR
                    * ds["Conversionlh"].fillna(0)  # dimension: DAILYTIMEBRACKET, TIMESLICE
                    * ds["Conversionls"].fillna(0)  # dimension: SEASON, TIMESLICE
                    * ds["Conversionld"].fillna(0)  # dimension: DAYTYPE, TIMESLICE
                ).sum(dim=["DAYTYPE", "DAILYTIMEBRACKET"])
            )
            * m["RateOfActivity"]
        )
        .where(
            (ds["TechnologyToStorage"].notnull())
            & (ds["StorageBalanceSeason"] != 0)
            & (ds["Conversionls"] != 0),
            drop=False,
        )
        .sum(["TECHNOLOGY", "MODE_OF_OPERATION", "TIMESLICE"])
    )

    RateOfStorageDischarge = (
        (ds["TechnologyFromStorage"] * m["RateOfActivity"]).where(
            (ds["TechnologyFromStorage"].notnull()) & (ds["TechnologyFromStorage"] != 0), drop=True
        )
    ).sum(["TECHNOLOGY", "MODE_OF_OPERATION"])

    StorageDischargeDaily = (
        (
            (
                ds["TechnologyFromStorage"]
                * (
                    # DaySplit is the term that maps timeslices to the assigned number of hours in the day,
                    # essentially converting from power to energy volume.
                    ds["DaySplit"]  # dimension: DAILYTIMEBRACKET, YEAR
                    * ds["Conversionlh"].fillna(0)  # dimension: DAILYTIMEBRACKET, TIMESLICE
                    * ds["Conversionls"].fillna(0)  # dimension: SEASON, TIMESLICE
                    * ds["Conversionld"].fillna(0)  # dimension: DAYTYPE, TIMESLICE
                ).sum(dim="DAILYTIMEBRACKET")
            )
            * m["RateOfActivity"]
        )
        .where(
            (ds["TechnologyFromStorage"].notnull())
            & (ds["StorageBalanceDay"] != 0)
            & (ds["Conversionls"] != 0),
            drop=False,
        )
        .sum(["TECHNOLOGY", "MODE_OF_OPERATION", "TIMESLICE"])
    )

    StorageDischargeSeasonally = (
        (
            (
                ds["TechnologyFromStorage"]
                * (
                    # YearSplit is the term that maps timeslices to the assigned number of hours in the year,
                    # essentially converting from power to energy volume.
                    ds["YearSplit"]  # dimension: TIMESLICE, YEAR
                    * ds["Conversionlh"].fillna(0)  # dimension: DAILYTIMEBRACKET, TIMESLICE
                    * ds["Conversionls"].fillna(0)  # dimension: SEASON, TIMESLICE
                    * ds["Conversionld"].fillna(0)  # dimension: DAYTYPE, TIMESLICE
                ).sum(dim=["DAYTYPE", "DAILYTIMEBRACKET"])
            )
            * m["RateOfActivity"]
        )
        .where(
            (ds["TechnologyFromStorage"].notnull())
            & (ds["StorageBalanceSeason"] != 0)
            & (ds["Conversionls"] != 0),
            drop=False,
        )
        .sum(["TECHNOLOGY", "MODE_OF_OPERATION", "TIMESLICE"])
    )

    NetCharge = ds["YearSplit"] * (RateOfStorageCharge - RateOfStorageDischarge)

    # Explicit storage level (state of charge) per timeslice
    StorageLevel = m["StorageLevel"]

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
            "StorageChargeSeasonally": StorageChargeSeasonally,
            "StorageDischargeSeasonally": StorageDischargeSeasonally,
            "NetCharge": NetCharge,
            "StorageLevel": StorageLevel,
            "AccumulatedNewStorageCapacity": AccumulatedNewStorageCapacity,
            "GrossStorageCapacity": GrossStorageCapacity,
            "CapitalInvestmentStorage": CapitalInvestmentStorage,
            "DiscountedCapitalInvestmentStorage": DiscountedCapitalInvestmentStorage,
            "TotalDiscountedStorageCost": TotalDiscountedStorageCost,
        }
    )
