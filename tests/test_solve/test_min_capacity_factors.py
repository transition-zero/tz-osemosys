from tz.osemosys import Commodity, Model, OperatingMode, Region, Technology, TimeDefinition


def test_min_capacity_factors():
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
            capacity_additional_min=10,
            capacity_factor_annual_min=0.2,
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
    breakpoint()
    # assert model.solution.NewCapacity.sel(YEAR=2026, TECHNOLOGY="generator") == 12.0
    # assert model.solution.NewCapacity.sel(YEAR=2020, TECHNOLOGY="unmet-demand") == 90.0

