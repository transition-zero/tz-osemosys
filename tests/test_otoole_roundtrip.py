import glob
from pathlib import Path
import sys

import pandas as pd
import numpy as np

from feo.osemosys.schemas import RunSpec

root_dir = "data/model_three/"
comparison_directory = "otoole_compare/model_three/"

(Path.cwd() / comparison_directory).mkdir(parents=True, exist_ok=True)

# uses the class method on the base class to instantiate itself
run_spec_object = RunSpec.from_otoole(root_dir=root_dir)

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
    
    try:

        # Read in and sort CSVs
        original_df_sorted = (pd.read_csv(original_files[stem])
                            .sort_values(by=pd.read_csv(original_files[stem]).columns.tolist())
                            .reset_index(drop=True))
        comparison_df_sorted = (pd.read_csv(comparison_files[stem])
                                .sort_values(by=pd.read_csv(comparison_files[stem]).columns.tolist())
                                .reset_index(drop=True))
        
        #TODO temporary casting to float for input data (from model_three) which defaults to int once read
        if stem in ["EmissionsPenalty","TotalAnnualMaxCapacityInvestment"]:
            original_df_sorted["VALUE"] = original_df_sorted["VALUE"].astype(float)
        
        assert (original_df_sorted.equals(comparison_df_sorted)), f"unequal files: {stem}"

    except AssertionError as e:
        print(f"Assertion Error: {e}")
        print(f"---------- original_df_sorted ----------")
        print(original_df_sorted.head(10))
        print(f"---------- comparison_df_sorted ----------")
        print(comparison_df_sorted.head(10))
        input("Press Enter to continue...")

# Flag any additional files created in the comparison directory
for stem in comparison_files.keys():
    if stem not in original_files.keys():
        print("New file: ", stem)
        print((pd.read_csv(comparison_files[stem])
                                .sort_values(by=pd.read_csv(comparison_files[stem]).columns.tolist())
                                .reset_index(drop=True)).head(10))