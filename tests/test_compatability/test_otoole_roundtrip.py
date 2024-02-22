import glob
from pathlib import Path

import pandas as pd
import pytest

from feo.osemosys.schemas import RunSpec


@pytest.mark.skip(reason="Many forthcoming changes with object construction.")
def test_files_equality():
    """
    Check CSVs are equivalent after creating a RunSpec object from CSVs and writing to CSVs
    """
    root_dir = "examples/otoole_csvs/otoole-full-electricity/"
    output_directory = "tests/otoole_compare/otoole-full-electricity/"

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
            # Cast all parameter values to floats
            if not stem.isupper():
                original_df_sorted["VALUE"] = original_df_sorted["VALUE"].astype(float)

            comparison_df_sorted = (
                pd.read_csv(comparison_files[stem])
                .sort_values(by=pd.read_csv(comparison_files[stem]).columns.tolist())
                .reset_index(drop=True)
            )
            # Cast all parameter values to floats
            if not stem.isupper():
                comparison_df_sorted["VALUE"] = comparison_df_sorted["VALUE"].astype(float)

            if original_df_sorted.empty and comparison_df_sorted.empty and stem != "TradeRoute":
                assert list(original_df_sorted.columns) == list(
                    comparison_df_sorted.columns
                ), f"unequal files: {stem}"
            elif original_df_sorted.empty and not comparison_df_sorted.empty:
                pass
            elif stem != "TradeRoute":
                assert original_df_sorted.equals(comparison_df_sorted), f"unequal files: {stem}"

        except AssertionError as e:
            print(f"Assertion Error: {e}")
            print("---------- original_df_sorted ----------")
            print(original_df_sorted.head(10))
            print("---------- comparison_df_sorted ----------")
            print(comparison_df_sorted.head(10))
            raise
