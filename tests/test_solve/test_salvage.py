import numpy as np

from tz.osemosys import Commodity, Model, OperatingMode, Region, Technology, TimeDefinition


def test_salvage_value_straight_line():

    time_definition = TimeDefinition(id="salvage-1", years=range(2020, 2035))
    regions = [Region(id="R1")]
    commodities = [Commodity(id="ELEC", demand_annual=25)]
    technologies = [
        Technology(
            id="coal",
            operating_life=10,  # years
            capex=200,  # mn$/GW
            operating_modes=[
                OperatingMode(
                    id="generation",
                    opex_variable=0.0,
                    output_activity_ratio={"ELEC": 1.0},
                )
            ],
        ),
    ]

    model = Model(
        id="simple-salvage-1",
        depreciation_method="straight-line",
        time_definition=time_definition,
        impacts=[],
        regions=regions,
        commodities=commodities,
        technologies=technologies,
    )

    model.solve()

    assert np.round(model.solution.DiscountedSalvageValue.sum().values) == 1203.0


def test_salvage_value_sinking_fund():

    time_definition = TimeDefinition(id="salvage-1", years=range(2020, 2035))
    regions = [Region(id="R1")]
    commodities = [Commodity(id="ELEC", demand_annual=25)]
    technologies = [
        Technology(
            id="coal",
            operating_life=10,  # years
            capex=200,  # mn$/GW
            operating_modes=[
                OperatingMode(
                    id="generation",
                    opex_variable=0.0,
                    output_activity_ratio={"ELEC": 1.0},
                )
            ],
        ),
    ]

    model = Model(
        id="simple-salvage-1",
        depreciation_method="sinking-fund",
        time_definition=time_definition,
        impacts=[],
        regions=regions,
        commodities=commodities,
        technologies=technologies,
    )

    model.solve()

    assert np.round(model.solution.DiscountedSalvageValue.sum().values) == 1349.0
