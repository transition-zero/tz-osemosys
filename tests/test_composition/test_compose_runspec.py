import json
from tempfile import NamedTemporaryFile

from tz.osemosys import Model
from tz.osemosys.schemas.model import RunSpec
from tz.osemosys.utils import recursive_keys

PASSING_RUNSPEC_DEFINITIONS = dict(
    most_basic=dict(
        time_definition=dict(
            id="yearpart-daypart",
            years=range(2020, 2051),
            timeslices=["A", "B", "C", "D"],
        ),
        regions=[dict(id="GB")],
        commodities=[dict(id="COAL")],
        impacts=[dict(id="CO2e")],
        technologies=[
            dict(
                id="coal_powerplant",
                operating_life=10,
                capex=15,
                opex_fixed=1.5,
                operating_modes=[
                    dict(
                        id="mode_1",
                        opex_variable=1.5,
                        input_activity_ratio={"COAL": 1.0},
                        emission_activity_ratio={"CO2e": 100},
                    )
                ],
            ),
            dict(
                id="coal_mine",
                operating_life=10,
                capex=15,
                opex_fixed=1.5,
                operating_modes=[
                    dict(id="mode_1", opex_variable=1.5, output_activity_ratio={"COAL": 1.0})
                ],
            ),
        ],
    ),
    most_basic_with_storage=dict(
        time_definition=dict(
            id="yearpart-daypart",
            years=range(2020, 2051),
            timeslices=["A", "B", "C", "D"],
        ),
        regions=[dict(id="GB")],
        commodities=[dict(id="COAL")],
        impacts=[dict(id="CO2e")],
        technologies=[
            dict(
                id="coal_powerplant",
                operating_life=10,
                capex=15,
                opex_fixed=1.5,
                operating_modes=[
                    dict(
                        id="mode_1",
                        opex_variable=1.5,
                        input_activity_ratio={"COAL": 1.0},
                        emission_activity_ratio={"CO2e": 100},
                        to_storage={"*": {"STO": 1}},
                        from_storage={"*": {"STO": 1}},
                    )
                ],
            ),
            dict(
                id="coal_mine",
                operating_life=10,
                capex=15,
                opex_fixed=1.5,
                operating_modes=[
                    dict(id="mode_1", opex_variable=1.5, output_activity_ratio={"COAL": 1.0})
                ],
            ),
        ],
        storage=[
            dict(
                id="STO",
                capex={"*": {"*": 100}},
                operating_life={"*": 10},
            )
        ],
    ),
)


def test_compose_runspec():
    for name, data in PASSING_RUNSPEC_DEFINITIONS.items():
        spec = RunSpec(id=name, **data)
        spec.compose()

        # check one param
        capex = [k for k in recursive_keys(spec.technologies[0].capex.data)]
        for region in spec.regions:
            assert region.id in [k[0] for k in capex]
        for year in spec.time_definition.years:
            assert str(year) in [k[1] for k in capex]

        # check the operating mode
        op_mode_1 = spec.technologies[0].operating_modes[0]
        input_activity_ratio = [k for k in recursive_keys(op_mode_1.input_activity_ratio.data)]
        for region in spec.regions:
            assert region.id in [k[0] for k in input_activity_ratio]
        for commodity in spec.commodities:
            assert commodity.id in [k[1] for k in input_activity_ratio]
        for year in spec.time_definition.years:
            assert str(year) in [k[2] for k in input_activity_ratio]


def test_model_roundtrip():
    tmp = NamedTemporaryFile()
    for name, params in PASSING_RUNSPEC_DEFINITIONS.items():
        model = Model(id=name, **params)
        json.dump(model.model_dump(), open(tmp.name, "w"))
        model_recovered = Model(**json.load(open(tmp.name)))

        assert model == model_recovered
