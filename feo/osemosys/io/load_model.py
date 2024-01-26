from glob import glob
from pathlib import Path

import yaml

from feo.osemosys import utils


def load_model(*spec_files):
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

    load_model will compose yaml data and directories of yaml, overwriting data from left to write.

    run_spec = load_model("base_technologies/", "my_model/solar_pv.yaml")

    ## Environment Variable Parsing

    ## Variable cross-referencing

    ## Simple python expressions

    ## Wildcards

    ##


    Examples
    -------
    run_spec = load_model("example/main.yaml","example/technologies.yaml")

    run_spec = load_model("technologies/", "models/my_model.yaml")

    run_spec = load_model("base_technologies.yaml", "models/my_model.yaml")


    """

    # load yaml
    spec_files = utils.flatten(
        [(glob(f + "/*.yaml") if Path(f).is_dir() else f) for f in spec_files]
    )

    cfg = {}
    for f in spec_files:
        cfg.update(yaml.load(open(f), Loader=utils.EnvVarLoader))

    # substitute variables denoted by ${var.subvar}
    substitute_functions = utils.substitute_factory(cfg)

    for f in substitute_functions:
        cfg = utils.walk_dict(cfg, f)

    # eval strings
    cfg = utils.walk_dict(cfg, utils.maybe_eval_string)
