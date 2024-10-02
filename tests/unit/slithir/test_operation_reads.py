from pathlib import Path
from collections import namedtuple
from slither import Slither
from slither.slithir.operations import Operation, NewContract

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


def check_num_local_vars_read(function, slithir_op: Operation, num_reads_expected: int):
    for node in function.nodes:
        for operation in node.irs:
            if isinstance(operation, slithir_op):
                assert len(operation.read) == num_reads_expected
                assert len(node.local_variables_read) == num_reads_expected


def check_num_states_vars_read(function, slithir_op: Operation, num_reads_expected: int):
    for node in function.nodes:
        for operation in node.irs:
            if isinstance(operation, slithir_op):
                assert len(operation.read) == num_reads_expected
                assert len(node.state_variables_read) == num_reads_expected


OperationTest = namedtuple("OperationTest", "contract_name slithir_op")

OPERATION_TEST = [OperationTest("NewContract", NewContract)]


def test_operation_reads(solc_binary_path) -> None:
    """
    Every slithir operation has its own contract and reads all local and state variables in readAllLocalVariables and readAllStateVariables, respectively.
    """
    solc_path = solc_binary_path("0.8.15")
    slither = Slither(Path(TEST_DATA_DIR, "operation_reads.sol").as_posix(), solc=solc_path)

    for op_test in OPERATION_TEST:
        print(op_test)
        available = slither.get_contract_from_name(op_test.contract_name)
        assert len(available) == 1
        target = available[0]

        num_state_variables = len(target.state_variables_ordered)
        state_function = target.get_function_from_signature("readAllStateVariables()")
        check_num_states_vars_read(state_function, op_test.slithir_op, num_state_variables)

        local_function = target.get_function_from_signature("readAllLocalVariables()")
        num_local_vars = len(local_function.local_variables)
        check_num_local_vars_read(local_function, op_test.slithir_op, num_local_vars)
