import pytest

from feo.osemosys.schemas import RunSpec


@pytest.mark.skip(reason="Many forthcoming changes with object construction.")
def test_to_xr_ds():
    """
    Check Runspec can be converted to dataset
    """

    run_spec_object = RunSpec.from_otoole(root_dir="examples/otoole_csvs/otoole-full-electricity")
    run_spec_object.to_xr_ds()
