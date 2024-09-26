import yaml

from tests.fixtures.paths import YAML_SAMPLE_PATHS
from tz.osemosys.io.load_model import load_model
from tz.osemosys.utils import EnvVarLoader, maybe_eval_string, substitute_factory, walk_dict


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
    myref2: 10.0
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
        walk_dict(data, f)

    assert data["myxref"] == 42
    assert data["xref2"][2]["a"] == 10.0


def test_expression_parse():
    blob = """
    a: '[el for el in  range(10)]'
    b: sum(range(3))
    c: max([4,5,6])
    d: min([4,5,6])
    e: '{k:v for k,v in zip(["x","y","z"],[1,2,3])}'
    f: '{k:k+1 for k in range(3)}'
    """
    data = yaml.load(blob, Loader=yaml.SafeLoader)

    walk_dict(data, maybe_eval_string)
    assert isinstance(data["a"], list)
    assert data["b"] == 3
    assert data["c"] == 6
    assert data["d"] == 4
    assert isinstance(data["e"], dict)
    assert data["e"]["x"] == 1
    assert data["f"][0] == 1


def test_sample_construction():
    for path in YAML_SAMPLE_PATHS:
        load_model(path)
