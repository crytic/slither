from slither import Slither

def test_path_filtering():
    return Slither("./tests/test_path_filtering/test_path_filtering.sol", filter_paths=["filtering_paths/libs", "filtering_paths/src/ReentrancyMock.sol"])
