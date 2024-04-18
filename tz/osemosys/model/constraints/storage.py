from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model

# from timeit import default_timer as timer


def add_storage_constraints(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]) -> Model:
    """Add Storage constraints to the model.
    Representation of storage technologies, ensuring that storage levels, charge/discharge rates
    are maintained for each daily time bracket, day type, and season.


    Arguments
    ---------
    ds: xarray.Dataset
        The parameters dataset
    m: linopy.Model
        A linopy model
    lex: Dict[str, LinearExpression]


    Returns
    -------
    linopy.Model


    Notes
    -----
    ```ampl
    s.t. S1_RateOfStorageCharge
    {r in REGION, s in STORAGE, ls in SEASON, ld in DAYTYPE, lh in DAILYTIMEBRACKET, y in YEAR}:
        sum{t in TECHNOLOGY, m in MODE_OF_OPERATION, l in TIMESLICE:
        TechnologyToStorage[r,t,s,m] > 0}
        RateOfActivity[r,l,t,m,y]
        * TechnologyToStorage[r,t,s,m]
        * Conversionls[l,ls] * Conversionld[l,ld] * Conversionlh[l,lh]
        =
        RateOfStorageCharge[r,s,ls,ld,lh,y];

    s.t. S2_RateOfStorageDischarge
    {r in REGION, s in STORAGE, ls in SEASON, ld in DAYTYPE, lh in DAILYTIMEBRACKET, y in YEAR}:
        sum{t in TECHNOLOGY, m in MODE_OF_OPERATION, l in TIMESLICE:
        TechnologyFromStorage[r,t,s,m] > 0}
        RateOfActivity[r,l,t,m,y]
        * TechnologyFromStorage[r,t,s,m]
        * Conversionls[l,ls] * Conversionld[l,ld] * Conversionlh[l,lh]
        =
        RateOfStorageDischarge[r,s,ls,ld,lh,y];

    s.t. S3_NetChargeWithinYear
    {r in REGION, s in STORAGE, ls in SEASON, ld in DAYTYPE, lh in DAILYTIMEBRACKET, y in YEAR}:
        sum{l in TIMESLICE:Conversionls[l,ls]>0 && Conversionld[l,ld] > 0 && Conversionlh[l,lh] > 0}
        (RateOfStorageCharge[r,s,ls,ld,lh,y]
        - RateOfStorageDischarge[r,s,ls,ld,lh,y])
        * YearSplit[l,y]
        * Conversionls[l,ls] * Conversionld[l,ld] * Conversionlh[l,lh]
        =
        NetChargeWithinYear[r,s,ls,ld,lh,y];

    s.t. S4_NetChargeWithinDay
    {r in REGION, s in STORAGE, ls in SEASON, ld in DAYTYPE, lh in DAILYTIMEBRACKET, y in YEAR}:
        (RateOfStorageCharge[r,s,ls,ld,lh,y]
        - RateOfStorageDischarge[r,s,ls,ld,lh,y])
        * DaySplit[lh,y]
        =
        NetChargeWithinDay[r,s,ls,ld,lh,y];

    s.t. S5_and_S6_StorageLevelYearStart
    {r in REGION, s in STORAGE, y in YEAR}:
        if y = min{yy in YEAR} min(yy)
        then StorageLevelStart[r,s]
        else StorageLevelYearStart[r,s,y-1]
        + sum{ls in SEASON, ld in DAYTYPE, lh in DAILYTIMEBRACKET}
        NetChargeWithinYear[r,s,ls,ld,lh,y-1]
        =
        StorageLevelYearStart[r,s,y];

    s.t. S7_and_S8_StorageLevelYearFinish
    {r in REGION, s in STORAGE, y in YEAR}:
        if y < max{yy in YEAR} max(yy)
        then StorageLevelYearStart[r,s,y+1]
        else StorageLevelYearStart[r,s,y]
        + sum{ls in SEASON, ld in DAYTYPE, lh in DAILYTIMEBRACKET}
        NetChargeWithinYear[r,s,ls,ld,lh,y]
        =
        StorageLevelYearFinish[r,s,y];

    s.t. S9_and_S10_StorageLevelSeasonStart
    {r in REGION, s in STORAGE, ls in SEASON, y in YEAR}:
        if ls = min{lsls in SEASON} min(lsls)
        then StorageLevelYearStart[r,s,y]
        else StorageLevelSeasonStart[r,s,ls-1,y]
        + sum{ld in DAYTYPE, lh in DAILYTIMEBRACKET}
        NetChargeWithinYear[r,s,ls-1,ld,lh,y]
        =
        StorageLevelSeasonStart[r,s,ls,y];

    s.t. S11_and_S12_StorageLevelDayTypeStart
    {r in REGION, s in STORAGE, ls in SEASON, ld in DAYTYPE, y in YEAR}:
        if ld = min{ldld in DAYTYPE} min(ldld)
        then StorageLevelSeasonStart[r,s,ls,y]
        else StorageLevelDayTypeStart[r,s,ls,ld-1,y]
        + sum{lh in DAILYTIMEBRACKET}
        NetChargeWithinDay[r,s,ls,ld-1,lh,y]
        * DaysInDayType[ls,ld-1,y]
        =
        StorageLevelDayTypeStart[r,s,ls,ld,y];

    s.t. S13_and_S14_and_S15_StorageLevelDayTypeFinish
    {r in REGION, s in STORAGE, ls in SEASON, ld in DAYTYPE, y in YEAR}:
        if ls = max{lsls in SEASON} max(lsls) && ld = max{ldld in DAYTYPE} max(ldld)
        then StorageLevelYearFinish[r,s,y]
        else if ld = max{ldld in DAYTYPE} max(ldld)
        then StorageLevelSeasonStart[r,s,ls+1,y]
        else StorageLevelDayTypeFinish[r,s,ls,ld+1,y]
        - sum{lh in DAILYTIMEBRACKET}
        NetChargeWithinDay[r,s,ls,ld+1,lh,y]
        * DaysInDayType[ls,ld+1,y]
        =
        StorageLevelDayTypeFinish[r,s,ls,ld,y];

    #
    ##########		Storage Constraints				#############
    #
    s.t. SC1_LowerLimit_BeginningOfDailyTimeBracketOfFirstInstanceOfDayTypeInFirstWeekConstraint
    {r in REGION, s in STORAGE, ls in SEASON, ld in DAYTYPE, lh in DAILYTIMEBRACKET, y in YEAR}:
        0 <= (StorageLevelDayTypeStart[r,s,ls,ld,y]
        + sum{lhlh in DAILYTIMEBRACKET:lh-lhlh>0} NetChargeWithinDay[r,s,ls,ld,lhlh,y])
        - StorageLowerLimit[r,s,y];

    s.t. SC1_UpperLimit_BeginningOfDailyTimeBracketOfFirstInstanceOfDayTypeInFirstWeekConstraint
    {r in REGION, s in STORAGE, ls in SEASON, ld in DAYTYPE, lh in DAILYTIMEBRACKET, y in YEAR}:
        (StorageLevelDayTypeStart[r,s,ls,ld,y]
        + sum{lhlh in DAILYTIMEBRACKET:lh-lhlh>0} NetChargeWithinDay[r,s,ls,ld,lhlh,y])
        - StorageUpperLimit[r,s,y] <= 0;

    s.t. SC2_LowerLimit_EndOfDailyTimeBracketOfLastInstanceOfDayTypeInFirstWeekConstraint
    {r in REGION, s in STORAGE, ls in SEASON, ld in DAYTYPE, lh in DAILYTIMEBRACKET, y in YEAR}:
        0 <= if ld > min{ldld in DAYTYPE} min(ldld)
        then (StorageLevelDayTypeStart[r,s,ls,ld,y]
        - sum{lhlh in DAILYTIMEBRACKET:lh-lhlh<0} NetChargeWithinDay[r,s,ls,ld-1,lhlh,y])
        - StorageLowerLimit[r,s,y];

    s.t. SC2_UpperLimit_EndOfDailyTimeBracketOfLastInstanceOfDayTypeInFirstWeekConstraint
    {r in REGION, s in STORAGE, ls in SEASON, ld in DAYTYPE, lh in DAILYTIMEBRACKET, y in YEAR}:
        if ld > min{ldld in DAYTYPE} min(ldld)
        then (StorageLevelDayTypeStart[r,s,ls,ld,y]
        - sum{lhlh in DAILYTIMEBRACKET:lh-lhlh<0} NetChargeWithinDay[r,s,ls,ld-1,lhlh,y])
        - StorageUpperLimit[r,s,y]
        <= 0;

    s.t. SC3_LowerLimit_EndOfDailyTimeBracketOfLastInstanceOfDayTypeInLastWeekConstraint
    {r in REGION, s in STORAGE, ls in SEASON, ld in DAYTYPE, lh in DAILYTIMEBRACKET, y in YEAR}:
        0 <= (StorageLevelDayTypeFinish[r,s,ls,ld,y]
        - sum{lhlh in DAILYTIMEBRACKET:lh-lhlh<0} NetChargeWithinDay[r,s,ls,ld,lhlh,y])
        - StorageLowerLimit[r,s,y];

    s.t. SC3_UpperLimit_EndOfDailyTimeBracketOfLastInstanceOfDayTypeInLastWeekConstraint
    {r in REGION, s in STORAGE, ls in SEASON, ld in DAYTYPE, lh in DAILYTIMEBRACKET, y in YEAR}:
        (StorageLevelDayTypeFinish[r,s,ls,ld,y]
        - sum{lhlh in DAILYTIMEBRACKET:lh-lhlh<0} NetChargeWithinDay[r,s,ls,ld,lhlh,y])
        - StorageUpperLimit[r,s,y] <= 0;

    s.t. SC4_LowerLimit_BeginningOfDailyTimeBracketOfFirstInstanceOfDayTypeInLastWeekConstraint
    {r in REGION, s in STORAGE, ls in SEASON, ld in DAYTYPE, lh in DAILYTIMEBRACKET, y in YEAR}:
        0 <= if ld > min{ldld in DAYTYPE} min(ldld)
        then (StorageLevelDayTypeFinish[r,s,ls,ld-1,y]
        + sum{lhlh in DAILYTIMEBRACKET:lh-lhlh>0} NetChargeWithinDay[r,s,ls,ld,lhlh,y])
        - StorageLowerLimit[r,s,y];

    s.t. SC4_UpperLimit_BeginningOfDailyTimeBracketOfFirstInstanceOfDayTypeInLastWeekConstraint
    {r in REGION, s in STORAGE, ls in SEASON, ld in DAYTYPE, lh in DAILYTIMEBRACKET, y in YEAR}:
        if ld > min{ldld in DAYTYPE} min(ldld)
        then (StorageLevelDayTypeFinish[r,s,ls,ld-1,y]
        + sum{lhlh in DAILYTIMEBRACKET:lh-lhlh>0} NetChargeWithinDay[r,s,ls,ld,lhlh,y])
        - StorageUpperLimit[r,s,y] <= 0;

    s.t. SC5_MaxChargeConstraint
    {r in REGION, s in STORAGE, ls in SEASON, ld in DAYTYPE, lh in DAILYTIMEBRACKET, y in YEAR}:
        RateOfStorageCharge[r,s,ls,ld,lh,y] <= StorageMaxChargeRate[r,s];

    s.t. SC6_MaxDischargeConstraint
    {r in REGION, s in STORAGE, ls in SEASON, ld in DAYTYPE, lh in DAILYTIMEBRACKET, y in YEAR}:
        RateOfStorageDischarge[r,s,ls,ld,lh,y] <= StorageMaxDischargeRate[r,s];

    #
    #########		Storage Investments				#############
    #
    s.t. SI1_StorageUpperLimit
    {r in REGION, s in STORAGE, y in YEAR}:
        AccumulatedNewStorageCapacity[r,s,y]
        + ResidualStorageCapacity[r,s,y]
        = StorageUpperLimit[r,s,y];

    s.t. SI2_StorageLowerLimit
    {r in REGION, s in STORAGE, y in YEAR}:
        MinStorageCharge[r,s,y]
        * StorageUpperLimit[r,s,y]
        = StorageLowerLimit[r,s,y];

    s.t. SI3_TotalNewStorage
    {r in REGION, s in STORAGE, y in YEAR}:
        sum{yy in YEAR: y-yy < OperationalLifeStorage[r,s] && y-yy>=0} NewStorageCapacity[r,s,yy]
        = AccumulatedNewStorageCapacity[r,s,y];

    s.t. SI4_UndiscountedCapitalInvestmentStorage
    {r in REGION, s in STORAGE, y in YEAR}:
        CapitalCostStorage[r,s,y]
        * NewStorageCapacity[r,s,y] = CapitalInvestmentStorage[r,s,y];

    s.t. SI5_DiscountingCapitalInvestmentStorage
    {r in REGION, s in STORAGE, y in YEAR}:
        CapitalInvestmentStorage[r,s,y]/(DiscountFactorStorage[r,s,y])
        = DiscountedCapitalInvestmentStorage[r,s,y];

    s.t. SI6_SalvageValueStorageAtEndOfPeriod1
    {r in REGION, s in STORAGE, y in YEAR:
        (y+OperationalLifeStorage[r,s]-1)
        <= (max{yy in YEAR} max(yy))}: 0 = SalvageValueStorage[r,s,y];

    s.t. SI7_SalvageValueStorageAtEndOfPeriod2
    {r in REGION, s in STORAGE, y in YEAR:
        (DepreciationMethod[r]=1 && (y+OperationalLifeStorage[r,s]-1) > (max{yy in YEAR} max(yy))
        && DiscountRateStorage[r,s]=0)
        || (DepreciationMethod[r]=2
        && (y+OperationalLifeStorage[r,s]-1) > (max{yy in YEAR} max(yy)))}:
        CapitalInvestmentStorage[r,s,y]
        * (1-(max{yy in YEAR} max(yy) - y+1)
        / OperationalLifeStorage[r,s])
        = SalvageValueStorage[r,s,y];

    s.t. SI8_SalvageValueStorageAtEndOfPeriod3
    {r in REGION, s in STORAGE, y in YEAR:
        DepreciationMethod[r]=1
        && (y+OperationalLifeStorage[r,s]-1) > (max{yy in YEAR} max(yy))
        && DiscountRateStorage[r,s]>0}:
        CapitalInvestmentStorage[r,s,y]
        * (1-(((1+DiscountRateStorage[r,s])^(max{yy in YEAR} max(yy) - y+1)-1)
        / ((1+DiscountRateStorage[r,s])^OperationalLifeStorage[r,s]-1)))
        = SalvageValueStorage[r,s,y];

    s.t. SI9_SalvageValueStorageDiscountedToStartYear
    {r in REGION, s in STORAGE, y in YEAR}:
        SalvageValueStorage[r,s,y]
        / ((1+DiscountRateStorage[r,s])^(max{yy in YEAR} max(yy)-min{yy in YEAR} min(yy)+1))
        = DiscountedSalvageValueStorage[r,s,y];

    s.t. SI10_TotalDiscountedCostByStorage{r in REGION, s in STORAGE, y in YEAR}:
        DiscountedCapitalInvestmentStorage[r,s,y]
        - DiscountedSalvageValueStorage[r,s,y]
        = TotalDiscountedStorageCost[r,s,y];
    ```
    """
    if ds["STORAGE"].size > 0:

        m.add_constraints(
            m["StorageLevelYearStart"] == lex["StorageLevelYearStart"],
            name="S5_and_S6_StorageLevelYearStart",
        )
        m.add_constraints(
            m["StorageLevelYearFinish"] == lex["StorageLevelYearFinish"],
            name="S7_and_S8_StorageLevelYearFinish",
        )
        m.add_constraints(
            m["StorageLevelSeasonStart"] == lex["StorageLevelSeasonStart"],
            name="S9_and_S10_StorageLevelSeasonStart",
        )
        m.add_constraints(
            m["StorageLevelDayTypeStart"] == lex["StorageLevelDayTypeStart"],
            name="S11_and_S12_StorageLevelDayTypeStart",
        )
        m.add_constraints(
            m["StorageLevelDayTypeFinish"] == lex["StorageLevelDayTypeFinish"],
            name="S13_and_S14_and_S15_StorageLevelDayTypeFinish",
        )

        # STORAGE INVESTMENTS

        discount_factor_storage = (1 + ds["DiscountRate"]) ** (
            ds.coords["YEAR"] - ds.coords["YEAR"][0]
        )

        new_storage_cap = m["NewStorageCapacity"].rename(YEAR="BUILDYEAR")
        mask = (ds.YEAR - new_storage_cap.data.BUILDYEAR >= 0) & (
            ds.YEAR - new_storage_cap.data.BUILDYEAR < ds.OperationalLifeStorage
        )
        con = m["AccumulatedNewStorageCapacity"] - new_storage_cap.where(mask).sum("BUILDYEAR") == 0
        m.add_constraints(con, name="SI3_TotalNewStorage")

        discount_factor_storage = (1 + ds["DiscountRate"]) ** (
            ds.coords["YEAR"] - ds.coords["YEAR"][0]
        )
        CapitalInvestmentStorage = ds["CapitalCostStorage"] * m["NewStorageCapacity"]
        con = (CapitalInvestmentStorage / discount_factor_storage) - m[
            "DiscountedCapitalInvestmentStorage"
        ] == 0
        m.add_constraints(con, name="SI5_DiscountingCapitalInvestmentStorage")

        def numerator_sv1(y: int):
            return (1 + ds["DiscountRateStorage"]) ** (ds.coords["YEAR"][-1] - y + 1) - 1

        def denominator_sv1():
            return (1 + ds["DiscountRateStorage"]) ** ds["OperationalLifeStorage"] - 1

        def salvage_cost_sv1(ds):
            return ds["CapitalCostStorage"].fillna(0) * (
                1 - (numerator_sv1(ds.coords["YEAR"]) / denominator_sv1())
            )

        con = m["SalvageValueStorage"] - (m["NewStorageCapacity"] * salvage_cost_sv1(ds)) == 0
        mask = (
            (ds["DepreciationMethod"] == 1)
            & ((ds.coords["YEAR"] + ds["OperationalLifeStorage"] - 1) > ds.coords["YEAR"][-1])
            & (ds["DiscountRateStorage"] > 0)
        )
        m.add_constraints(con, name="SI6_SalvageValueStorageAtEndOfPeriod1", mask=mask)

        def numerator_sv2(y: int):
            return ds.coords["YEAR"][-1] - y + 1

        def denominator_sv2():
            return ds["OperationalLifeStorage"]

        def salvage_cost_sv2(ds):
            return ds["CapitalCostStorage"].fillna(0) * (
                1 - (numerator_sv2(ds.coords["YEAR"]) / denominator_sv2())
            )

        con = m["SalvageValueStorage"] - (m["NewStorageCapacity"] * salvage_cost_sv2(ds)) == 0
        mask = (
            (ds["DepreciationMethod"] == 1)
            & ((ds.coords["YEAR"] + ds["OperationalLifeStorage"] - 1) > ds.coords["YEAR"][-1])
            & (ds["DiscountRateStorage"] == 0)
        ) | (
            (ds["DepreciationMethod"] == 2)
            & ((ds.coords["YEAR"] + ds["OperationalLifeStorage"] - 1) > ds.coords["YEAR"][-1])
        )
        m.add_constraints(con, name="SI7_SalvageValueStorageAtEndOfPeriod2", mask=mask)

        con = m["SalvageValueStorage"] == 0
        mask = (ds.coords["YEAR"] + ds["OperationalLifeStorage"] - 1) <= ds.coords["YEAR"][-1]
        m.add_constraints(con, name="SI8_SalvageValueStorageAtEndOfPeriod3", mask=mask)

        def discounting(ds):
            return (1 + ds["DiscountRateStorage"]) ** (
                1 + ds.coords["YEAR"][-1] - ds.coords["YEAR"][0]
            )

        con = m["DiscountedSalvageValueStorage"] - m["SalvageValueStorage"] / discounting(ds) == 0
        m.add_constraints(con, name="SI9_SalvageValueStorageDiscountedToStartYear")

        con = (
            m["DiscountedCapitalInvestmentStorage"] - m["DiscountedSalvageValueStorage"]
            == m["TotalDiscountedStorageCost"]
        )
        m.add_constraints(con, name="SI10_TotalDiscountedCostByStorage")

        # CAPACITY CONSTRAINTS

        con = (
            lex["StorageLevelDayTypeStart"]
            + lex["NetChargeWithinDay"].shift(DAILYTIMEBRACKET=1).cumsum("DAILYTIMEBRACKET")
            - lex["StorageLowerLimit"]
            >= 0
        )
        m.add_constraints(con, name="SC1_LowerLimit_BeginningOfFirstWeek")

        con = (
            lex["StorageLevelDayTypeStart"]
            + lex["NetChargeWithinDay"].shift(DAILYTIMEBRACKET=1).cumsum("DAILYTIMEBRACKET")
            - lex["StorageUpperLimit"]
            <= 0
        )
        m.add_constraints(con, name="SC1_UpperLimit_BeginningOfFirstWeek")

        con = (
            lex["StorageLevelDayTypeStart"]
            # sum minus cumsum gives the sum of DAILYTIMEBRACKET for all future timebrackets
            - (
                lex["NetChargeWithinDay"].shift(DAYTYPE=1).sum("DAILYTIMEBRACKET")
                - lex["NetChargeWithinDay"].shift(DAYTYPE=1).cumsum("DAILYTIMEBRACKET")
            )
            - lex["StorageLowerLimit"]
            >= 0
        )
        mask = ds["DAYTYPE"] != ds["DAYTYPE"][0]
        m.add_constraints(con, name="SC2_LowerLimit_EndOfFirstWeek", mask=mask)

        con = (
            lex["StorageLevelDayTypeStart"]
            # sum minus cumsum gives the sum of DAILYTIMEBRACKET for all future timebrackets
            - (
                lex["NetChargeWithinDay"].shift(DAYTYPE=1).sum("DAILYTIMEBRACKET")
                - lex["NetChargeWithinDay"].shift(DAYTYPE=1).cumsum("DAILYTIMEBRACKET")
            )
            - lex["StorageUpperLimit"]
            <= 0
        )
        mask = ds["DAYTYPE"] != ds["DAYTYPE"][0]
        m.add_constraints(con, name="SC2_UpperLimit_EndOfFirstWeek", mask=mask)

        con = (
            lex["StorageLevelDayTypeFinish"]
            # sum minus cumsum gives the sum of DAILYTIMEBRACKET for all future timebrackets
            - (
                lex["NetChargeWithinDay"].sum("DAILYTIMEBRACKET")
                - lex["NetChargeWithinDay"].cumsum("DAILYTIMEBRACKET")
            )
            - lex["StorageLowerLimit"]
            >= 0
        )
        m.add_constraints(con, name="SC3_LowerLimit_EndOfLastWeek")

        con = (
            lex["StorageLevelDayTypeFinish"]
            # sum minus cumsum gives the sum of DAILYTIMEBRACKET for all future timebrackets
            - (
                lex["NetChargeWithinDay"].sum("DAILYTIMEBRACKET")
                - lex["NetChargeWithinDay"].cumsum("DAILYTIMEBRACKET")
            )
            - lex["StorageUpperLimit"]
            <= 0
        )
        m.add_constraints(con, name="SC3_UpperLimit_EndOfLastWeek")

        con = (
            lex["StorageLevelDayTypeFinish"].shift(DAYTYPE=1)
            + lex["NetChargeWithinDay"].shift(DAILYTIMEBRACKET=1).cumsum("DAILYTIMEBRACKET")
            - lex["StorageLowerLimit"]
            >= 0
        )
        mask = ds["DAYTYPE"] != ds["DAYTYPE"][0]
        m.add_constraints(con, name="SC4_LowerLimit_BeginningOfLastWeek", mask=mask)

        con = (
            lex["StorageLevelDayTypeFinish"].shift(DAYTYPE=1)
            + lex["NetChargeWithinDay"].shift(DAILYTIMEBRACKET=1).cumsum("DAILYTIMEBRACKET")
            - lex["StorageUpperLimit"]
            <= 0
        )
        mask = ds["DAYTYPE"] != ds["DAYTYPE"][0]
        m.add_constraints(con, name="SC4_UpperLimit_BeginningOfLastWeek", mask=mask)

        if "StorageMaxChargeRate" in ds.data_vars:
            con = lex["RateOfStorageCharge"] <= ds["StorageMaxChargeRate"]
            m.add_constraints(con, name="SC5_MaxChargeConstraint")

        if "StorageMaxDischargeRate" in ds.data_vars:
            con = lex["RateOfStorageDischarge"] <= ds["StorageMaxDischargeRate"]
            m.add_constraints(con, name="SC6_MaxDischargeConstraint")

    return m
