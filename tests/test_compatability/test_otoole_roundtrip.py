import glob
from pathlib import Path

import pandas as pd

from tz.osemosys.schemas import RunSpec


def test_files_equality():
    """
    Check CSVs are equivalent after creating a RunSpec object from CSVs and writing to CSVs
    """

    # to be implemented
    # TODO

    EXCLUDE_STEMS = [
        "DiscountRateIdv",
        "DiscountRateStorage",
    ]

    root_dir = "examples/otoole_compat/input_csv/otoole-full-electricity-complete/"
    output_directory = "tests/otoole_compare/otoole-full-electricity-complete/"

    create_output_directory(output_directory)

    # uses the class method on the base class to instantiate itself
    run_spec_object = RunSpec.from_otoole_csv(root_dir=root_dir)

    # Write output CSVs
    run_spec_object.to_otoole_csv(output_directory=output_directory)

    comparison_files = glob.glob(output_directory + "*.csv")
    comparison_files = {
        Path(f).stem: f for f in comparison_files if Path(f).stem not in EXCLUDE_STEMS
    }

    original_files = glob.glob(root_dir + "*.csv")
    original_files = {Path(f).stem: f for f in original_files if Path(f).stem not in EXCLUDE_STEMS}

    check_files_equality(original_files, comparison_files, run_spec_object.otoole_cfg.empty_dfs)


def create_output_directory(output_directory):
    """
    Create output directory if it doesn't exist.
    """
    output_path = Path.cwd() / output_directory
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def check_files_equality(original_files, comparison_files, empty_dfs):
    """
    Check if the files from original and comparison directories are equal.
    """
    for stem, original_file in original_files.items():
        if stem in empty_dfs:
            continue
        original_cols = pd.read_csv(original_file).columns.tolist()
        try:
            original_df_sorted = (
                pd.read_csv(original_file)[original_cols]
                .sort_values(by=original_cols)
                .reset_index(drop=True)
            )
            # Cast all parameter values to floats
            if not stem.isupper():
                original_df_sorted["VALUE"] = original_df_sorted["VALUE"].astype(float)

            comparison_df_sorted = (
                pd.read_csv(comparison_files[stem])[original_cols]
                .sort_values(by=original_cols)
                .reset_index(drop=True)
            )
            # Cast all parameter values to floats
            if not stem.isupper():
                comparison_df_sorted["VALUE"] = comparison_df_sorted["VALUE"].astype(float)

            if original_df_sorted.empty and comparison_df_sorted.empty:
                assert list(original_df_sorted.columns) == list(
                    comparison_df_sorted.columns
                ), f"unequal files: {stem}"
            elif original_df_sorted.empty and not comparison_df_sorted.empty:
                pass
            else:
                assert original_df_sorted.equals(comparison_df_sorted), f"unequal files: {stem}"

        except AssertionError as e:
            print(f"Assertion Error: {e}")
            print("---------- original_df_sorted ----------")
            print(original_df_sorted)
            print("---------- comparison_df_sorted ----------")
            print(comparison_df_sorted)
            raise
