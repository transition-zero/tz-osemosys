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
