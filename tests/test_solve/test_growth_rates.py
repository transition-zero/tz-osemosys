from tz.osemosys import Commodity, Model, OperatingMode, Region, Technology, TimeDefinition


def test_growth_rate_floor():
    """
    In this model, we expect generators to be built 10GW per year until 20% of gross capacity >10GW
    This should occur in 2026, when 20% of 60GW = 12GW.
    Meanwhile, unmet demand should be unconstrained to build to meet the demand of 100GW.
    """

    time_definition = TimeDefinition(id="yrs", years=range(2020, 2030))
    regions = [Region(id="single-region")]
    commodities = [Commodity(id="electricity", demand_annual=100)]
    impacts = []
    technologies = [
        Technology(
            id="generator",
            operating_life=20,  # years
            capex=0.1,
            capacity_additional_max_growth_rate=0.2,
            capacity_additional_max_floor=10,
            operating_modes=[
                OperatingMode(
                    id="generation", opex_variable=0.0, output_activity_ratio={"electricity": 1.0}
                )
            ],
        ),
        Technology(
            id="unmet-demand",
            operating_life=1,
            capex=0.1,
            operating_modes=[
                OperatingMode(
                    id="generation",
                    opex_variable=100.0,
                    output_activity_ratio={"electricity": 1.0},
                ),
            ],
        ),
    ]

    model = Model(
        id="simple-additional-capacity",
        time_definition=time_definition,
        regions=regions,
        commodities=commodities,
        impacts=impacts,
        technologies=technologies,
    )

    model.solve()

    assert model.solution.NewCapacity.sel(YEAR=2026, TECHNOLOGY="generator") == 12.0
    assert model.solution.NewCapacity.sel(YEAR=2020, TECHNOLOGY="unmet-demand") == 90.0


def test_growth_rate_ceil():
    """
    In this model, we expect generators to be built 10GW per year until 20% of gross capacity >10GW
    This should occur in 2023, when 50% of 30GW = 15GW.
    Howevever, after this, maximum new capacity of genertors should be capped at 20GW.
    Meanwhile, unmet demand should be unconstrained to build to meet the demand of 100GW.
    """

    time_definition = TimeDefinition(id="yrs", years=range(2020, 2030))
    regions = [Region(id="single-region")]
    commodities = [Commodity(id="electricity", demand_annual=100)]
    impacts = []
    technologies = [
        Technology(
            id="generator",
            operating_life=20,  # years
            capex=0.1,
            capacity_additional_max_growth_rate=0.5,
            capacity_additional_max_floor=10,
            capacity_additional_max=20,
            operating_modes=[
                OperatingMode(
                    id="generation", opex_variable=0.0, output_activity_ratio={"electricity": 1.0}
                )
            ],
        ),
        Technology(
            id="unmet-demand",
            operating_life=1,
            capex=0.1,
            operating_modes=[
                OperatingMode(
                    id="generation",
                    opex_variable=100.0,
                    output_activity_ratio={"electricity": 1.0},
                ),
            ],
        ),
    ]

    model = Model(
        id="simple-additional-capacity",
        time_definition=time_definition,
        regions=regions,
        commodities=commodities,
        impacts=impacts,
        technologies=technologies,
    )

    model.solve()

    assert model.solution.NewCapacity.sel(YEAR=2023, TECHNOLOGY="generator") == 15.0
    assert model.solution.NewCapacity.sel(YEAR=2024, TECHNOLOGY="generator") == 20.0


def test_growth_rate_min():
    """
    In this model, we add a 'bad generator', one that is expensive to build and run.
    The model would prefer to build 'generator' and fall back to 'unmet-demand'.
    We have set a min_growth_rate on 'bad-generator' of 0.1, and a residual capacity of 10GM
    So we expect new capacity in 2021 to be 1GW, and in 2022 to be 1.1GW.
    """

    time_definition = TimeDefinition(id="yrs", years=range(2020, 2030))
    regions = [Region(id="single-region")]
    commodities = [Commodity(id="electricity", demand_annual=100)]
    impacts = []
    technologies = [
        Technology(
            id="bad-generator",
            operating_life=20,  # years
            capex=100,
            capacity_additional_min_growth_rate=0.1,
            residual_capacity=10.0,
            operating_modes=[
                OperatingMode(
                    id="generation", opex_variable=10.0, output_activity_ratio={"electricity": 1.0}
                )
            ],
        ),
        Technology(
            id="generator",
            operating_life=20,  # years
            capex=0.1,
            capacity_additional_max_growth_rate=0.5,
            capacity_additional_max_floor=10,
            capacity_additional_max=20,
            operating_modes=[
                OperatingMode(
                    id="generation", opex_variable=0.0, output_activity_ratio={"electricity": 1.0}
                )
            ],
        ),
        Technology(
            id="unmet-demand",
            operating_life=1,
            capex=0.1,
            operating_modes=[
                OperatingMode(
                    id="generation",
                    opex_variable=10.0,
                    output_activity_ratio={"electricity": 1.0},
                ),
            ],
        ),
    ]

    model = Model(
        id="simple-additional-capacity",
        time_definition=time_definition,
        regions=regions,
        commodities=commodities,
        impacts=impacts,
        technologies=technologies,
    )

    model.solve()

    assert model.solution.NewCapacity.sel(YEAR=2021, TECHNOLOGY="bad-generator") == 1.0
    assert model.solution.NewCapacity.sel(YEAR=2022, TECHNOLOGY="bad-generator") == 1.1
