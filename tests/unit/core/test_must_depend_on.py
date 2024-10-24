from pathlib import Path
from slither import Slither
from slither.analyses.data_dependency.data_dependency import get_must_depends_on
from slither.core.variables.variable import Variable
from slither.core.declarations import SolidityVariable, SolidityVariableComposed
from typing import Union
from slither.slithir.variables import (
    Constant,
)

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"
SUPPORTED_TYPES = Union[Variable, SolidityVariable, Constant]


def test_must_depend_on_returns(solc_binary_path):
    solc_path = solc_binary_path("0.8.19")
    file = Path(TEST_DATA_DIR, "must_depend_on.sol").as_posix()
    slither_obj = Slither(file, solc=solc_path)

    for contract in slither_obj.contracts:
        for function in contract.functions:
            if contract == "Unsafe" and function == "int_transferFrom":
                result = get_must_depends_on(function.parameters[0])
                break
    assert isinstance(result, list)
    assert result[0] == SolidityVariableComposed("msg.sender"), "Output should be msg.sender"

    result = get_must_depends_on(slither_obj.contracts[1].functions[2].parameters[1])
    assert isinstance(result, list)
    assert len(result) == 0, "Output should be empty"
