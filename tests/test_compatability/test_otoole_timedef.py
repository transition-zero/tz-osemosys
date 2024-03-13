from pathlib import Path

import pandas as pd

from tests.fixtures.paths import OTOOLE_SAMPLE_PATHS
from tz.osemosys.schemas.time_definition import TimeDefinition


def test_otoole_roundtrip():
    comparison_root = "./tests/otoole_compare/"

    for path in OTOOLE_SAMPLE_PATHS:
        comparison_model = Path(path).name
        output_directory = Path(comparison_root + comparison_model)
        output_directory.mkdir(parents=True, exist_ok=True)

        timedef = TimeDefinition.from_otoole_csv(root_dir=path)

        timedef.to_otoole_csv(output_directory=output_directory)

        for stem, params in timedef.otoole_stems.items():
            if stem not in timedef.otoole_cfg.empty_dfs:
                left = (
                    pd.read_csv(Path(path) / (stem + ".csv"))
                    .sort_values(params["columns"])
                    .reset_index(drop=True)
                )
                right = (
                    pd.read_csv(Path(output_directory) / Path(stem + ".csv"))
                    .sort_values(params["columns"])
                    .reset_index(drop=True)
                )

                assert left.equals(right)
