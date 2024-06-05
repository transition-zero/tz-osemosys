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

        left = pd.read_csv(Path(path) / ("REGION.csv")).sort_values("VALUE").reset_index(drop=True)
        right = (
            pd.read_csv(Path(output_directory) / Path("REGION.csv"))
            .sort_values("VALUE")
            .reset_index(drop=True)
        )

        assert left.equals(right)
