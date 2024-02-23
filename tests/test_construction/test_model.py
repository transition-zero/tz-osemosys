import shutil

import pytest

from feo.osemosys.schemas.model import RunSpec


@pytest.mark.skip(reason="implemented upstream")
def test_model_construction():
    run_spec_object = RunSpec.from_otoole(root_dir="examples/otoole_csvs/otoole-full-electricity/")
    assert isinstance(run_spec_object, RunSpec)


@pytest.mark.skip(reason="implemented upstream")
def test_model_construction_failcases(create_test_model_construction_failcases):
    folder_paths = create_test_model_construction_failcases
    with pytest.raises(ValueError) as e:  # noqa: F841
        for csv_folder in folder_paths:
            RunSpec.from_otoole(root_dir=csv_folder)
    # Delete folders once used
    for csv_folder in folder_paths:
        shutil.rmtree(csv_folder)
