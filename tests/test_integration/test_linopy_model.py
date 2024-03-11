from pathlib import Path

import numpy as np
import pandas as pd

from feo.osemosys import Model
from tests.fixtures.paths import OTOOLE_SAMPLE_PATHS, OTOOLE_SAMPLE_RESULTS

TOL = 0.0001  # 0.01% tolerance, results within 99.99% similar


def test_linopy_model():
    otoole_sample_results = {Path(path).stem: path for path in OTOOLE_SAMPLE_RESULTS}

    for sample_path in OTOOLE_SAMPLE_PATHS:
        model_name = Path(sample_path).stem

        if model_name in otoole_sample_results:
            results_path = otoole_sample_results[model_name]

            model = Model.from_otoole_csv(sample_path)

            model.solve()

            ref_results_df = pd.read_csv(Path(results_path) / "TotalDiscountedCost.csv")

            print(model._m.solution.TotalDiscountedCost.sum().values, ref_results_df["VALUE"].sum())

        assert np.isclose(
            model._m.solution.TotalDiscountedCost.sum().values,
            ref_results_df["VALUE"].sum(),
            rtol=TOL,
        )
