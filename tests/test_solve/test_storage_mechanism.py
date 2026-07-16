import pytest
import xarray as xr

from tz.osemosys import Commodity, Model, OperatingMode, Region, Storage, Technology, TimeDefinition

HOURS_IN_YEAR = 8760


# ======================================================================================
# Model builders and shared assertions
# ======================================================================================
def assert_storage_invariants(model):
    """Properties true for ANY valid storage solution, independent of the formulation."""
    assert model._m.termination_condition == "optimal"
    sol = model.solution

    # StorageLevel is the running cumulative sum of NetCharge (the recursion constraint)
    net = sol.NetCharge.stack(YRTS=["YEAR", "TIMESLICE"])
    level = sol.StorageLevel.stack(YRTS=["YEAR", "TIMESLICE"])
    xr.testing.assert_allclose(level, net.cumsum("YRTS").rename("StorageLevel"))

    # storage level never goes negative and never exceeds installed gross capacity
    assert (sol.StorageLevel >= -1e-6).all()
    assert (sol.StorageLevel <= sol.GrossStorageCapacity + 1e-6).all()


def _battery_tech(operating_life, capex, opex_variable=None, storage="bat-storage"):
    """A technology that charges and discharges electricity in/out of ``storage``.

    ``opex_variable`` is passed through only when given, so callers that omit it keep the
    schema default.
    """
    extra = {} if opex_variable is None else {"opex_variable": opex_variable}
    return Technology(
        id="bat-tech",
        operating_life=operating_life,
        capex=capex,
        operating_modes=[
            OperatingMode(
                id="charge",
                input_activity_ratio={"electricity": 1.0},
                to_storage={"*": {storage: True}},
                **extra,
            ),
            OperatingMode(
                id="discharge",
                output_activity_ratio={"electricity": 1.0},
                from_storage={"*": {storage: True}},
                **extra,
            ),
        ],
    )


def _two_bracket_time_definition(split, years=(2020,), timeslices=("D", "N")):
    """A single representative day split into two daily time brackets.

    ``split`` is the weight of the first timeslice (bracket 1); the second takes the rest.
    ``year_split`` and ``day_split`` are set equal so the YearSplit- and DaySplit-based storage
    expressions see the same (possibly unequal) split -- required for the daily-balance
    constraint, since an omitted ``day_split`` would otherwise default to an equal split.
    """
    first, second = timeslices
    return TimeDefinition(
        id="-".join(str(t) for t in timeslices),
        years=list(years),
        seasons=[1],
        day_types=[1],
        daily_time_brackets=[1, 2],
        timeslices=list(timeslices),
        timeslice_in_season={first: 1, second: 1},
        timeslice_in_daytype={first: 1, second: 1},
        timeslice_in_timebracket={first: 1, second: 2},
        year_split={first: split, second: 1 - split},
        day_split={1: split, 2: 1 - split},
    )


def _daynight_model(
    time_def,
    storage_kwargs,
    solar_opex=0.0,
    storage_capex=1.0,
    storage_life=1,
    tech_life=1,
    model_id="storage-daynight",
):
    """Solar generates only during the day; night demand must be met from storage.

    Demand is split 50/50 between D and N, so night demand (= ``0.5 * demand_annual``)
    can only be served by discharging storage that was charged during the day.
    """
    return Model(
        id=model_id,
        time_definition=time_def,
        regions=[Region(id="single-region")],
        commodities=[
            Commodity(id="electricity", demand_annual=100, demand_profile={"D": 0.5, "N": 0.5})
        ],
        impacts=[],
        storage=[
            Storage(
                id="bat-storage",
                capex=storage_capex,
                operating_life=storage_life,
                residual_capacity=0,
                **storage_kwargs,
            )
        ],
        technologies=[
            Technology(
                id="solar-pv",
                operating_life=tech_life,
                capex=1,
                capacity_factor={"D": 1, "N": 0},
                operating_modes=[
                    OperatingMode(
                        id="generation",
                        opex_variable=solar_opex,
                        output_activity_ratio={"electricity": 1.0},
                    )
                ],
            ),
            _battery_tech(operating_life=tech_life, capex=1),
        ],
    )


def _annual_model(w_day, balance_year):
    """Two-year day/night model with expensive year-2 generation; 
    storage incentivised to carry energy forward but forbidden by the balance_year flag.
    """
    return _daynight_model(
        _two_bracket_time_definition(w_day, years=(2020, 2021)),
        {"storage_balance_year": True} if balance_year else {},
        solar_opex={"*": {2020: 0, 2021: 100}},
        storage_capex=0.01,
        storage_life=10,
        tech_life=10,
        model_id="storage-annual",
    )


def _seasonal_model(year_split, demand_profile):
    """Cheap generation only in one daytype; storage shifts it within the season."""
    time_def = TimeDefinition(
        id="seasonal",
        years=range(2020, 2030),
        seasons=[1, 2],
        day_types=[1, 2],
        daily_time_steps=[1],
        timeslices=["S1D1", "S1D2", "S2D1", "S2D2"],
        timeslice_in_season={"S1D1": 1, "S1D2": 1, "S2D1": 2, "S2D2": 2},
        timeslice_in_daytype={"S1D1": 1, "S1D2": 2, "S2D1": 1, "S2D2": 2},
        timeslice_in_timebracket={"S1D1": 1, "S1D2": 1, "S2D1": 1, "S2D2": 1},
        year_split=year_split,
        days_in_day_type={1: {1: {"*": 2}, 2: {"*": 5}}, 2: {1: {"*": 2}, 2: {"*": 5}}},
    )
    return Model(
        id="storage-seasonal",
        time_definition=time_def,
        regions=[Region(id="single-region")],
        commodities=[Commodity(id="electricity", demand_annual=25, demand_profile=demand_profile)],
        impacts=[],
        storage=[
            Storage(
                id="bat-storage",
                capex=10,
                operating_life=10,
                residual_capacity=0,
                storage_balance_season=True,
                initial_level=0,
            )
        ],
        technologies=[
            Technology(
                id="expensive-gen",
                operating_life=1,
                capex=100,
                operating_modes=[
                    OperatingMode(
                        id="generation",
                        opex_variable={"*": {"*": 100}},
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
                    OperatingMode(id="generation", output_activity_ratio={"electricity": 1.0})
                ],
            ),
            _battery_tech(operating_life=10, capex=0.01),
        ],
    )


def _max_hours_model(charge_window_hours, max_hours):
    """Solar available only in a short T1 window; storage must charge fast (see test docstring)."""
    time_def = _two_bracket_time_definition(
        charge_window_hours / HOURS_IN_YEAR, years=range(2020, 2025), timeslices=("T1", "T2")
    )
    return Model(
        id="storage-max-hours",
        time_definition=time_def,
        regions=[Region(id="single-region")],
        commodities=[
            Commodity(id="electricity", demand_annual=1, demand_profile={"T1": 0.0, "T2": 1.0})
        ],
        impacts=[],
        storage=[
            Storage(
                id="bat-storage",
                capex=0.01,
                operating_life=100,
                residual_capacity=0,
                max_hours=max_hours,
            )
        ],
        technologies=[
            Technology(
                id="solar-pv",
                operating_life=100,
                capex=1,
                capacity_factor={"T1": 1, "T2": 0},  # solar only in the short T1 charge window
                operating_modes=[
                    OperatingMode(
                        id="generation", opex_variable=0, output_activity_ratio={"electricity": 1.0}
                    )
                ],
            ),
            _battery_tech(operating_life=100, capex=0.01, opex_variable=0),
        ],
    )


# ======================================================================================
# Tests
# ======================================================================================
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
    time_definition = _two_bracket_time_definition(0.5, years=range(2020, 2030))
    technologies = [
        Technology(
            id="solar-pv",
            operating_life=2,  # years
            capex=10,
            capacity_factor={"D": 1, "N": 0},
            operating_modes=[
                OperatingMode(
                    id="generation",
                    # electricity cost rises by 10 each year, incentivising carrying energy forward
                    opex_variable={"*": {year: 10 * (year - 2020) for year in range(2020, 2030)}},
                    output_activity_ratio={"electricity": 1.0},
                )
            ],
        ),
        # one technology that can charge/discharge either storage
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
        Storage(id="bat-storage", capex=0.1, operating_life=100, residual_capacity=0),
    ]
    model = Model(
        id="simple-storage",
        time_definition=time_definition,
        regions=[Region(id="single-region")],
        commodities=[
            Commodity(id="electricity", demand_annual=25, demand_profile={"D": 0.5, "N": 0.5})
        ],
        impacts=[],
        storage=storage,
        technologies=technologies,
    )
    model.solve(solver_name="highs")
    assert_storage_invariants(model)

    sel = dict(YEAR=2020, REGION="single-region")
    assert model.solution.NewStorageCapacity.sel(STORAGE="bat-storage-daily", **sel).item() == 12.5
    net = model.solution.NetCharge.sel(STORAGE="bat-storage", **sel)
    assert net.sel(TIMESLICE="D").item() == 75
    assert net.sel(TIMESLICE="N").item() == 0


@pytest.mark.parametrize(
    "behaviour",
    [
        pytest.param({}, id="free"),
        pytest.param({"storage_balance_day": True}, id="daily-balance"),
    ],
)
@pytest.mark.parametrize(
    "w_day",
    [pytest.param(0.5, id="equal-split"), pytest.param(0.75, id="unequal-split")],
)
def test_storage_daynight(behaviour, w_day):
    """Free vs daily-balanced storage, under an equal vs unequal day/night split.

    Night demand can only be met from storage, so the storage charges the night's energy by
    day and fully discharges it at night. NetCharge (= 0.5 * demand_annual = 50) is
    split-invariant; the power rate (energy / time-fraction) is split-dependent, exposing any
    incorrect DaySplit/YearSplit conversion.
    """
    model = _daynight_model(_two_bracket_time_definition(w_day), behaviour)
    model.solve(solver_name="highs")
    assert_storage_invariants(model)

    net = model.solution.NetCharge.sel(REGION="single-region", YEAR=2020, STORAGE="bat-storage")
    net_d = net.sel(TIMESLICE="D").item()
    net_n = net.sel(TIMESLICE="N").item()

    # energy moved is split-invariant: charge the night's demand by day, release it at night
    assert net_d == pytest.approx(50.0, rel=1e-4)
    assert net_n == pytest.approx(-50.0, rel=1e-4)
    assert net.sum().item() == pytest.approx(0, abs=1e-6)  # the day nets to zero

    # power rate = energy / time-fraction, so it DOES depend on the split
    assert net_d / w_day == pytest.approx(50.0 / w_day, rel=1e-4)  # charge rate
    assert -net_n / (1 - w_day) == pytest.approx(50.0 / (1 - w_day), rel=1e-4)  # discharge rate

    # storage only needs to hold one night's worth of energy
    gross = model.solution.GrossStorageCapacity.sel(
        REGION="single-region", YEAR=2020, STORAGE="bat-storage"
    ).item()
    assert gross == pytest.approx(50.0, rel=1e-4)


@pytest.mark.parametrize(
    "w_day",
    [pytest.param(0.5, id="equal-split"), pytest.param(0.75, id="unequal-split")],
)
def test_storage_annual_balance(w_day):
    """storage_balance_year forces each year's NetCharge to sum to zero.

    Year-2 generation is expensive, so without the flag the model over-builds cheap year-1
    solar+storage and carries a full year of energy across the year boundary. The flag forbids
    that, forcing per-year balance. Both results are split-invariant.
    """
    # with the flag: every year's net charge is forced to zero (no cross-year carryover)
    model = _annual_model(w_day, balance_year=True)
    model.solve(solver_name="highs")
    assert_storage_invariants(model)
    net = model.solution.NetCharge.sel(REGION="single-region", STORAGE="bat-storage")
    for year in (2020, 2021):
        assert net.sel(YEAR=year).sum().item() == pytest.approx(0, abs=1e-6)

    # without the flag the constraint is genuinely binding: a full year of energy is carried
    # from the cheap year (2020) into the expensive year (2021)
    free = _annual_model(w_day, balance_year=False)
    free.solve(solver_name="highs")
    free_net = free.solution.NetCharge.sel(REGION="single-region", STORAGE="bat-storage")
    assert free_net.sel(YEAR=2020).sum().item() == pytest.approx(100.0, rel=1e-4)
    assert free_net.sel(YEAR=2021).sum().item() == pytest.approx(-100.0, rel=1e-4)


@pytest.mark.parametrize(
    "profile, expected_shift",
    [
        pytest.param(
            {"S1D1": 0.25, "S1D2": 0.25, "S2D1": 0.25, "S2D2": 0.25}, 6.25, id="equal-split"
        ),
        pytest.param(
            {"S1D1": 0.143, "S1D2": 0.357, "S2D1": 0.143, "S2D2": 0.357}, 8.925, id="unequal-split"
        ),
    ],
)
def test_storage_seasonal_balance(profile, expected_shift):
    """storage_balance_season forces charge == discharge within each season.

    Cheap generation is available only in the weekend daytype of season 1 (S1D1); storage shifts
    it into the weekday daytype (S1D2). The energy shifted equals the weekday demand
    (= demand_annual * profile[S1D2]), so the relevant "split" is the profile across daytypes.
    """
    # year_split matches the demand profile (fraction of year == fraction of demand per slice)
    model = _seasonal_model(year_split=profile, demand_profile=profile)
    model.solve(solver_name="highs")
    assert_storage_invariants(model)

    # storage is built once and sized to the energy it shifts (= weekday demand)
    cap = model.solution.NewStorageCapacity.sel(REGION="single-region", STORAGE="bat-storage")
    assert cap.sel(YEAR=2020).item() == pytest.approx(expected_shift, rel=1e-4)
    assert cap.sel(YEAR=2021).item() == pytest.approx(0.0, abs=1e-6)

    net = model.solution.NetCharge.sel(REGION="single-region", YEAR=2020, STORAGE="bat-storage")
    # charge in the cheap weekend daytype, discharge the same energy in the weekday daytype
    assert net.sel(TIMESLICE="S1D1").item() == pytest.approx(expected_shift, rel=1e-4)
    assert net.sel(TIMESLICE="S1D2").item() == pytest.approx(-expected_shift, rel=1e-4)
    # each season nets to zero (the seasonal balance)
    assert net.sel(TIMESLICE=["S1D1", "S1D2"]).sum().item() == pytest.approx(0, abs=1e-6)
    assert net.sel(TIMESLICE=["S2D1", "S2D2"]).sum().item() == pytest.approx(0, abs=1e-6)


@pytest.mark.parametrize(
    "charge_window_hours, max_hours, expected_capacity, expected_rate",
    [
        pytest.param(12, 24, 2.0, 730.0, id="window-12h"),
        pytest.param(6, 24, 4.0, 1460.0, id="window-6h"),
    ],
)
def test_storage_max_hours(charge_window_hours, max_hours, expected_capacity, expected_rate):
    """max_hours caps power: Rate <= GrossStorageCapacity * HOURS_IN_YEAR / max_hours.

    Solar is available only in a short T1 window while all demand is in T2, so the storage must
    charge its whole energy (=1) during T1 at a forced rate of 1 / YearSplit(T1). With max_hours
    short enough the power rating (not the energy) drives the capacity to
    charge_rate * max_hours / HOURS_IN_YEAR; a narrower window forces a higher rate and a larger
    capacity, which is the split-dependence being tested.
    """
    model = _max_hours_model(charge_window_hours, max_hours)
    model.solve(solver_name="highs")
    assert_storage_invariants(model)

    energy_capacity = model.solution.NewStorageCapacity.values.flatten()[0]  # bat-storage
    net_charge = model.solution.NetCharge.isel(YEAR=0).values.flatten()
    charge_rate = net_charge[0] / (charge_window_hours / HOURS_IN_YEAR)  # annualise the T1 charge

    # the power rating binds: capacity is driven by the forced fast charge, not by energy alone
    assert energy_capacity == pytest.approx(expected_capacity)
    assert charge_rate == pytest.approx(expected_rate)
    # the binding identity of the max_hours constraint
    assert charge_rate == pytest.approx(energy_capacity * HOURS_IN_YEAR / max_hours)
    # storage charges its full energy in T1 and discharges it in T2
    assert net_charge[0] == pytest.approx(1.0)  # T1 (charge)
    assert net_charge[1] == pytest.approx(-1.0)  # T2 (discharge)
