# ##################
# ### TECHNOLOGY ###
# ##################

class TechnologyOperatingMode(OSeMOSYSBase):
    # activity ratios & efficiency
    impact_activity_ratio: RegionCommodityYearData
    input_activity_ratio: RegionCommodityYearData
    output_activity_ratio: RegionCommodityYearData
    to_storage: str | None
    from_storage: str | None

    # financials
    opex_variable: RegionYearData

class Technology(OSeMOSYSBase):
    # unit conversions
    activity_unit_ratio: float # one unit of capacity used for a whole year

    # economic grain size, e.g. only 5000MW plants (forces MILP problem)
    capacity_addition_size: RegionData | None 

    # capacity, lifespan, availability
    availability_factor: RegionYearData 
    capacity_factor: RegionYearTimeData
    operating_life: RegionData

    # financials
    capex: RegionYearData
    opex_fixed: RegionYearData
    
    # operations
    operating_modes: List[TechnologyOperatingMode]

    # initial conditions
    residual_capacity: RegionYearData

    # constraints - capacity
    gross_capacity_max: RegionYearData                      # potential
    additional_capacity_max_ceil: RegionYearData            # Absolute value (ceil relative to growth rate)
    additional_capacity_max_floor: RegionYearData           # absolute value (floor relative to growth rate)
    additional_capacity_max_growth_rate: RegionYearData     # growth rate (<1.)
    gross_capacity_min: RegionYearData                      # must-build
    additional_capacity_min: RegionYearData                 # Absolute must-build value
    additional_capacity_min_growth_rate: RegionYearData     # growth rate (<1.)

    # constraints - activity
    annual_activity_max: RegionYearData
    annual_activity_min: RegionYearData
    total_activity_max: RegionData
    total_activity_min: RegionData



class TechnologyStorage(Technology):
    include_regions: List[str] | None
    exclude_regions: List[str] | None
    minimum_charge: RegionData
    initial_level: RegionData
    max_discharge_rate: RegionData
    max_charge_rate: RegionData



class TechnologyProduction(Technology):
    include_regions: List[str] | None
    exclude_regions: List[str] | None
    is_renewable: bool



class TechnologyTransmission(Technology):
    include_region_pairs: List[str] | None
    exclude_region_pairs: List[str] | None