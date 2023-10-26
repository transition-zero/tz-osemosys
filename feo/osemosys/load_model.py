import yaml
from osemosys import utils


def load_model(*spec_files):
    """
    Instantiate an OSeMOSYS RunSpec from one or more yaml files.

    Parameters
    ----------
    *spec_files: *str
        One or more yaml files defining the RunSpec.


    Returns
    -------
    run_spec: schemas.RunSpec
        The configured and validated RunSpec.


    Example
    -------
    run_spec = load_model("example/main.yaml","example/technologies.yaml")

    """

    # load yaml
    cfg = {}
    for f in spec_files:
        cfg.update(yaml.load(open(f)), Loader=yaml.SafeLoader)

    # substitute variables denoted by {{$var.subvar}}
    cfg = utils.walk_dict(cfg, utils.maybe_substitute_variables, cfg)

    # eval strings
    cfg = utils.walk_dict(cfg, utils.maybe_eval_string)
