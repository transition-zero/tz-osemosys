import numpy as np

from tz.osemosys import Commodity, Model, OperatingMode, Region, Storage, Technology, TimeDefinition

EXAMPLE_YAML = "examples/utopia/main.yaml"


def test_model_construction_from_yaml():
    """
    Check Runspec can be converted to dataset
    """

    model = Model.from_yaml(EXAMPLE_YAML)

    model._build()

    model._m.solve()

    assert model._m.termination_condition == "optimal"
    assert np.round(model._m.objective.value) == 29044.0


def test_most_simple():
    model = Model(
        id="test-feasibility",
        time_definition=dict(id="years-only", years=range(2020, 2031)),
        regions=[dict(id="single-region")],
        commodities=[dict(id="electricity", demand_annual=25)],
        impacts=[],
        technologies=[
            dict(
                id="coal-gen",
                operating_life=2,
                capex=400,
                operating_modes=[
                    dict(
                        id="generation",
                        opex_variable=5,
                        output_activity_ratio={"electricity": 1},
                    )
                ],
            )
        ],
    )

    model._build()

    model._m.solve()

    assert model._m.termination_condition == "optimal"
    assert np.round(model._m.objective.value) == 45736.0


def test_simple_storage():

    time_definition = TimeDefinition(
        id="years-only",
        years=range(2020, 2030),
        seasons=[1],
        day_types=[1],
        daily_time_steps=[1, 2],
        timeslices=["D", "N"],
        timeslice_in_season={"D": 1, "N": 1},
        timeslice_in_daytype={"D": 1, "N": 1},
        timeslice_in_timebracket={"D": 1, "N": 2},
        year_split={"D": 0.5, "N": 0.5},
    )
    regions = [Region(id="single-region")]
    commodities = [
        Commodity(id="electricity", demand_annual=25, demand_profile={"D": 0.5, "N": 0.5})
    ]
    impacts = []
    technologies = [
        Technology(
            id="solar-pv",
            operating_life=2,  # years
            capex=10,
            capacity_factor={"D": 1, "N": 0},
            operating_modes=[
                OperatingMode(
                    id="generation", opex_variable=0.0, output_activity_ratio={"electricity": 1.0}
                )
            ],
        ),
        Technology(
            id="bat-tech",
            operating_life=3,
            capex=20,
            operating_modes=[
                OperatingMode(
                    id="charge",
                    opex_variable=0,
                    input_activity_ratio={"electricity": 1.0},
                    to_storage={"*": {"bat-storage": True}},
                ),
                OperatingMode(
                    id="discharge",
                    opex_variable=0,
                    output_activity_ratio={"electricity": 1.0},
                    from_storage={"*": {"bat-storage": True}},
                ),
            ],
        ),
    ]

    storage = [
        Storage(
            id="bat-storage",
            capex=0.01,
            operating_life=100,
            residual_capacity=0,
        )
    ]

    model = Model(
        id="simple-carbon-price",
        time_definition=time_definition,
        regions=regions,
        commodities=commodities,
        impacts=impacts,
        storage=storage,
        technologies=technologies,
    )

    model.solve()

    assert model.solution.NewStorageCapacity.values[0][0][0] == 12.5
    assert np.round(model.objective) == 3494.0


def test_simple_trade():
    """
    2 region model, both regions have electricity demand and are able to trade with each other, but
    generating capacity can be constructed with 0 capex in the first region (R1), and non-zero cost
    in the second region (R2).

    Trade capacity additions are limited so that R2 imports as much energy as it can from R1, and
    then installs its own generating capacity to make up any shortfall.
    """
    model = Model(
        id="test-trade",
        time_definition=dict(id="years-only", years=range(2020, 2031)),
        regions=[dict(id="R1"), dict(id="R2")],
        trade=[
            dict(
                id="electricity transmission",
                commodity="electricity",
                trade_routes={"R1": {"R2": {"*": True}}},
                capex={"R1": {"R2": {"*": 100}}},
                operational_life={"R1": {"R2": {"*": 2}}},
                trade_loss={"*": {"*": {"*": 0.1}}},
                residual_capacity={"R1": {"R2": {"*": 5}}},
                capacity_additional_max={"R1": {"R2": {"*": 5}}},
                cost_of_capital={"R1": {"R2": 0.1}},
                construct_region_pairs=True,
            )
        ],
        commodities=[dict(id="electricity", demand_annual=25)],
        impacts=[],
        technologies=[
            dict(
                id="coal-gen",
                operating_life=2,
                capex={"R1": {"*": 0}, "R2": {"*": 400}},
                operating_modes=[
                    dict(
                        id="generation",
                        opex_variable=5,
                        output_activity_ratio={"electricity": 1},
                    )
                ],
            )
        ],
    )

    model.solve()

    assert model.solution["NetTrade"].values[0][2][0] == 15
    assert np.round(model._m.objective.value) == 28200.0
