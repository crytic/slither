from slither import Slither
from tests.test_features import _run_all_detectors

def test_path_filtering():
    slither = Slither("./tests/test_path_filtering/test_path_filtering.py")
    _run_all_detectors(slither)
