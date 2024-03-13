import shutil

import pytest

from tz.osemosys.schemas.model import RunSpec


def test_model_construction():
    run_spec_object = RunSpec.from_otoole_csv(
        root_dir="examples/otoole_compat/input_csv/otoole-full-electricity/"
    )
    assert isinstance(run_spec_object, RunSpec)


@pytest.mark.skip(reason="fail cases not implemented?")
def test_model_construction_failcases(create_test_model_construction_failcases):
    folder_paths = create_test_model_construction_failcases
    with pytest.raises(ValueError) as e:  # noqa: F841
        for csv_folder in folder_paths:
            RunSpec.from_otoole_csv(root_dir=csv_folder)
    # Delete folders once used
    for csv_folder in folder_paths:
        shutil.rmtree(csv_folder)
