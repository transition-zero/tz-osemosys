from tz.osemosys import Commodity, Model, OperatingMode, Region, Technology, TimeDefinition


def test_min_capacity_factors():
    """
    In this model, we force the expensive 'unmet-demand' technology to be built at 10 GW per year,
     with operating life of 1, and then utilised with a capacity_factor_annual_min of 0.2 (20%).
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
        id="simple-min-capacity-factors",
        time_definition=time_definition,
        regions=regions,
        commodities=commodities,
        impacts=impacts,
        technologies=technologies,
    )

    model.solve(solver="highs")

    assert (
        model.solution["TotalTechnologyAnnualActivity"].sel(YEAR=2025, TECHNOLOGY="unmet-demand")
        == 2
    )
