from pathlib import Path
from slither import Slither
from slither.slithir.operations import Assignment
from slither.slithir.variables import Constant

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


func_to_results = {
    "returnEvent()": "16700440330922901039223184000601971290390760458944929668086539975128325467771",
    "returnError()": "224292994",
    "returnFunctionFromContract()": "890000139",
    "returnFunction()": "890000139",
    "returnFunctionWithStructure()": "1430834845",
    "returnFunctionThroughLocaLVar()": "3781905051",
}


def test_enum_max_min(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.19")
    slither = Slither(Path(TEST_DATA_DIR, "selector.sol").as_posix(), solc=solc_path)

    contract = slither.get_contract_from_name("Test")[0]

    for func_name, value in func_to_results.items():
        f = contract.get_function_from_signature(func_name)
        assignment = f.slithir_operations[0]
        assert (
            isinstance(assignment, Assignment)
            and isinstance(assignment.rvalue, Constant)
            and assignment.rvalue.value == value
        )
