from pathlib import Path

import pandas as pd

from tests.fixtures.paths import OTOOLE_SAMPLE_PATHS
from tz.osemosys.schemas.impact import Impact


def test_otoole_roundtrip():
    comparison_root = "./tests/otoole_compare/"

    for path in OTOOLE_SAMPLE_PATHS:

        comparison_model = Path(path).name
        output_directory = Path(comparison_root + comparison_model)
        output_directory.mkdir(parents=True, exist_ok=True)

        impacts = Impact.from_otoole_csv(root_dir=path)

        Impact.to_otoole_csv(impacts=impacts, output_directory=output_directory)

        if impacts:
            for stem, params in impacts[0].otoole_stems.items():
                if stem not in impacts[0].otoole_cfg.empty_dfs:
                    left = (
                        pd.read_csv(Path(path) / (stem + ".csv"))
                        .sort_values(params["columns"])
                        .reset_index(drop=True)
                        .sort_index(axis=1)
                    )
                    right = (
                        pd.read_csv(Path(output_directory) / Path(stem + ".csv"))
                        .sort_values(params["columns"])
                        .reset_index(drop=True)
                        .sort_index(axis=1)
                    )
                    print("LEFT")
                    print(left)
                    print("RIGHT")
                    print(right)
                    print("ASSERT", stem, left.equals(right))

                    assert left.equals(right)
