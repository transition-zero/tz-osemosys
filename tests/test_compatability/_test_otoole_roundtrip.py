import glob
from pathlib import Path

import numpy as np
import pandas as pd

from feo.osemosys.schemas import RunSpec

root_dir = "data/model_three_edited/"
output_directory = "otoole_compare/model_three_edited/"

(Path.cwd() / output_directory).mkdir(parents=True, exist_ok=True)

# uses the class method on the base class to instantiate itself
run_spec_object = RunSpec.from_otoole(root_dir=root_dir)

run_spec_dataset = run_spec_object.to_xr_ds()

# type(run_spec_object) == <class RunSpec>
run_spec_object.to_otoole(output_directory=output_directory)

comparison_files = glob.glob(output_directory + "*.csv")
comparison_files = {Path(f).stem: f for f in comparison_files}

original_files = glob.glob(root_dir + "*.csv")
original_files = {Path(f).stem: f for f in original_files}


# let's check all our keys from our original data are in comparison
for stem in original_files.keys():
    print("checking stem:", stem)
    assert stem in comparison_files.keys(), f"missing stem: {stem}"

# now let's check that all data is equal
for stem in original_files.keys():
    try:
        # Read in and sort CSVs
        original_df_sorted = (
            pd.read_csv(original_files[stem])
            .sort_values(by=pd.read_csv(original_files[stem]).columns.tolist())
            .reset_index(drop=True)
        )
        comparison_df_sorted = (
            pd.read_csv(comparison_files[stem])
            .sort_values(by=pd.read_csv(comparison_files[stem]).columns.tolist())
            .reset_index(drop=True)
        )

        # TODO temporary casting for input data VALUEs
        if stem in ["EmissionsPenalty", "TotalAnnualMaxCapacityInvestment"]:
            original_df_sorted["VALUE"] = original_df_sorted["VALUE"].astype(float)
        if stem in ["OperationalLife"]:
            original_df_sorted["VALUE"] = original_df_sorted["VALUE"].astype(np.int64)

        if "YEAR" in original_df_sorted.columns:
            original_df_sorted["YEAR"] = original_df_sorted["YEAR"].astype(np.int64)
        if "MODE_OF_OPERATION" in original_df_sorted.columns:
            original_df_sorted["MODE_OF_OPERATION"] = original_df_sorted[
                "MODE_OF_OPERATION"
            ].astype(np.int64)

        if original_df_sorted.empty and comparison_df_sorted.empty:
            assert list(original_df_sorted.columns) == list(
                comparison_df_sorted.columns
            ), f"unequal files: {stem}"
        else:
            assert original_df_sorted.equals(comparison_df_sorted), f"unequal files: {stem}"

    except AssertionError as e:
        print(f"Assertion Error: {e}")
        print("---------- original_df_sorted ----------")
        print(original_df_sorted.head(10))
        print("---------- comparison_df_sorted ----------")
        print(comparison_df_sorted.head(10))
        input("Press Enter to continue...")

# Flag any additional files created in the comparison directory
for stem in comparison_files.keys():
    if stem not in original_files.keys():
        print("New file: ", stem)
        print(
            (
                pd.read_csv(comparison_files[stem])
                .sort_values(by=pd.read_csv(comparison_files[stem]).columns.tolist())
                .reset_index(drop=True)
            ).head(10)
        )
