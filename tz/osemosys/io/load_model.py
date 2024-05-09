from glob import glob
from pathlib import Path

import yaml

from tz.osemosys import utils
from tz.osemosys.schemas import RunSpec


def load_cfg(*spec_files):
    """
    Instantiate an OSeMOSYS RunSpec from one or more yaml files.

    Parameters
    ----------
    *spec_files: *str
        One or more yaml files or directories from which to compose the RunSpec


    Returns
    -------
    run_spec: schemas.RunSpec
        The configured and validated RunSpec.


    # Features

    ## Composition

    `load_model` will load yaml data, merging multiple yaml files together.

        run_spec = load_model("my_model/technologies.yaml", "my_model/solar_pv.yaml")

    Directories will be automatically searched for yaml files to parse.

        run_spec = load_model("base/technologies.yaml", "my_model/solar_pv.yaml")

    ## Environment Variable Parsing

    Environment variables will be automatically parsed in yaml files.
    They should be denoted with `$ENV{<MYVAR>}`.

        # my_model.yaml
        discount_rate: $ENV{DISCOUNT_RATE}

    ## Variable cross-referencing

    Fields in the yaml composition can be cross-referenced.
    Fields should be denoted with `${<my.field>}`.
    Fields can be nested with dot-notation.

        technologies:
          gas:
            capacity_factor: 1.
          coal:
            capacity_factor: ${technologies.gas.capacity_factor}

    Fields can even be even across files.

        # gas.yaml
        technologies:
          gas:
            capacity_factor: 1.

        # coal.yaml
        technologies:
          coal:
            capacity_factory: ${technologies.gas.capacity_factor}

    ## Simple python expressions

    Simple python expressions can be parsed in data fields.
    List and dict comprehensions can be used, as well as simple mathematical operators (+-*/^),
    and basic built-in functions (zip,sum,min,max,range).

        regions: "[f'REGION-{char}' for char in ['abcd']]"

    Expressions can be combined with  environment variables and cross-referencing.

        years: "range(2020, $ENV{END_YEAR})"
        capex: "{yr:1*1.04^(yr - min(${years})) for yr in ${years}}"


    Examples
    -------
    run_spec = load_model("example/main.yaml","example/technologies.yaml")

    run_spec = load_model("technologies/", "models/my_model.yaml")

    run_spec = load_model("base_technologies.yaml", "models/my_model.yaml")


    """

    # load yaml
    spec_files = utils.maybe_flatten(
        [(glob(f + "/*.yaml") if Path(f).is_dir() else f) for f in spec_files]
    )

    cfg = {}
    for f in spec_files:
        cfg.update(yaml.load(open(f), Loader=utils.EnvVarLoader))

    # substitute variables denoted by ${var.subvar}
    substitute_functions = utils.substitute_factory(cfg)

    for f in substitute_functions:
        utils.walk_dict(cfg, f)

    # eval strings
    changes_made = True
    while changes_made:
        changes_made = utils.walk_dict(cfg, utils.maybe_eval_string)

    return cfg


def load_model(*spec_files):
    cfg = load_cfg(*spec_files)

    return RunSpec(**cfg)
