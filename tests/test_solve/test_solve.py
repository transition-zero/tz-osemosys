from pathlib import Path

import numpy as np
import pytest
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
        daily_time_brackets=[1, 2],
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
        id="simple-storage",
        time_definition=time_definition,
        regions=regions,
        commodities=commodities,
        impacts=impacts,
        storage=storage,
        technologies=technologies,
    )
    model.solve(solver_name="highs")

    assert model._m.termination_condition == "optimal"

    assert (
        model.solution.NewStorageCapacity.sel(
            YEAR=2020, REGION="single-region", STORAGE="bat-storage-daily"
        ).item()
        == 12.5
    )
    assert (
        model.solution.NetCharge.sel(
            YEAR=2020, REGION="single-region", STORAGE="bat-storage", TIMESLICE="D"
        )
        == 75
    )
    assert (
        model.solution.NetCharge.sel(
            YEAR=2020, REGION="single-region", STORAGE="bat-storage", TIMESLICE="N"
        )
        == 0
    )
    # test storage level recursion
    net = model.solution.NetCharge.stack(YRTS=["YEAR", "TIMESLICE"])
    level = model.solution.StorageLevel.stack(YRTS=["YEAR", "TIMESLICE"])
    xr.testing.assert_allclose(level, net.cumsum("YRTS").rename("StorageLevel"))

    # test storage level bounds
    assert (model.solution.StorageLevel >= -1e-6).all()
    assert (model.solution.StorageLevel <= model.solution.GrossStorageCapacity + 1e-6).all()


def test_simple_storage_daily_balance():
    """Simple daily storage balance with a non-uniform DaySplit.

    Two daily time brackets, D = 0.75 of the day, N = 0.25. Solar generates only in D,
    so storage must charge in D and discharge in N to meet night demand. With
    storage_balance_day, equal energy charged/discharged forces the discharge rate to be
    3x the charge rate (rate_D * 0.75 == rate_N * 0.25).
    """
    time_definition = TimeDefinition(
        id="t",
        years=[2020],
        seasons=[1],
        day_types=[1],
        daily_time_steps=[1, 2],
        timeslices=["D", "N"],
        timeslice_in_season={"D": 1, "N": 1},
        timeslice_in_daytype={"D": 1, "N": 1},
        timeslice_in_timebracket={"D": 1, "N": 2},
        year_split={"D": 0.75, "N": 0.25},
        day_split={1: 0.75, 2: 0.25},
    )
    commodities = [
        Commodity(id="electricity", demand_annual=100, demand_profile={"D": 0.5, "N": 0.5})
    ]
    technologies = [
        Technology(
            id="solar-pv",
            operating_life=1,
            capex=1,
            capacity_factor={"D": 1, "N": 0},
            operating_modes=[
                OperatingMode(id="generation", output_activity_ratio={"electricity": 1.0})
            ],
        ),
        Technology(
            id="bat-tech",
            operating_life=1,
            capex=1,
            operating_modes=[
                OperatingMode(
                    id="charge",
                    input_activity_ratio={"electricity": 1.0},
                    to_storage={"*": {"bat-storage": True}},
                ),
                OperatingMode(
                    id="discharge",
                    output_activity_ratio={"electricity": 1.0},
                    from_storage={"*": {"bat-storage": True}},
                ),
            ],
        ),
    ]
    storage = [
        Storage(
            id="bat-storage",
            capex=1,
            operating_life=1,
            residual_capacity=0,
            storage_balance_day=True,
            initial_level=0,
        )
    ]
    model = Model(
        id="storage-daily-nonuniform",
        time_definition=time_definition,
        regions=[Region(id="single-region")],
        commodities=commodities,
        impacts=[],
        storage=storage,
        technologies=technologies,
    )
    model.solve(solver_name="highs")
    assert model._m.termination_condition == "optimal"

    # storage charges in D exactly the energy it discharges in N, so the day nets to zero
    # (the daily balance). A wrong formulation would leave a non-zero net charge.
    net = model.solution.NetCharge.sel(REGION="single-region", YEAR=2020, STORAGE="bat-storage")
    assert net.sel(TIMESLICE="D").item() == pytest.approx(50, rel=1e-4)
    assert net.sel(TIMESLICE="N").item() == pytest.approx(-50, rel=1e-4)
    assert net.sel(TIMESLICE=["D", "N"]).sum().item() == pytest.approx(0, abs=1e-6)


def test_simple_storage_seasonal_balancing():
    """
    Model to test the functionality of the storage_balance_season tag.

    There are 2 seasons, one in which electricity is cheap to produce for one for one of the
    daytypes, and another season in which only expensive generation is available.

    Electricity is cheap to produce in daytype 1 (weekend) and more expensive in daytype 2 (weekday)
    hence the model is encouraged to use storage to shift power from the weekdays to the weekend.
    (see the capacity factor on the "cheap-gen" technology).
    """
    time_definition = TimeDefinition(
        id="years-only",
        years=range(2020, 2030),
        seasons=[1, 2],
        day_types=[1, 2],
        daily_time_steps=[1],
        timeslices=["S1D1", "S1D2", "S2D1", "S2D2"],
        timeslice_in_season={"S1D1": 1, "S1D2": 1, "S2D1": 2, "S2D2": 2},
        timeslice_in_daytype={"S1D1": 1, "S1D2": 2, "S2D1": 1, "S2D2": 2},
        timeslice_in_timebracket={"S1D1": 1, "S1D2": 1, "S2D1": 1, "S2D2": 1},
        year_split={"S1D1": 0.143, "S1D2": 0.357, "S2D1": 0.143, "S2D2": 0.357},
        days_in_day_type={
            1: {1: {"*": 2}, 2: {"*": 5}},
            2: {1: {"*": 2}, 2: {"*": 5}},
        },  # {season:{day_type:{year:int}}}
    )
    regions = [Region(id="single-region")]
    commodities = [
        Commodity(
            id="electricity",
            demand_annual=25,
            demand_profile={"S1D1": 0.143, "S1D2": 0.357, "S2D1": 0.143, "S2D2": 0.357},
        )
    ]
    impacts = []
    technologies = [
        Technology(
            id="expensive-gen",
            operating_life=1,  # years
            capex=100,
            operating_modes=[
                OperatingMode(
                    id="generation",
                    opex_variable={
                        "*": {
                            "*": 100,
                        }
                    },
                    output_activity_ratio={"electricity": 1.0},
                )
            ],
        ),
        Technology(
            id="cheap-gen",
            operating_life=10,
            capex=0.01,
            capacity_factor={"S1D1": 1.0, "S1D2": 0.0, "S2D1": 0.0, "S2D2": 0.0},
            operating_modes=[
                OperatingMode(
                    id="generation",
                    output_activity_ratio={"electricity": 1.0},
                )
            ],
        ),
        Technology(
            id="bat-tech",
            operating_life=10,
            capex=0.01,
            operating_modes=[
                OperatingMode(
                    id="charge",
                    input_activity_ratio={"electricity": 1.0},
                    to_storage={"*": {"bat-storage": True}},
                ),
                OperatingMode(
                    id="discharge",
                    output_activity_ratio={"electricity": 1.0},
                    from_storage={"*": {"bat-storage": True}},
                ),
            ],
        ),
    ]
    storage = [
        Storage(
            id="bat-storage",
            capex=10,
            operating_life=10,
            residual_capacity=0,
            storage_balance_season=True,
            initial_level=0,
        ),
    ]
    model = Model(
        id="simple-storage-seasonal-balancing",
        time_definition=time_definition,
        regions=regions,
        commodities=commodities,
        impacts=impacts,
        storage=storage,
        technologies=technologies,
    )
    model.solve(solver_name="highs")

    assert model._m.termination_condition == "optimal"

    assert (
        model.solution.NewStorageCapacity.sel(
            YEAR=2020, REGION="single-region", STORAGE="bat-storage"
        ).item()
        == 8.925
    )
    assert (
        model.solution.NewStorageCapacity.sel(
            YEAR=2021, REGION="single-region", STORAGE="bat-storage"
        ).item()
        == 0.0
    )
    # storage charges in the cheap weekend daytype (S1D1) and discharges the same energy in
    # the expensive weekday daytype (S1D2), so the season nets to zero (the seasonal balance).
    # A wrong formulation would leave a non-zero net charge.
    net = model.solution.NetCharge.sel(REGION="single-region", YEAR=2020, STORAGE="bat-storage")
    assert net.sel(TIMESLICE="S1D1").item() == pytest.approx(8.925, rel=1e-4)
    assert net.sel(TIMESLICE="S1D2").item() == pytest.approx(-8.925, rel=1e-4)
    assert net.sel(TIMESLICE=["S1D1", "S1D2"]).sum().item() == pytest.approx(0, abs=1e-6)


def test_simple_storage_max_hours():
    """
    max_hours is the number of clock hours to fully charge/discharge at maximum power, so the
    max power is P_max = GrossStorageCapacity / max_hours [energy/hr].
    RateOfStorageCharge/Discharge are annualised (PJ/yr): power = Rate / HOURS_IN_YEAR.
    Imposing physical power <= P_max gives the binding relationship
        RateOfStorageCharge/Discharge <= GrossStorageCapacity * HOURS_IN_YEAR / max_hours.
    A simple model that forces the storage to charge fast so the power rating binds:
    - 1 season, 1 daytype, 2 brackets. T1 represents just 12 clock-hours of the year
      (year_split = 12/8760); T2 is the remaining 8748 hours.
    - Solar (the only generator) is available ONLY in the short T1 window; all demand is in T2.
    - The storage must therefore charge its entire energy (demand = 1) during T1, giving a
      forced annualised charge rate of 1 / (12/8760) = 730.
    - With max_hours = 24 the power rating binds and drives the capacity to
        capacity = charge_rate * max_hours / HOURS_IN_YEAR = 730 * 24 / 8760 = 2.0.
      Intuitively: a 24-hour storage that can only charge for 12 hours reaches half its rated
      capacity, so it needs twice the capacity of the energy it must store.
    """
    charge_window_hours = 12
    max_hours = 24
    year_split = {"T1": charge_window_hours / 8760, "T2": (8760 - charge_window_hours) / 8760}

    time_definition = TimeDefinition(
        id="years-only",
        years=range(2020, 2025),
        seasons=[1],
        day_types=[1],
        daily_time_brackets=[1, 2],
        timeslices=["T1", "T2"],
        timeslice_in_season={"T1": 1, "T2": 1},
        timeslice_in_daytype={"T1": 1, "T2": 1},
        timeslice_in_timebracket={"T1": 1, "T2": 2},
        year_split=year_split,
    )
    regions = [Region(id="single-region")]
    commodities = [
        # all demand falls in T2, when solar is unavailable
        Commodity(id="electricity", demand_annual=1, demand_profile={"T1": 0.0, "T2": 1.0})
    ]
    impacts = []
    technologies = [
        Technology(
            id="solar-pv",
            operating_life=100,
            capex=1,
            capacity_factor={"T1": 1, "T2": 0},  # solar only in the short T1 charge window
            operating_modes=[
                OperatingMode(
                    id="generation",
                    opex_variable=0,
                    output_activity_ratio={"electricity": 1.0},
                )
            ],
        ),
        Technology(
            id="bat-tech",
            operating_life=100,
            capex=0.01,
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
            max_hours=max_hours,
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

    energy_capacity = model.solution.NewStorageCapacity.values.flatten()[0]  # bat-storage
    # NetCharge(T1) = YearSplit(T1) * charge_rate; charging is forced entirely into T1
    net_charge = model.solution.NetCharge.isel(YEAR=0).values.flatten()
    charge_rate = net_charge[0] / year_split["T1"]

    # the power rating binds: capacity is driven by the forced fast charge, not by energy alone
    assert energy_capacity == pytest.approx(2.0)
    assert charge_rate == pytest.approx(730.0)
    # the binding identity: charge_rate == capacity * HOURS_IN_YEAR / max_hours
    assert charge_rate == pytest.approx(energy_capacity * 8760 / max_hours)
    # storage charges its full energy in T1 and discharges it in T2
    assert net_charge[0] == pytest.approx(1.0)  # 2020, T1 (charge)
    assert net_charge[1] == pytest.approx(-1.0)  # 2020, T2 (discharge)


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
