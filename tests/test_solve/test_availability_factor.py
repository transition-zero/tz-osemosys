from tz.osemosys import Commodity, Model, OperatingMode, Region, Technology, TimeDefinition

# Capacity is pinned at 10 GW (residual_capacity == capacity_gross_max) and
# CapacityToActivityUnit defaults to 1, so annual activity ceilings below are
# just `10 * factor`.
CAPACITY = 10


def _two_timeslice_time_definition():
    """A year split evenly between a 'D' and an 'N' timeslice."""
    return TimeDefinition(
        id="day-night",
        years=[2020],
        timeslices=["D", "N"],
        year_split={"D": 0.5, "N": 0.5},
    )


def _pinned_capacity_model(capacity_factor, availability_factor, model_id):
    """A fixed-capacity generator plus an expensive backstop, against demand it cannot meet.

    Demand far exceeds what ``generator`` can produce, and ``generator`` is far cheaper than
    ``unmet-demand``, so the solver always pushes ``generator`` to whatever ceiling the
    constraints allow -- which is exactly what these tests measure.
    """
    return Model(
        id=model_id,
        time_definition=_two_timeslice_time_definition(),
        regions=[Region(id="single-region")],
        commodities=[Commodity(id="electricity", demand_annual=100)],
        impacts=[],
        technologies=[
            Technology(
                id="generator",
                operating_life=20,
                capex=0.1,
                residual_capacity=CAPACITY,
                capacity_gross_max=CAPACITY,
                capacity_factor=capacity_factor,
                availability_factor=availability_factor,
                operating_modes=[
                    OperatingMode(
                        id="generation",
                        opex_variable=0.0,
                        output_activity_ratio={"electricity": 1.0},
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
                    )
                ],
            ),
        ],
    )


def _annual_activity(model, technology="generator"):
    model.solve(solver_name="highs")
    assert model._m.termination_condition == "optimal"
    return (
        model.solution["TotalTechnologyAnnualActivity"].sel(YEAR=2020, TECHNOLOGY=technology).item()
    )


def test_availability_factor_does_not_scale_sub_annual_capacity_factor():
    """CAb1 caps annual activity at ``AvailabilityFactor``, it does not scale CapacityFactor.

    The generator has a sub-annual capacity factor profile averaging 0.8
    (``0.5 * 1.0 + 0.5 * 0.6``) and an availability factor of 0.9. The two bounds apply
    independently, so the binding one is the capacity factor:

        annual activity <= CAPACITY * min(AvailabilityFactor, mean CapacityFactor)
                        == 10 * min(0.9, 0.8) == 8.0

    Previously CAb1 multiplied the two together, capping activity at ``10 * 0.8 * 0.9 == 7.2``
    and making it impossible for a technology to reach its own capacity factor whenever
    ``AvailabilityFactor < 1`` -- the infeasibility this constraint was changed to fix.
    """
    model = _pinned_capacity_model(
        capacity_factor={"D": 1.0, "N": 0.6},
        availability_factor=0.9,
        model_id="availability-factor-with-profile",
    )

    assert _annual_activity(model) == 8.0


def test_availability_factor_still_binds_when_below_capacity_factor():
    """The other side of the ``min``: AvailabilityFactor is still a real annual ceiling.

    With a flat capacity factor of 1.0, nothing competes with the availability factor, so it
    binds directly: ``10 * min(0.6, 1.0) == 6.0``. Guards against the (incorrect) reading that
    dropping CapacityFactor from CAb1 made AvailabilityFactor inert.
    """
    model = _pinned_capacity_model(
        capacity_factor=1.0,
        availability_factor=0.6,
        model_id="availability-factor-binding",
    )

    assert _annual_activity(model) == 6.0
