from tz.osemosys.io.load_model import load_model

EXAMPLE_YAML = "/home/dwelsby/repos/tz-osemosys/examples/utopia"


def test_to_xr_ds():
    """
    Check Runspec can be converted to dataset
    """

    run_spec_object = load_model(EXAMPLE_YAML)
    run_spec_object.to_xr_ds()
