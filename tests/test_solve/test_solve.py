import numpy as np

from tz.osemosys import Commodity, Model, OperatingMode, Region, Storage, Technology, TimeDefinition

EXAMPLE_YAML = "examples/utopia/main.yaml"


def test_model_construction_from_yaml():
    """
    Check Runspec can be converted to dataset
    """

    model = Model.from_yaml(EXAMPLE_YAML)

    model._build()

    model._m.solve(solver_name="highs")

    assert model._m.termination_condition == "optimal"
    assert np.round(model._m.objective.value) == 29044.0


def test_model_solve_from_otoole_csv():
    """
    Check that a model can be constructed and solved from a otoole style set of CSVs
    """

    path = "examples/otoole_compat/input_csv/otoole-simple-hydro"

    model = Model.from_otoole_csv(path)
    model.solve(solver="highs")

    assert model._m.termination_condition == "optimal"
    assert np.round(model._m.objective.value) == 5591653.0


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

    model._m.solve(solver_name="highs")

    assert model._m.termination_condition == "optimal"
    assert np.round(model._m.objective.value) == 45736.0


def test_simple_storage():
    """
    This model tests storage with 2 different behaviours, and has 2 different daily time brackets.
    The only generation technology is solar, which produces power during the day but not at night,
    so that storage must be used to meet demand.

    The first storage technology, 'bat-storage-daily', must charge and discharge by the same amount
    each day. The second storage technology, 'bat-storage', has no restrictions on it's charging and
    discharging behaviour.

    The cost to produce electricity increases over each year, so that there is an incentive to carry
    energy forward in years.

    bat-storage-daily is the cheaper technology so is used balance energy in the first few years,
    whereas as the cost of electricity increases, bat-storage is used to store energy for later
    years.
    """
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
                    id="generation",
                    opex_variable={
                        "*": {
                            2020: 0,
                            2021: 10,
                            2022: 20,
                            2023: 30,
                            2024: 40,
                            2025: 50,
                            2026: 60,
                            2027: 70,
                            2028: 80,
                            2029: 90,
                        }
                    },
                    output_activity_ratio={"electricity": 1.0},
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
                    to_storage={"*": {"bat-storage-daily": True}},
                ),
                OperatingMode(
                    id="discharge",
                    opex_variable=0,
                    output_activity_ratio={"electricity": 1.0},
                    from_storage={"*": {"bat-storage-daily": True}},
                ),
                OperatingMode(
                    id="charge2",
                    opex_variable=0,
                    input_activity_ratio={"electricity": 1.0},
                    to_storage={"*": {"bat-storage": True}},
                ),
                OperatingMode(
                    id="discharge2",
                    opex_variable=0,
                    output_activity_ratio={"electricity": 1.0},
                    from_storage={"*": {"bat-storage": True}},
                ),
            ],
        ),
    ]
    storage = [
        Storage(
            id="bat-storage-daily",
            capex=0.01,
            operating_life=100,
            residual_capacity=0,
            storage_balance_day=True,
        ),
        Storage(
            id="bat-storage",
            capex=0.1,
            operating_life=100,
            residual_capacity=0,
        ),
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
    model.solve(solver="highs")

    assert model.solution.NewStorageCapacity.values[0][0][0] == 12.5
    assert model.solution.NetCharge[0][1][0][0] == 75  # bat-storage 2020 Day charge
    assert model.solution.NetCharge[0][1][0][1] == 0  # bat-storage 2020 Night charge
    assert np.round(model.objective) == 8905.0


def test_simple_trade():
    """
    2 region model, both regions have electricity demand and are able to trade with each other, but
    generating capacity can be constructed with 0 capex in the first region (R1), and non-zero cost
    in the second region (R2).

    Trade capacity additions are limited so that R2 imports as much energy as it can from R1, and
    then installs its own generating capacity to make up any shortfall.

    Pseudo units and a capacity_activity_unit_ratio of 2 is used.
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
                operating_life={"R1": {"R2": {"*": 2}}},
                trade_loss={"*": {"*": {"*": 0.1}}},
                residual_capacity={"R1": {"R2": {"*": 5}}},
                capacity_additional_max={"R1": {"R2": {"*": 5}}},
                cost_of_capital={"R1": {"R2": 0.1}},
                construct_region_pairs=True,
                capacity_activity_unit_ratio=2,
            )
        ],
        commodities=[dict(id="electricity", demand_annual=50)],
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
                capacity_activity_unit_ratio=2,
            )
        ],
    )

    model.solve(solver="highs")

    assert model.solution["NetTrade"].values[0][2][0] == 30
    assert np.round(model._m.objective.value) == 30387.0


def test_simple_re_target():
    """
    This model has 2 generators, solar and coal, with identical parameters except for solar having
    double the capex and is tagged as renewable using the param include_in_joint_renewable_target.

    A 20% renewable target is set.
    """
    model = Model(
        id="test-feasibility",
        renewable_production_target=0.2,
        time_definition=dict(id="years-only", years=range(2020, 2031)),
        regions=[dict(id="single-region")],
        commodities=[
            dict(id="electricity", demand_annual=25, include_in_joint_renewable_target=True)
        ],
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
            ),
            dict(
                id="solar-gen",
                operating_life=2,
                capex=800,
                include_in_joint_renewable_target=True,
                operating_modes=[
                    dict(
                        id="generation",
                        opex_variable=5,
                        output_activity_ratio={"electricity": 1},
                    )
                ],
            ),
        ],
    )

    model._build()

    model._m.solve(solver_name="highs")

    assert model._m.termination_condition == "optimal"
    assert np.round(model._m.objective.value) == 54671.0
    assert model._m.solution["NewCapacity"][0][1][0] == 5  # i.e. solar new capacity
