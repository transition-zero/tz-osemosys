from tz.osemosys import Commodity, Model, OperatingMode, Region, Technology, TimeDefinition


def test_growth_rate_floor():
    """
    In this model, we expect generators to be built at 1 GW for 2020 (i.e. the floor value) plus the
    allowed growth rate in the given year.
    In 2020, as there is no existing capacity, only the floor value can be built (1 GW).
    In 2021 the model can build the floor value plus the capacity from the previous year * the
    growth rate (0.2), 1 + 1 * 0.02 which gives 1.02 GW.
    In 2022 the floor value becomes 0, so only additional capacity can be installed according to the
     growth rate, gross capacity in 2021 (2.02 GW) * 0.03 = 0.0606 GW.

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
            capacity_additional_max_growth_rate={
                "*": {
                    2020: 0.01,
                    2021: 0.02,
                    2022: 0.03,
                    2023: 0.04,
                    2024: 0.05,
                    2025: 0.06,
                    2026: 0.07,
                    2027: 0.08,
                    2028: 0.09,
                    2029: 0.1,
                }
            },
            capacity_additional_max_floor={
                "*": {
                    2020: 1.0,
                    2021: 1.0,
                    2022: 0,
                    2023: 0,
                    2024: 0,
                    2025: 0,
                    2026: 0,
                    2027: 0,
                    2028: 0,
                    2029: 0,
                }
            },
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

    model.solve(solver="highs")

    assert model.solution.NewCapacity.sel(YEAR=2022, TECHNOLOGY="generator") == 0.0606
    assert model.solution.NewCapacity.sel(YEAR=2020, TECHNOLOGY="unmet-demand") == 99.0


def test_growth_rate_ceil():
    """
    In this model, a constant growth rate and floor value are used.
    Howevever, maximum new capacity of genertors is capped at 20GW.
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

    model.solve(solver="highs")

    assert model.solution.NewCapacity.sel(YEAR=2021, TECHNOLOGY="generator") == 15.0
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

    model.solve(solver="highs")

    assert model.solution.NewCapacity.sel(YEAR=2021, TECHNOLOGY="bad-generator") == 1.0
    assert model.solution.NewCapacity.sel(YEAR=2022, TECHNOLOGY="bad-generator") == 1.1
