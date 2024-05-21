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

        # storage level may not exceed gross capacity
        con = lex["StorageLevel"] <= lex["GrossStorageCapacity"].expand_dims(
            {"TIMESLICE": ds["TIMESLICE"]}
        ).stack(YRTS=["YEAR", "TIMESLICE"])
        m.add_constraints(con, name="StorageGrossCapacitySufficiency")

        # storage level may not be less than minimum charge
        if "MinStorageCharge" in ds.data_vars:
            con = lex["StorageLevel"].fillna(0) >= ds["MinStorageCharge"].expand_dims(
                {"TIMESLICE": ds["TIMESLICE"]}
            ).stack(YRTS=["YEAR", "TIMESLICE"])
            m.add_constraints(con, name="StorageMinimumCharge")

        # storage charge rate may not exceed max charge rate
        if "StorageMaxChargeRate" in ds.data_vars:
            con = lex["RateOfStorageCharge"] <= ds["StorageMaxChargeRate"]
            m.add_constraints(con, name="SC5_MaxChargeConstraint")

        # # storage discharge rate may not exceed max discharge rate
        if "StorageMaxDischargeRate" in ds.data_vars:
            con = lex["RateOfStorageDischarge"] <= ds["StorageMaxDischargeRate"]
            m.add_constraints(con, name="SC6_MaxDischargeConstraint")

    return m
