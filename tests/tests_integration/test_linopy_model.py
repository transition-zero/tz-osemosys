import pytest
import pandas as pd

from feo.osemosys.model.full_linopy_run import *
from tests.fixtures.paths import OTOOLE_SAMPLE_RESULTS


def test_linopy_model():
    
    for sample_path in OTOOLE_SAMPLE_RESULTS:
        #sample_name = sample_path.split('/')[-1]
        sample_name = 'otoole-simple-hydro'
        m = create_and_run_linopy(sample_name)
        ref_result_obj_df = pd.read_csv(os.path.join('examples/otoole_results/',
                                                     sample_name,
                                                    'TotalDiscountedCost.csv'))
        result_tolerance = 0.001 # 0.01% tolerance, results within 99.99% similar
        test_result_obj = m.solution.TotalDiscountedCost.sum().values
        ref_result_obj = ref_result_obj_df['VALUE'].sum()
        result_diff = ((test_result_obj - ref_result_obj) / ref_result_obj)
        
        #assert result_diff <= result_tolerance
        print(result_tolerance, 
              result_diff,
              sample_name)
    
test_linopy_model()