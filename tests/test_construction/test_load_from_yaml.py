import yaml

from feo.osemosys.io.load_model import load_model
from feo.osemosys.utils import EnvVarLoader, substitute_factory, walk_dict
from tests.fixtures.paths import YAML_SAMPLE_PATHS


def test_env_var_parse(mock_env_var):
    blob = """
    myenvval_expr: $ENV{MYVAR} + $ENV{MYOTHERVAR}
    myval: ${MYVAR}
    """
    data = yaml.load(blob, Loader=EnvVarLoader)
    assert data["myenvval_expr"] == "5 + 37"


def test_var_parse():
    blob = """
    myref1: 42
    myref2: 10
    myxref: ${myref1}
    xref2:
      - a: 1
        b: 2
      - a: 1
        b: 2
      - a: ${myref2}
        b: 2
    """
    data = yaml.load(blob, Loader=yaml.SafeLoader)

    sub_functions = substitute_factory(data)

    for f in sub_functions:
        data = walk_dict(data, f)

    assert data["myxref"] == "42"
    assert data["xref2"][2]["a"] == "10"


def test_sample_construction():
    for path in YAML_SAMPLE_PATHS:
        print(path)
        load_model(path)
    assert False
