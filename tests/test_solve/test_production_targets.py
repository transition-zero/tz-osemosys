import xarray as xr

from tz.osemosys import Model


def test_production_target():
    model = Model(
        id="test-production-targets",
        time_definition=dict(id="years-only", years=range(2020, 2025)),
        regions=[dict(id="single-region")],
        commodities=[
            dict(id="electricity", demand_annual=25),
            dict(id="hydrogen", demand_annual=25),
        ],
        impacts=[],
        technologies=[
            dict(
                id="tech-1",
                operating_life=2,
                capex=400,
                production_target_max={
                    "single-region": {
                        "electricity": {"2021": 0.3, "2022": 0.4},
                        "hydrogen": {"2023": 0.5, "2024": 0.6},
                    }
                },
                operating_modes=[
                    dict(
                        id="electricity-gen",
                        opex_variable=5,
                        output_activity_ratio={"electricity": 1},
                    ),
                    dict(
                        id="hydrogen-gen",
                        opex_variable=5,
                        output_activity_ratio={"hydrogen": 1},
                    ),
                ],
            ),
            dict(
                id="tech-2",
                operating_life=2,
                capex=800,
                production_target_min={
                    "single-region": {
                        "electricity": {"2023": 0.3, "2024": 0.4},
                        "hydrogen": {"2021": 0.5, "2022": 0.6},
                    }
                },
                operating_modes=[
                    dict(
                        id="electricity-gen",
                        opex_variable=10,
                        output_activity_ratio={"electricity": 1},
                    ),
                    dict(
                        id="hydrogen-gen",
                        opex_variable=10,
                        output_activity_ratio={"hydrogen": 1},
                    ),
                ],
            ),
        ],
    )

    model.solve(solver_name="highs", io_api="direct")
    assert model._m.termination_condition == "optimal"

    production = model.solution["ProductionByTechnology"].squeeze(drop=True)
    xr.testing.assert_equal(
        production.sel(TECHNOLOGY="tech-1", drop=True) / production.sum(dim="TECHNOLOGY"),
        xr.DataArray(
            [[1.0, 1.0], [0.3, 0.5], [0.4, 0.4], [0.7, 0.5], [0.6, 0.6]],
            coords=[[2020, 2021, 2022, 2023, 2024], ["electricity", "hydrogen"]],
            dims=["YEAR", "FUEL"],
        ),
    )
    xr.testing.assert_equal(
        production.sel(TECHNOLOGY="tech-2", drop=True) / production.sum(dim="TECHNOLOGY"),
        xr.DataArray(
            [[0.0, 0.0], [0.7, 0.5], [0.6, 0.6], [0.3, 0.5], [0.4, 0.4]],
            coords=[[2020, 2021, 2022, 2023, 2024], ["electricity", "hydrogen"]],
            dims=["YEAR", "FUEL"],
        ),
    )
