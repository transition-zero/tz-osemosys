from pathlib import Path

import pandas as pd

from tests.fixtures.paths import OTOOLE_SAMPLE_PATHS
from tz.osemosys.schemas.region import Region


def test_otoole_roundtrip():
    comparison_root = "./tests/otoole_compare/"

    for path in OTOOLE_SAMPLE_PATHS:
        comparison_model = Path(path).name
        output_directory = Path(comparison_root + comparison_model)
        output_directory.mkdir(parents=True, exist_ok=True)

        regions = Region.from_otoole_csv(root_dir=path)

        Region.to_otoole_csv(regions=regions, output_directory=output_directory)

        for stem, params in regions[0].otoole_stems.items():
            if stem not in regions[0].otoole_cfg.empty_dfs:
                left = (
                    pd.read_csv(Path(path) / (stem + ".csv"))[params["columns"]]
                    .sort_values(params["columns"])
                    .reset_index(drop=True)
                )
                right = (
                    pd.read_csv(Path(output_directory) / Path(stem + ".csv"))[params["columns"]]
                    .sort_values(params["columns"])
                    .reset_index(drop=True)
                )

                print("LEFT")
                print(left)
                print("RIGHT")
                print(right)

                assert left.equals(right)
