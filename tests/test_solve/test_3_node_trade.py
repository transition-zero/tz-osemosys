import numpy as np

from tz.osemosys import Model


def test_3_node_trade_export():
    """
    Three regions (R1, R2, R3) with R1 as sole exporter to R2 and R3. R1 has a fixed
    surplus of 10 and no new capacity is allowed for trade or generation, so total
    export is capped at 10. Variable costs differ by region (R1=5, R2=10, R3=0; R3
    cheapest, R2 most expensive). Without a minimum per link then R1 would send
    all 10 on the expensive R2 and 0 on the cheaper R3. A min capacity factor of
    0.5 on each link requires at least 5 on each, so both links are used and the
    solution is 5+5. The test asserts Export 5 and 5 on the two links, confirming
    that the minimum-flow constraints are applied correctly.

    Parameters
    ----------
    Regions R1, R2, R3; one commodity and one technology. R1 residual 60 and demand 50
    (surplus 10), R2 and R3 residual and demand 50 each. Variable costs R1=5, R2=10,
    R3=0. Both links capacity 10 with capacity_factor_annual_min 0.5.
    capacity_additional_max 0 for trade and technology. Assertion: Export(R1→R2) and
    Export(R1→R3) equal to 5 for the solved year.
    """
    model = Model(
        id="test-3-node-trade",
        time_definition=dict(id="years-only", years=range(2020, 2031)),
        regions=[dict(id="R1"), dict(id="R2"), dict(id="R3")],
        trade=[
            dict(
                id="electricity transmission",
                commodity="electricity",
                trade_routes={
                    "R1": {"R2": {"*": True}, "R3": {"*": True}},
                },
                capex={
                    "R1": {"R2": {"*": 100}, "R3": {"*": 100}},
                },
                operating_life={
                    "R1": {"R2": {"*": 2}, "R3": {"*": 2}},
                },
                trade_loss={"*": {"*": {"*": 0}}},
                residual_capacity={
                    "R1": {"R2": {"*": 10}, "R3": {"*": 10}},
                },
                capacity_additional_max={
                    "R1": {"R2": {"*": 0}, "R3": {"*": 0}},
                },
                cost_of_capital={"R1": {"R2": 0.1, "R3": 0.1}},
                capacity_activity_unit_ratio=1,
                capacity_factor_annual_min={
                    "R1": {"R2": {"*": 0.5}, "R3": {"*": 0.5}},
                },
            )
        ],
        commodities=[dict(id="electricity", demand_annual=50)],
        impacts=[],
        technologies=[
            dict(
                id="coal-gen",
                operating_life=2,
                capex={"R1": {"*": 0}, "R2": {"*": 0}, "R3": {"*": 0}},
                residual_capacity={
                    "R1": {"*": 60},
                    "R2": {"*": 50},
                    "R3": {"*": 50},
                },
                capacity_additional_max={"R1": {"*": 0}, "R2": {"*": 0}, "R3": {"*": 0}},
                operating_modes=[
                    dict(
                        id="generation",
                        opex_variable={
                            "R1": {"*": 5},
                            "R2": {"*": 10},
                            "R3": {"*": 0},
                        },
                        output_activity_ratio={"electricity": 1},
                    )
                ],
            )
        ],
    )

    model.solve(solver_name="highs")

    export = model.solution["Export"].sel(YEAR=2020)
    r1_to_r2 = export.sel(REGION="R1", _REGION="R2").sum(dim=["TIMESLICE", "FUEL"]).item()
    r1_to_r3 = export.sel(REGION="R1", _REGION="R3").sum(dim=["TIMESLICE", "FUEL"]).item()
    assert np.round(r1_to_r2, 10) == 5
    assert np.round(r1_to_r3, 10) == 5
