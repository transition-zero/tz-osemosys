from pathlib import Path

import pandas as pd

from feo.osemosys.schemas.time_definition import TimeDefinition

root_dir = "data/model_three/"
output_directory = "otoole_compare/model_three/"

timedef = TimeDefinition.from_otoole_csv(root_dir=root_dir)

timedef.to_otoole_csv(output_directory=output_directory)

for stem in TimeDefinition.otoole_stems:
    left = pd.read_csv(Path(root_dir) / (stem + ".csv"))
    right = pd.read_csv(Path(output_directory) / (stem + ".csv"))
    print("Compare:", stem, left.equals(right))
