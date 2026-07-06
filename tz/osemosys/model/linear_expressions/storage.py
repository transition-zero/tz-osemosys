from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_storage(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):
    # Use the social DiscountRate so that discounted storage salvage values land in
    # the same present-value basis as technology salvage values in the objective.
    DiscountFactorStorage = (1 + ds["DiscountRate"]) ** (
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

    StorageChargeSeasonally = (
        (
            ds["YearSplit"]
            * ds["TechnologyToStorage"]
            * (
                ds["Conversionlh"].fillna(0)
                * ds["Conversionls"].fillna(0)
                * ds["Conversionld"].fillna(0)
            ).sum(dim="DAYTYPE")
            * m["RateOfActivity"]
        ).where(
            (ds["TechnologyToStorage"].notnull())
            & (ds["StorageBalanceSeason"] != 0)
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

    StorageDischargeSeasonally = (
        (
            ds["YearSplit"]
            * ds["TechnologyFromStorage"]
            * (
                ds["Conversionlh"].fillna(0)
                * ds["Conversionls"].fillna(0)
                * ds["Conversionld"].fillna(0)
            ).sum(dim="DAYTYPE")
            * m["RateOfActivity"]
        ).where(
            (ds["TechnologyFromStorage"].notnull())
            & (ds["StorageBalanceSeason"] != 0)
            & (ds["Conversionls"] != 0),
            drop=False,
        )
    ).sum(["TECHNOLOGY", "MODE_OF_OPERATION", "TIMESLICE"])

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

    # Storage capital discounted using social DiscountRate for comparability with technology
    # costs in the objective function.
    DiscountFactorStorage_annual = (1 + ds["DiscountRate"]) ** (
        ds.coords["YEAR"] - min(ds.coords["YEAR"])
    )

    # PVAnnuity uses social DiscountRate (matching the technology path in discounting.py)
    PVAnnuityStorage = (
        (1 - (1 + ds["DiscountRate"]) ** (-(ds["OperationalLifeStorage"])))
        * (1 + ds["DiscountRate"])
        / ds["DiscountRate"]
    )

    CapitalRecoveryFactorStorage = (1 - (1 + ds["DiscountRateStorage"]) ** (-1)) / (
        1 - (1 + ds["DiscountRateStorage"]) ** (-(ds["OperationalLifeStorage"]))
    )

    # Financials updated to the same method as used for technologies (financials.py) and trades (trade.py)
    CapitalInvestmentStorage = (
        ds["CapitalCostStorage"].fillna(0)
        * m["NewStorageCapacity"]
        * CapitalRecoveryFactorStorage
        * PVAnnuityStorage
    )

    DiscountedCapitalInvestmentStorage = CapitalInvestmentStorage / DiscountFactorStorage_annual

    # Storage salvage value components (OSeMOSYS SI7/SI8).
    # SV1 uses the social DiscountRate so the sinking-fund fraction is consistent with
    # the social-rate discounting applied to both capital investment and salvage value.
    # When DiscountRateStorage != DiscountRate this prevents the fraction from being
    # calibrated to one rate while the base capital cost is evaluated at another.
    SV1NumeratorStorage = (1 + ds["DiscountRate"]) ** (
        max(ds.coords["YEAR"]) - ds.coords["YEAR"] + 1
    ) - 1

    SV1DenominatorStorage = (1 + ds["DiscountRate"]) ** ds["OperationalLifeStorage"] - 1

    SV2NumeratorStorage = max(ds.coords["YEAR"]) - ds.coords["YEAR"] + 1

    SV2DenominatorStorage = ds["OperationalLifeStorage"]

    sv1_storage_mask = (
        (ds["DepreciationMethod"] == 1)
        & ((ds.coords["YEAR"] + ds["OperationalLifeStorage"] - 1) > max(ds.coords["YEAR"]))
        & (ds["DiscountRate"] > 0)
    )
    sv2_storage_mask = (
        (ds["DepreciationMethod"] == 1)
        & ((ds.coords["YEAR"] + ds["OperationalLifeStorage"] - 1) > max(ds.coords["YEAR"]))
        & (ds["DiscountRate"] == 0)
    ) | (
        (ds["DepreciationMethod"] == 2)
        & ((ds.coords["YEAR"] + ds["OperationalLifeStorage"] - 1) > max(ds.coords["YEAR"]))
    )

    # salvage value factors (storage)
    SV1CostStorage = ds["CapitalCostStorage"].fillna(0) * (
        CapitalRecoveryFactorStorage
        * PVAnnuityStorage
        * (1 - (SV1NumeratorStorage / SV1DenominatorStorage))
    )

    SV2CostStorage = ds["CapitalCostStorage"].fillna(0) * (
        CapitalRecoveryFactorStorage
        * PVAnnuityStorage
        * (1 - (SV2NumeratorStorage / SV2DenominatorStorage))
    )

    # salvage value (storage)
    SalvageValueStorage = (
        m["NewStorageCapacity"] * SV1CostStorage.where(sv1_storage_mask, drop=False)
        + m["NewStorageCapacity"] * SV2CostStorage.where(sv2_storage_mask, drop=False)
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
