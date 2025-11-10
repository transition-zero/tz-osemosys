from pathlib import Path

import numpy as np
import xarray as xr

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
    model.solve(solver_name="highs")

    assert model._m.termination_condition == "optimal"
    assert np.round(model._m.objective.value) == 5591653.0


def test_model_save_netcdf(tmp_path: Path):
    model = Model.from_yaml(EXAMPLE_YAML)
    assert not hasattr(model, "_data")
    model.save_netcdf(tmp_path / "model.build.nc")
    assert hasattr(model, "_data")
    model.solve(solver_name="highs")
    assert model._solution is not None
    model.save_netcdf(tmp_path / "model.solve.nc")

    ds = xr.load_dataset(tmp_path / "model.solve.nc")
    for var in model._data:
        xr.testing.assert_identical(ds[var], model._data[var])
    for var in model._solution:
        xr.testing.assert_identical(ds[var], model._solution[var])


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
    model.solve(solver_name="highs")

    assert model.solution.NewStorageCapacity.values[0][0][0] == 12.5
    assert model.solution.NetCharge[0][1][0][0] == 75  # bat-storage 2020 Day charge
    assert model.solution.NetCharge[0][1][0][1] == 0  # bat-storage 2020 Night charge
    assert np.round(model.objective) == 8905.0


def test_simple_storage_max_hours():
    """
    This model tests the funcationality of max_hours in storage, which limits the ratio of storage
    capacity (in energy units) to maximum charge/discharge rate (in power units). Pseudo units and
    a capacity_activity_unit_ratio of 31.536 are used.

    The model includes 2 seasons and 4 daily time brackets of unequal length. The modelled hours
    are:
    - S1T1: 0-3
    - S1T2: 3-6
    - S1T3: 6-15
    - S1T4: 15-24

    Only one generator is available to meet demand, but is only available for the first 2 timeslices
    (S1T1 and S1T2), so that storage must be used to meet demand in the other timeslices.

    The demand in timeslices S1T3 and S1T4 is 0.1875. If storage where able to charge and discharge
    freely, it would only require 0.375 capacity to meet the combined demand of these timeslices.

    However, a max_hours of 12 is set, which means that for a given storage capacity, the fastest
    rate at which it can discharge or charge fully is 12 hours. Given for each day, storage is only
    able to charge for 6 hours, if the capacity were 0.375, over the first 2 timeslices it would
    only be able to charge 0.1875, which is not enough to meet the demand in S1T3 and S1T4. Hence
    the storage capacity must be at least 0.75 to meet the demand in S1T3 and S1T4.

    storage_balance_day cannot be set as true here as the model must charge for 6 hours and
    discharge for 18 hours, hence charge cannot equal discharge.
    """
    time_definition = TimeDefinition(
        id="years-only",
        years=range(2020, 2030),
        seasons=[1, 2],
        day_types=[1],
        daily_time_steps=[1, 2, 3, 4],  # 0-3, 3-6, 6-15, 15-24
        timeslices=["S1T1", "S1T2", "S1T3", "S1T4", "S2T1", "S2T2", "S2T3", "S2T4"],
        timeslice_in_season={
            "S1T1": 1,
            "S1T2": 1,
            "S1T3": 1,
            "S1T4": 1,
            "S2T1": 2,
            "S2T2": 2,
            "S2T3": 2,
            "S2T4": 2,
        },
        timeslice_in_daytype={
            "S1T1": 1,
            "S1T2": 1,
            "S1T3": 1,
            "S1T4": 1,
            "S2T1": 1,
            "S2T2": 1,
            "S2T3": 1,
            "S2T4": 1,
        },
        timeslice_in_timebracket={
            "S1T1": 1,
            "S1T2": 2,
            "S1T3": 3,
            "S1T4": 4,
            "S2T1": 1,
            "S2T2": 2,
            "S2T3": 3,
            "S2T4": 4,
        },
        year_split={
            "S1T1": 0.0625,
            "S1T2": 0.0625,
            "S1T3": 0.1875,
            "S1T4": 0.1875,
            "S2T1": 0.0625,
            "S2T2": 0.0625,
            "S2T3": 0.1875,
            "S2T4": 0.1875,
        },
    )
    regions = [Region(id="single-region")]
    commodities = [
        Commodity(
            id="electricity",
            demand_annual=1,
            demand_profile={
                "S1T1": 0.0625,
                "S1T2": 0.0625,
                "S1T3": 0.1875,
                "S1T4": 0.1875,
                "S2T1": 0.0625,
                "S2T2": 0.0625,
                "S2T3": 0.1875,
                "S2T4": 0.1875,
            },
        )
    ]
    impacts = []
    technologies = [
        Technology(
            id="solar-pv",
            operating_life=2,  # years
            capex=10,
            capacity_activity_unit_ratio=31.536,
            capacity_factor={
                "S1T1": 1,
                "S1T2": 1,
                "S1T3": 0,
                "S1T4": 0,
                "S2T1": 1,
                "S2T2": 1,
                "S2T3": 0,
                "S2T4": 0,
            },
            operating_modes=[
                OperatingMode(
                    id="generation",
                    opex_variable={
                        "*": {
                            "*": 0,
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
            max_hours=12,
            # storage_balance_day=True, # cannot be set as True here due to unequal year_splits
        ),
    ]
    model = Model(
        id="simple-storage-max-hours",
        time_definition=time_definition,
        regions=regions,
        commodities=commodities,
        impacts=impacts,
        storage=storage,
        technologies=technologies,
    )
    model.solve(solver_name="highs")

    assert model.solution.NewStorageCapacity.values[0][0][0] == 0.75  # 2020, bat-storage capacity
    assert model.solution.NetCharge.values[0][0][0][0] == 0.1875  # 2020, S1T1 net charge
    assert model.solution.NetCharge.values[0][0][0][2] == -0.1875  # 2020, S1T3 net charge
    assert np.round(model.objective) == 175.0


def test_simple_trade():
    """
    2 region model, both regions have electricity demand and are able to trade with each other, but
    generating capacity can be constructed with 0 capex in the first region (R1), and non-zero cost
    in the second region (R2).

    Trade capacity additions are limited so that R2 imports as much energy as it can from R1, and
    then installs its own generating capacity to make up any shortfall.

    A maximum availability_factor of 80% is set, so installed trade capacity can only be used for
    80% of the time.

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
                # the R2:R1 constraint below should not have any effect as only R1:R2 route is used
                availability_factor={"R1": {"R2": {"*": 0.8}}, "R2": {"R1": {"*": 0.1}}},
                activity_annual_max={"R1": {"R2": {"*": 24}}},
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

    model.solve(solver_name="highs")

    assert round(model.solution["NetTrade"].values[0][2][0][0], 10) == 24
    assert np.round(model._m.objective.value) == 34828.0


def test_simple_trade_forced_min_activity():
    """
    2 region model, both regions have electricity demand and are able to trade with each other, but
    generating capacity can be constructed with non-zero capex in the first region (R1), and 0 cost
    in the second region (R2).

    Trade capacity additions are forced so that R2 must import energy R1, and then installs its own
    generating capacity to make up any shortfall.

    A minimum annual capacity factor of 50% is set, so installed trade capacity must be used for
    50% of the time.

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
                capacity_activity_unit_ratio=2,
                capacity_factor_annual_min={"R1": {"R2": {"*": 0.5}}},
                activity_annual_min={"R1": {"R2": {"*": 5}}},
            )
        ],
        commodities=[dict(id="electricity", demand_annual=50)],
        impacts=[],
        technologies=[
            dict(
                id="coal-gen",
                operating_life=2,
                capex={"R1": {"*": 400}, "R2": {"*": 0}},
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

    model.solve(solver_name="highs")

    assert round(model.solution["NetTrade"].values[0][2][0][0], 10) == 5
    assert np.round(model._m.objective.value) == 53417.0


def test_trade_masking():
    model = Model(
        id="test-trade-masking",
        time_definition=dict(id="years-only", years=range(2020, 2022)),
        regions=[dict(id="R1"), dict(id="R2")],
        impacts=[],
        commodities=[dict(id="electricity", demand_annual=1.0)],
        technologies=[
            dict(
                id="gen",
                operating_modes=[dict(id="generation", output_activity_ratio={"electricity": 1})],
            )
        ],
        trade=[
            dict(
                id="electricity transmission",
                commodity="electricity",
                trade_routes={
                    "R1": {"R2": {2020: True}},
                    "R2": {"R1": {2021: True}},
                },
            )
        ],
    )

    model._build()
    # There should be no self-trade
    assert not model._m.variables["Import"].mask.sel(REGION="R1", _REGION="R1").any()
    assert not model._m.variables["Export"].mask.sel(REGION="R2", _REGION="R2").any()
    # Import mask should be transpose of Export mask in (REGION, _REGION) dims
    assert (
        model._m.variables["Export"].mask.sel(REGION="R1").to_numpy()
        == model._m.variables["Import"].mask.sel(_REGION="R1").to_numpy()
    ).all()
    assert (
        model._m.variables["Export"].mask.sel(REGION="R2").to_numpy()
        == model._m.variables["Import"].mask.sel(_REGION="R2").to_numpy()
    ).all()
    # Masking should also be applied on constraints
    assert model._m.constraints["EBa10_EnergyBalanceEachTS4_trn"].mask is not None


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


def test_simple_reserve_margin():
    """
    This model has a reserve margin requirement of 20%, with only one technology able to provide
    capacity towards the reserve margin (derated so that only 50% of the capacity contributes).
    The model checks that sufficient capacity is built to meet both demand and the reserve margin
    requirement.

    40 units of expensive-tech-with-reserve-margin are built and 60 units of
    cheap-tech-without-reserve-margin are built. 50% of 40 is 20, which meets the 20% reserve margin
    requirement on the 100 units of demand.
    """

    EXPENSIVE_TECH_WITH_RESERVE_MARGIN_CAPEX = 300
    EXPENSIVE_TECH_RESERVE_MARGIN_FACTOR = 0.5
    CHEAP_TECH_WITHOUT_RESERVE_MARGIN_CAPEX = 200

    RESERVE_MARGIN = 0.2
    DEMAND_ANNUAL = 100

    model = Model(
        id="test-reserve-margin",
        reserve_margin=RESERVE_MARGIN,
        time_definition=dict(id="years-only", years=range(2020, 2031)),
        regions=[dict(id="single-region")],
        commodities=[
            dict(
                id="electricity", demand_annual=DEMAND_ANNUAL, include_in_joint_reserve_margin=True
            )
        ],
        impacts=[],
        technologies=[
            dict(
                id="expensive-tech-with-reserve-margin",
                operating_life=5,
                capex=EXPENSIVE_TECH_WITH_RESERVE_MARGIN_CAPEX,
                include_in_joint_reserve_margin=EXPENSIVE_TECH_RESERVE_MARGIN_FACTOR,
                operating_modes=[
                    dict(
                        id="generation",
                        output_activity_ratio={"electricity": 1},
                    )
                ],
            ),
            dict(
                id="cheap-tech-without-reserve-margin",
                operating_life=5,
                capex=CHEAP_TECH_WITHOUT_RESERVE_MARGIN_CAPEX,
                include_in_joint_reserve_margin=0,
                operating_modes=[
                    dict(
                        id="generation",
                        output_activity_ratio={"electricity": 1},
                    )
                ],
            ),
        ],
    )

    model._build()

    model._m.solve(solver_name="highs")

    assert model._m.termination_condition == "optimal"
    assert (
        model._m.solution["NewCapacity"]
        .sel(YEAR=2020, TECHNOLOGY="expensive-tech-with-reserve-margin")
        .item()
        * EXPENSIVE_TECH_RESERVE_MARGIN_FACTOR
        == DEMAND_ANNUAL * RESERVE_MARGIN
    )
