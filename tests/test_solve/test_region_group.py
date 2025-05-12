import numpy as np

from tz.osemosys import Commodity, Model, OperatingMode, Region, RegionGroup, Technology, TimeDefinition, Impact


def test_region_grouping():

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
    regionsgroup = [RegionGroup(id="GBL",
                                include_in_region_group={"R1": {"*": True},
                                                         "R2": {"*": True}}
                            )
                        ]
    commodities = [Commodity(id="ELEC", demand_annual=25)]
    technologies = [
        Technology(
            id="coal",
            operating_life=10,  # years
            capex=200, 
            operating_modes=[
                OperatingMode(
                    id="generation",
                    opex_variable=0.0,
                    output_activity_ratio={"ELEC": 1.0},
                    emission_activity_ratio={"CO2": 0.1}
                )
            ],
        ),
    ]

    model = Model(
        id="test-region-group",
        depreciation_method="straight-line",
        time_definition=time_definition,
        regionsgroup=regionsgroup,
        impacts=impacts,
        regions=regions,
        commodities=commodities,
        technologies=technologies,
    )

    model.solve(solver="highs")