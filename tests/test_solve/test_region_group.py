import numpy as np

from tz.osemosys import (
    Commodity,
    Impact,
    Model,
    OperatingMode,
    Region,
    RegionGroup,
    Technology,
    TimeDefinition,
)


def test_region_grouping_include():
    """
    In this test 2 regions are assigned to a region group and an RE target of 50% added for the
    defined region group.
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
    regions = [Region(id="R1"), Region(id="R2")]
    impacts = [Impact(id="CO2")]
    regionsgroup = [
        RegionGroup(id="GBL", include_in_region_group={"R1": {"*": True}, "R2": {"*": True}})
    ]
    commodities = [Commodity(id="ELEC", demand_annual=25, include_in_joint_renewable_target=True)]
    region_group_renewable_production_target = 0.5
    technologies = [
        Technology(
            id="coal",
            operating_life=10,  # years
            capex=200,
            include_in_joint_renewable_target=False,
            operating_modes=[
                OperatingMode(
                    id="generation",
                    opex_variable=0.0,
                    output_activity_ratio={"ELEC": 1.0},
                    emission_activity_ratio={"CO2": 0.1},
                )
            ],
        ),
        Technology(
            id="solar-pv",
            operating_life=10,  # years
            capex=200,
            include_in_joint_renewable_target=True,
            operating_modes=[
                OperatingMode(
                    id="generation",
                    opex_variable=10.0,
                    output_activity_ratio={"ELEC": 1.0},
                    emission_activity_ratio={"CO2": 0.0},
                )
            ],
        ),
    ]

    model = Model(
        id="test-region-group-include",
        depreciation_method="straight-line",
        time_definition=time_definition,
        regionsgroup=regionsgroup,
        impacts=impacts,
        regions=regions,
        commodities=commodities,
        technologies=technologies,
        region_group_renewable_production_target=region_group_renewable_production_target,
    )

    model.solve(solver="highs")

    assert np.round(model._m.objective.value) == 11978


def test_region_grouping_exclude():
    """
    In this test neither regions are assigned to the region group with the RE target.
    Thus the model is less restricted and the objective value is lower than the test with region
    groups included.
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
    regions = [Region(id="R1"), Region(id="R2")]
    impacts = [Impact(id="CO2")]
    regionsgroup = [
        RegionGroup(id="GBL", include_in_region_group={"R1": {"*": False}, "R2": {"*": False}})
    ]
    commodities = [Commodity(id="ELEC", demand_annual=25, include_in_joint_renewable_target=True)]
    region_group_renewable_production_target = 0.5
    technologies = [
        Technology(
            id="coal",
            operating_life=10,  # years
            capex=200,
            include_in_joint_renewable_target=False,
            operating_modes=[
                OperatingMode(
                    id="generation",
                    opex_variable=0.0,
                    output_activity_ratio={"ELEC": 1.0},
                    emission_activity_ratio={"CO2": 0.1},
                )
            ],
        ),
        Technology(
            id="solar-pv",
            operating_life=10,  # years
            capex=200,
            include_in_joint_renewable_target=True,
            operating_modes=[
                OperatingMode(
                    id="generation",
                    opex_variable=10.0,
                    output_activity_ratio={"ELEC": 1.0},
                    emission_activity_ratio={"CO2": 0.0},
                )
            ],
        ),
    ]

    model = Model(
        id="test-region-group-exclude",
        depreciation_method="straight-line",
        time_definition=time_definition,
        regionsgroup=regionsgroup,
        impacts=impacts,
        regions=regions,
        commodities=commodities,
        technologies=technologies,
        region_group_renewable_production_target=region_group_renewable_production_target,
    )

    model.solve(solver="highs")

    assert np.round(model._m.objective.value) == 10000
