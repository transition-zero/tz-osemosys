from pathlib import Path

import pandas as pd

from tests.fixtures.paths import OTOOLE_SAMPLE_PATHS
from tz.osemosys.schemas.technology import Technology


def test_otoole_roundtrip():
    comparison_root = "./tests/otoole_compare/"

    for path in OTOOLE_SAMPLE_PATHS:
        comparison_model = Path(path).name
        output_directory = Path(comparison_root + comparison_model)
        output_directory.mkdir(parents=True, exist_ok=True)

        technologies = Technology.from_otoole_csv(root_dir=path)
        print(technologies[0].otoole_cfg)

        Technology.to_otoole_csv(technologies=technologies, output_directory=output_directory)

        if technologies:
            for stem, params in technologies[0].otoole_stems.items():
                if stem not in technologies[0].otoole_cfg.empty_dfs:
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
                    left["VALUE"] = left["VALUE"].astype(float)
                    right["VALUE"] = right["VALUE"].astype(float)
                    if not left.equals(right):
                        print("LEFT")
                        print(left)
                        print("RIGHT")
                        print(right)

                    assert left.equals(right)
