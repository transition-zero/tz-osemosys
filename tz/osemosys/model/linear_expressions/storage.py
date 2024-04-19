from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_storage(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):
    ConversionFactor = ds["Conversionlh"] * ds["Conversionld"] * ds["Conversionls"]

    RateOfStorageCharge = (
        (ConversionFactor * ds["TechnologyToStorage"] * m["RateOfActivity"]).where(
            (ds["TechnologyToStorage"].notnull())
            & (ds["TechnologyToStorage"] != 0)
            & (ConversionFactor).notnull()
        )
    ).sum(["TECHNOLOGY", "MODE_OF_OPERATION", "TIMESLICE"])

    RateOfStorageDischarge = (
        (ConversionFactor * ds["TechnologyFromStorage"] * m["RateOfActivity"]).where(
            (ds["TechnologyFromStorage"].notnull())
            & (ds["TechnologyFromStorage"] != 0)
            & (ConversionFactor).notnull()
        )
    ).sum(["TECHNOLOGY", "MODE_OF_OPERATION", "TIMESLICE"])

    NetChargeWithinYear = (
        (RateOfStorageCharge - RateOfStorageDischarge).where(ConversionFactor.notnull())
        * ConversionFactor
        * ds["YearSplit"]
    ).sum("TIMESLICE")

    NetChargeWithinDay = (RateOfStorageCharge - RateOfStorageDischarge) * ds["DaySplit"]

    # YEAR
    firstyear_mask = ds["YEAR"] == ds["YEAR"][0]
    # TODO add StorageLevelStart rather than 0 for the first year
    # ds["StorageLevelStart"].expand_dims(YEAR=ds["YEAR"].values).where(firstyear_mask)
    StorageLevelYearStart = 0 + (
        m["StorageLevelYearStart"].shift(YEAR=1)
        + NetChargeWithinYear.shift(YEAR=1).sum(["SEASON", "DAYTYPE", "DAILYTIMEBRACKET"])
    ).where(~firstyear_mask)

    notlastyear_mask = ds["YEAR"] < ds["YEAR"][-1]
    StorageLevelYearFinish = StorageLevelYearStart.shift(YEAR=-1).where(notlastyear_mask) + (
        StorageLevelYearStart + NetChargeWithinYear.sum(["SEASON", "DAYTYPE", "DAILYTIMEBRACKET"])
    ).where(~notlastyear_mask)

    # SEASON
    firstseason_mask = ds["SEASON"] == ds["SEASON"][0]
    StorageLevelSeasonStart = StorageLevelYearStart.where(firstseason_mask) + (
        m["StorageLevelSeasonStart"].shift(SEASON=1)
        + NetChargeWithinYear.shift(SEASON=1).sum(["DAYTYPE", "DAILYTIMEBRACKET"])
    ).where(~firstseason_mask)

    # DAYTYPE
    firstdaytype_mask = ds["DAYTYPE"] == ds["DAYTYPE"][0]
    StorageLevelDayTypeStart = StorageLevelSeasonStart.where(firstdaytype_mask) + (
        m["StorageLevelDayTypeStart"].shift(DAYTYPE=1)
        + (
            (NetChargeWithinDay.shift(DAYTYPE=1) * ds["DaysInDayType"].shift(DAYTYPE=1)).sum(
                ["DAILYTIMEBRACKET"]
            )
        )
    ).where(~firstdaytype_mask)

    lastseason_mask = ds["SEASON"] == ds["SEASON"][-1]
    lastdaytype_mask = ds["DAYTYPE"] == ds["DAYTYPE"][-1]

    StorageLevelDayTypeFinish = (
        (StorageLevelYearFinish.where((lastseason_mask) & (lastdaytype_mask)))
        + (StorageLevelSeasonStart.shift(SEASON=-1).where((lastdaytype_mask) & (~lastseason_mask)))
        + (
            m["StorageLevelDayTypeFinish"].shift(DAYTYPE=-1)
            - (NetChargeWithinDay.shift(DAYTYPE=-1) * ds["DaysInDayType"].shift(DAYTYPE=-1)).sum(
                ["DAILYTIMEBRACKET"]
            )
        ).where(
            ~((lastseason_mask) & (lastdaytype_mask)) & ~((lastdaytype_mask) & (~lastseason_mask))
        )
    )

    StorageUpperLimit = m["AccumulatedNewStorageCapacity"] + ds["ResidualStorageCapacity"]

    StorageLowerLimit = ds["MinStorageCharge"] * StorageUpperLimit

    lex.update(
        {
            "RateOfStorageCharge": RateOfStorageCharge,
            "RateOfStorageDischarge": RateOfStorageDischarge,
            "NetChargeWithinYear": NetChargeWithinYear,
            "NetChargeWithinDay": NetChargeWithinDay,
            "StorageLevelYearStart": StorageLevelYearStart,
            "StorageLevelYearFinish": StorageLevelYearFinish,
            "StorageLevelSeasonStart": StorageLevelSeasonStart,
            "StorageLevelDayTypeStart": StorageLevelDayTypeStart,
            "StorageLevelDayTypeFinish": StorageLevelDayTypeFinish,
            "StorageUpperLimit": StorageUpperLimit,
            "StorageLowerLimit": StorageLowerLimit,
        }
    )
