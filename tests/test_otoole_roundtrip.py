import glob
from pathlib import Path

import pandas as pd

from feo.osemosys.schemas import RunSpec

root_dir = "data/model_three/"
comparison_directory = "otoole_compare/model_three/"

(Path.cwd() / comparison_directory).mkdir(parents=True, exist_ok=True)

# uses the class method on the base class to instantiate itself
run_spec_object = RunSpec.from_otoole_csv(root_dir=root_dir, comparison_directory=comparison_directory)

# type(run_spec_object) == <class RunSpec>
run_spec_object.to_otoole_csv(comparison_directory=comparison_directory)

comparison_files = glob.glob(comparison_directory + "*.csv")
comparison_files = {Path(f).stem: f for f in comparison_files}

original_files = glob.glob(root_dir + "*.csv")
original_files = {Path(f).stem: f for f in original_files}


# let's check all our keys from our original data are in comparison
for stem in original_files.keys():
    print("checking stem:", stem)
    assert stem in comparison_files.keys(), f"missing stem: {stem}"

# now let's check that all data is equal
for stem in original_files.keys():
    assert pd.read_csv(original_files[stem]).equals(
        pd.read_csv(comparison_files[stem])
    ), f"unequal files: {stem}"
