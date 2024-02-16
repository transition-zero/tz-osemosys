import glob
from pathlib import Path

import numpy as np
import pandas as pd

from feo.osemosys.schemas import RunSpec

# Can run solely this test with:
# python -m pytest tests/test_compatability/test_otoole_roundtrip.py -k test_files_equality


def test_files_equality():
    root_dir = "examples/otoole_csvs/model_three_edited/"
    output_directory = "tests/otoole_compare/model_three_edited/"

    create_output_directory(output_directory)

    # uses the class method on the base class to instantiate itself
    run_spec_object = RunSpec.from_otoole(root_dir=root_dir)

    # Write output CSVs
    run_spec_object.to_otoole(output_directory=output_directory)

    comparison_files = glob.glob(output_directory + "*.csv")
    comparison_files = {Path(f).stem: f for f in comparison_files}

    original_files = glob.glob(root_dir + "*.csv")
    original_files = {Path(f).stem: f for f in original_files}

    check_files_equality(original_files, comparison_files)


def create_output_directory(output_directory):
    """
    Create output directory if it doesn't exist.
    """
    output_path = Path.cwd() / output_directory
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def check_files_equality(original_files, comparison_files):
    """
    Check if the files from original and comparison directories are equal.
    """
    for stem, original_file in original_files.items():
        try:
            original_df_sorted = (
                pd.read_csv(original_file)
                .sort_values(by=pd.read_csv(original_file).columns.tolist())
                .reset_index(drop=True)
            )
            comparison_df_sorted = (
                pd.read_csv(comparison_files[stem])
                .sort_values(by=pd.read_csv(comparison_files[stem]).columns.tolist())
                .reset_index(drop=True)
            )
            # Additional checks for specific cases
            if stem in ["EmissionsPenalty", "TotalAnnualMaxCapacityInvestment"]:
                original_df_sorted["VALUE"] = original_df_sorted["VALUE"].astype(float)
            if stem == "OperationalLife":
                original_df_sorted["VALUE"] = original_df_sorted["VALUE"].astype(np.int64)

            if "YEAR" in original_df_sorted.columns:
                original_df_sorted["YEAR"] = original_df_sorted["YEAR"].astype(np.int64)
            if "MODE_OF_OPERATION" in original_df_sorted.columns:
                original_df_sorted["MODE_OF_OPERATION"] = original_df_sorted[
                    "MODE_OF_OPERATION"
                ].astype(np.int64)

            assert original_df_sorted.equals(comparison_df_sorted), f"unequal files: {stem}"
        except AssertionError as e:
            print(f"Assertion Error: {e}")
            print("---------- original_df_sorted ----------")
            print(original_df_sorted.head(10))
            print("---------- comparison_df_sorted ----------")
            print(comparison_df_sorted.head(10))
            raise
