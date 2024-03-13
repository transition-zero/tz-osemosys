import numpy as np

from tz.osemosys import Model

EXAMPLE_YAML = "examples/utopia/main.yaml"


def test_model_construction_from_yaml():
    """
    Check Runspec can be converted to dataset
    """

    model = Model.from_yaml(EXAMPLE_YAML)

    model._build()

    model._m.solve()

    assert model._m.termination_condition == "optimal"
    assert np.round(model._m.objective.value) == 10753472.0


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
