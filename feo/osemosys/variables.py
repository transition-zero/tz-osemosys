import xarray as xr
from linopy import Model
from numpy import inf


def add_demand_variables(ds: xr.Dataset, m: Model) -> Model:
    """Add demand variables to the model

    Arguments
    ---------
    ds: xarray.Dataset
        The parameters dataset
    m: linopy.Model
        A linopy model

    Returns
    -------
    linopy.Model
    """
    RTiFY = [ds.coords["REGION"], ds.coords["TIMESLICE"], ds.coords["FUEL"], ds.coords["YEAR"]]

    # mask = ds['SpecifiedAnnualDemand'].expand_dims('TIMESLICE').notnull()
    m.add_variables(lower=0, upper=inf, coords=RTiFY, name="RateOfDemand", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RTiFY, name="Demand", integer=False)
    return m


def add_storage_variables(ds: xr.Dataset, m: Model) -> Model:
    """Add storage variables to the model

        Arguments
    ---------
    ds: xarray.Dataset
        The parameters dataset
    m: linopy.Model
        A linopy model

    Returns
    -------
    linopy.Model
    """
    # Create the required index
    RSSDDY = [
        ds.coords["REGION"],
        ds.coords["STORAGE"],
        ds.coords["SEASON"],
        ds.coords["DAYTYPE"],
        ds.coords["DAILYTIMEBRACKET"],
        ds.coords["YEAR"],
    ]
    RSY = [ds.coords["REGION"], ds.coords["STORAGE"], ds.coords["YEAR"]]

    m.add_variables(lower=-inf, upper=inf, coords=RSSDDY, name="RateOfStorageCharge", integer=False)
    m.add_variables(
        lower=-inf, upper=inf, coords=RSSDDY, name="RateOfStorageDischarge", integer=False
    )
    m.add_variables(lower=-inf, upper=inf, coords=RSSDDY, name="NetChargeWithinYear", integer=False)
    m.add_variables(lower=-inf, upper=inf, coords=RSSDDY, name="NetChargeWithinDay", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RSY, name="StorageLevelYearStart", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RSY, name="StorageLevelYearFinish", integer=False)
    coords = [ds.coords["REGION"], ds.coords["STORAGE"], ds.coords["SEASON"], ds.coords["YEAR"]]
    m.add_variables(
        lower=0, upper=inf, coords=coords, name="StorageLevelSeasonStart", integer=False
    )
    coords = [
        ds.coords["REGION"],
        ds.coords["STORAGE"],
        ds.coords["SEASON"],
        ds.coords["DAYTYPE"],
        ds.coords["YEAR"],
    ]
    m.add_variables(
        lower=0, upper=inf, coords=coords, name="StorageLevelDayTypeStart", integer=False
    )
    coords = [
        ds.coords["REGION"],
        ds.coords["STORAGE"],
        ds.coords["SEASON"],
        ds.coords["DAYTYPE"],
        ds.coords["YEAR"],
    ]
    m.add_variables(
        lower=0, upper=inf, coords=coords, name="StorageLevelDayTypeFinish", integer=False
    )
    m.add_variables(lower=0, upper=inf, coords=RSY, name="StorageLowerLimit", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RSY, name="StorageUpperLimit", integer=False)
    m.add_variables(
        lower=0, upper=inf, coords=RSY, name="AccumulatedNewStorageCapacity", integer=False
    )
    m.add_variables(lower=0, upper=inf, coords=RSY, name="NewStorageCapacity", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RSY, name="CapitalInvestmentStorage", integer=False)
    m.add_variables(
        lower=0, upper=inf, coords=RSY, name="DiscountedCapitalInvestmentStorage", integer=False
    )
    m.add_variables(lower=0, upper=inf, coords=RSY, name="SalvageValueStorage", integer=False)
    m.add_variables(
        lower=0, upper=inf, coords=RSY, name="DiscountedSalvageValueStorage", integer=False
    )
    m.add_variables(
        lower=0, upper=inf, coords=RSY, name="TotalDiscountedStorageCost", integer=False
    )
    return m


def add_capacity_variables(ds: xr.Dataset, m: Model) -> Model:
    """Add capacity variables to the model

    Arguments
    ---------
    ds: xarray.Dataset
        The parameters dataset
    m: linopy.Model
        A linopy model

    Returns
    -------
    linopy.Model
    """
    # Create the required index
    RTeY = [ds.coords["REGION"], ds.coords["TECHNOLOGY"], ds.coords["YEAR"]]

    # masks
    mask = ds["CapacityOfOneTechnologyUnit"].notnull()

    m.add_variables(
        lower=0, upper=inf, coords=RTeY, name="NumberOfNewTechnologyUnits", integer=True, mask=mask
    )
    m.add_variables(lower=0, upper=inf, coords=RTeY, name="NewCapacity", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RTeY, name="AccumulatedNewCapacity", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RTeY, name="TotalCapacityAnnual", integer=False)
    return m


def add_activity_variables(ds: xr.Dataset, m: Model) -> Model:
    """Add activity variables to the model

    Arguments
    ---------
    ds: xarray.Dataset
        The parameters dataset
    m: linopy.Model
        A linopy model

    Returns
    -------
    linopy.Model
    """
    # Add indices
    RRTiFY = [
        ds.coords["REGION"],
        ds.coords["_REGION"],
        ds.coords["TIMESLICE"],
        ds.coords["FUEL"],
        ds.coords["YEAR"],
    ]
    RRFY = [ds.coords["REGION"], ds.coords["_REGION"], ds.coords["FUEL"], ds.coords["YEAR"]]
    RFY = [ds.coords["REGION"], ds.coords["FUEL"], ds.coords["YEAR"]]
    RTiFY = [ds.coords["REGION"], ds.coords["TIMESLICE"], ds.coords["FUEL"], ds.coords["YEAR"]]
    RTiTeFY = [
        ds.coords["REGION"],
        ds.coords["TIMESLICE"],
        ds.coords["TECHNOLOGY"],
        ds.coords["FUEL"],
        ds.coords["YEAR"],
    ]
    RTiTeMY = [
        ds.coords["REGION"],
        ds.coords["TIMESLICE"],
        ds.coords["TECHNOLOGY"],
        ds.coords["MODE_OF_OPERATION"],
        ds.coords["YEAR"],
    ]
    RTiTeMFY = [
        ds.coords["REGION"],
        ds.coords["TIMESLICE"],
        ds.coords["TECHNOLOGY"],
        ds.coords["MODE_OF_OPERATION"],
        ds.coords["FUEL"],
        ds.coords["YEAR"],
    ]
    RTeY = [ds.coords["REGION"], ds.coords["TECHNOLOGY"], ds.coords["YEAR"]]

    # Add masks
    iac_mask = ds["InputActivityRatio"].notnull()
    iac_mask_m = ds["InputActivityRatio"].sum("MODE_OF_OPERATION") != 0
    oac_mask = ds["OutputActivityRatio"].notnull()
    oac_mask_m = ds["OutputActivityRatio"].sum("MODE_OF_OPERATION") != 0

    m.add_variables(lower=0, upper=inf, coords=RTiTeMY, name="RateOfActivity", integer=False)
    coords = [
        ds.coords["REGION"],
        ds.coords["TECHNOLOGY"],
        ds.coords["TIMESLICE"],
        ds.coords["YEAR"],
    ]
    m.add_variables(lower=0, upper=inf, coords=coords, name="RateOfTotalActivity", integer=False)
    m.add_variables(
        lower=0, upper=inf, coords=RTeY, name="TotalTechnologyAnnualActivity", integer=False
    )
    coords = [
        ds.coords["REGION"],
        ds.coords["TECHNOLOGY"],
        ds.coords["MODE_OF_OPERATION"],
        ds.coords["YEAR"],
    ]
    m.add_variables(
        lower=0, upper=inf, coords=coords, name="TotalAnnualTechnologyActivityByMode", integer=False
    )
    coords = [ds.coords["REGION"], ds.coords["TECHNOLOGY"]]
    m.add_variables(
        lower=-inf,
        upper=inf,
        coords=coords,
        name="TotalTechnologyModelPeriodActivity",
        integer=False,
    )
    m.add_variables(
        lower=0,
        upper=inf,
        coords=RTiTeMFY,
        name="RateOfProductionByTechnologyByMode",
        integer=False,
        mask=oac_mask,
    )
    m.add_variables(
        lower=0,
        upper=inf,
        coords=RTiTeFY,
        name="RateOfProductionByTechnology",
        integer=False,
        mask=oac_mask_m,
    )
    m.add_variables(
        lower=0,
        upper=inf,
        coords=RTiTeFY,
        name="ProductionByTechnology",
        integer=False,
        mask=oac_mask_m,
    )
    coords = [ds.coords["REGION"], ds.coords["TECHNOLOGY"], ds.coords["FUEL"], ds.coords["YEAR"]]
    m.add_variables(
        lower=0,
        upper=inf,
        coords=coords,
        name="ProductionByTechnologyAnnual",
        integer=False,
        mask=oac_mask_m,
    )
    m.add_variables(lower=0, upper=inf, coords=RTiFY, name="RateOfProduction", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RTiFY, name="Production", integer=False)
    m.add_variables(
        lower=0,
        upper=inf,
        coords=RTiTeMFY,
        name="RateOfUseByTechnologyByMode",
        integer=False,
        mask=iac_mask,
    )
    m.add_variables(
        lower=0,
        upper=inf,
        coords=RTiTeFY,
        name="RateOfUseByTechnology",
        integer=False,
        mask=iac_mask_m,
    )
    coords = [ds.coords["REGION"], ds.coords["TECHNOLOGY"], ds.coords["FUEL"], ds.coords["YEAR"]]
    m.add_variables(
        lower=0,
        upper=inf,
        coords=coords,
        name="UseByTechnologyAnnual",
        integer=False,
        mask=iac_mask_m,
    )
    m.add_variables(lower=0, upper=inf, coords=RTiFY, name="RateOfUse", integer=False)
    m.add_variables(
        lower=0, upper=inf, coords=RTiTeFY, name="UseByTechnology", integer=False, mask=iac_mask_m
    )
    m.add_variables(lower=0, upper=inf, coords=RTiFY, name="Use", integer=False)
    m.add_variables(lower=-inf, upper=inf, coords=RRTiFY, name="Trade", integer=False)
    m.add_variables(lower=-inf, upper=inf, coords=RRFY, name="TradeAnnual", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RFY, name="ProductionAnnual", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RFY, name="UseAnnual", integer=False)

    return m


def add_emission_variables(ds: xr.Dataset, m: Model) -> Model:
    """Add emisison variables to the model

    Arguments
    ---------
    ds: xarray.Dataset
        The parameters dataset
    m: linopy.Model
        A linopy model

    Returns
    -------
    linopy.Model
    """
    # Create the required indexes
    RTeY = [ds.coords["REGION"], ds.coords["TECHNOLOGY"], ds.coords["YEAR"]]
    RE = [ds.coords["REGION"], ds.coords["EMISSION"]]
    REY = [ds.coords["REGION"], ds.coords["EMISSION"], ds.coords["YEAR"]]
    RTeEY = [ds.coords["REGION"], ds.coords["TECHNOLOGY"], ds.coords["EMISSION"], ds.coords["YEAR"]]
    RTeEMY = [
        ds.coords["REGION"],
        ds.coords["TECHNOLOGY"],
        ds.coords["EMISSION"],
        ds.coords["MODE_OF_OPERATION"],
        ds.coords["YEAR"],
    ]
    # Create the masks
    ear_mask = ds["EmissionActivityRatio"].notnull()
    ear_mask_m = ds["EmissionActivityRatio"].sum("MODE_OF_OPERATION") != 0
    ep_mask = ds["EmissionsPenalty"].notnull()

    # Add the variables
    m.add_variables(
        lower=0,
        upper=inf,
        coords=RTeEMY,
        name="AnnualTechnologyEmissionByMode",
        integer=False,
        mask=ear_mask,
    )
    m.add_variables(
        lower=0,
        upper=inf,
        coords=RTeEY,
        name="AnnualTechnologyEmission",
        integer=False,
        mask=ear_mask_m,
    )
    m.add_variables(
        lower=0,
        upper=inf,
        coords=RTeEY,
        name="AnnualTechnologyEmissionPenaltyByEmission",
        integer=False,
        mask=ep_mask,
    )
    m.add_variables(
        lower=0, upper=inf, coords=RTeY, name="AnnualTechnologyEmissionsPenalty", integer=False
    )
    m.add_variables(
        lower=0, upper=inf, coords=RTeY, name="DiscountedTechnologyEmissionsPenalty", integer=False
    )
    m.add_variables(lower=0, upper=inf, coords=REY, name="AnnualEmissions", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RE, name="ModelPeriodEmissions", integer=False)

    return m


def add_variables(ds: xr.Dataset, m: Model) -> Model:
    """Add all variables to the model

    Arguments
    ---------
    ds: xarray.Dataset
        The parameters dataset
    m: linopy.Model
        A linopy model

    Returns
    -------
    linopy.Model
    """
    RTeY = [ds.coords["REGION"], ds.coords["TECHNOLOGY"], ds.coords["YEAR"]]
    RY = [ds.coords["REGION"], ds.coords["YEAR"]]

    m = add_demand_variables(ds, m)
    # m = add_storage_variables(ds, m)
    m = add_capacity_variables(ds, m)
    m = add_activity_variables(ds, m)

    # Costing Variables

    m.add_variables(lower=0, upper=inf, coords=RTeY, name="CapitalInvestment", integer=False)
    m.add_variables(
        lower=0, upper=inf, coords=RTeY, name="DiscountedCapitalInvestment", integer=False
    )
    m.add_variables(lower=0, upper=inf, coords=RTeY, name="SalvageValue", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RTeY, name="DiscountedSalvageValue", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RTeY, name="OperatingCost", integer=False)
    m.add_variables(lower=0, upper=inf, coords=RTeY, name="DiscountedOperatingCost", integer=False)
    m.add_variables(
        lower=0, upper=inf, coords=RTeY, name="AnnualVariableOperatingCost", integer=False
    )
    m.add_variables(lower=0, upper=inf, coords=RTeY, name="AnnualFixedOperatingCost", integer=False)
    m.add_variables(
        lower=0, upper=inf, coords=RTeY, name="TotalDiscountedCostByTechnology", integer=False
    )
    m.add_variables(lower=0, upper=inf, coords=RY, name="TotalDiscountedCost", integer=False)
    coords = [ds.coords["REGION"]]
    m.add_variables(
        lower=0, upper=inf, coords=coords, name="ModelPeriodCostByRegion", integer=False
    )

    # Reserve Margin

    m.add_variables(
        lower=0, upper=inf, coords=RY, name="TotalCapacityInReserveMargin", integer=False
    )
    coords = [ds.coords["REGION"], ds.coords["TIMESLICE"], ds.coords["YEAR"]]
    m.add_variables(
        lower=0, upper=inf, coords=coords, name="DemandNeedingReserveMargin", integer=False
    )

    # RE Gen Target

    m.add_variables(lower=-inf, upper=inf, coords=RY, name="TotalREProductionAnnual", integer=False)
    m.add_variables(
        lower=-inf, upper=inf, coords=RY, name="RETotalProductionOfTargetFuelAnnual", integer=False
    )

    m = add_emission_variables(ds, m)

    return m
