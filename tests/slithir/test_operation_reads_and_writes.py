from collections import namedtuple
import pytest
from solc_select import solc_select
from slither import Slither
from slither.core.declarations import Function
from slither.slithir.operations import (
    Operation,
    NewContract,
    Assignment,
    Binary,
    HighLevelCall,
    LowLevelCall,
    # Return,
    # NewStructure,
    # Transfer,
    # Send,
    TypeConversion,
    Index,
    Member,
    Unary,
    Unpack,
    Length,
    InitArray,
)


def check_num_local_vars_read(function: Function, slithir_op: Operation, num_reads_expected: int):
    for node in function.nodes:
        for operation in node.irs:
            if isinstance(operation, slithir_op):
                assert len(operation.read) == num_reads_expected
                assert len(node.local_variables_read) == num_reads_expected


def check_num_local_vars_written(
    function: Function, slithir_op: Operation, num_writes_expected: int
):
    for node in function.nodes:
        for operation in node.irs:
            if isinstance(operation, slithir_op):
                assert operation.lvalue in node.local_variables_read
                assert len(node.local_variables_read) == num_writes_expected


def check_num_state_vars_read(function: Function, slithir_op: Operation, num_reads_expected: int):
    for node in function.nodes:
        for operation in node.irs:
            if isinstance(operation, slithir_op):
                print(*operation.read)
                assert len(operation.read) == num_reads_expected
                assert len(node.state_variables_read) == num_reads_expected


def check_num_state_vars_written(
    function: Function, slithir_op: Operation, num_writes_expected: int
):
    for node in function.nodes:
        for operation in node.irs:
            if isinstance(operation, slithir_op):
                assert operation.lvalue in node.state_variables_read
                assert len(node.state_variables_read) == num_writes_expected


OperationTest = namedtuple("OperationTest", "slithir_op read_contract_name write_contract_name")

OPERATION_TEST = [
    OperationTest(NewContract, "NewContractReadAll", "NewContractWriteAll"),
    OperationTest(Assignment, "AssignmentReadAll", "AssignmentWriteAll"),
    OperationTest(Binary, "BinaryReadAll", "BinaryWriteAll"),
    OperationTest(HighLevelCall, "HighLevelCallReadAll", "HighLevelCallWriteAll"),
    OperationTest(LowLevelCall, "LowLevelCallReadAll", "LowLevelCallWriteAll"),
    OperationTest(TypeConversion, "TypeConversionReadAll", "TypeConversionWriteAll"),
    OperationTest(Index, "IndexReadAll", "IndexWriteAll"),
    OperationTest(Member, "MemberReadAll", "MemberWriteAll"),
    OperationTest(Unary, "UnaryReadAll", "UnaryWriteAll"),
    OperationTest(Unpack, "UnpackReadAll", "UnpackWriteAll"),
    OperationTest(Length, "LengthReadAll", "LengthWriteAll"),
    OperationTest(InitArray, "InitArrayReadAll", "InitArrayWriteAll"),
    # TODO cannot write
    # OperationTest(Return, "ReturnReadAll", "ReturnWriteAll"),
    # OperationTest(NewStructure, "NewStructureReadAll", "NewStructureWriteAll")
    # OperationTest(Transfer, "TransferReadAll", "TransferWriteAll"),
    # OperationTest(Send, "SendReadAll", "SendWriteAll"),
]


@pytest.mark.parametrize("op_test", OPERATION_TEST)
def test_operation_read_and_writes(op_test) -> None:
    """
    Every slithir operation has its own contract and reads all local and state variables in readAllLocalVariables and readAllStateVariables, respectively.
    """
    solc_select.switch_global_version("0.8.0", always_install=True)
    slither = Slither("./tests/slithir/operation_reads.sol")

    available_to_read = slither.get_contract_from_name(op_test.read_contract_name)
    assert len(available_to_read) == 1
    read_target = available_to_read[0]

    available_to_write = slither.get_contract_from_name(op_test.write_contract_name)
    assert len(available_to_write) == 1
    write_target = available_to_write[0]

    num_state_variables = len(read_target.state_variables_ordered)
    read_state_function = read_target.get_function_from_signature("readAllStateVariables()")
    check_num_state_vars_read(read_state_function, op_test.slithir_op, num_state_variables)

    num_state_variables = len(write_target.state_variables_ordered)
    write_state_function = write_target.get_function_from_signature("writeAllStateVariables()")
    # TODO not a good way to check since these are stored in TMP variables
    # check_num_state_vars_written(write_state_function, op_test.slithir_op, num_state_variables)

    read_local_function = read_target.get_function_from_signature("readAllLocalVariables()")
    num_local_vars = len(read_local_function.local_variables)
    check_num_local_vars_read(read_local_function, op_test.slithir_op, num_local_vars)

    write_local_function = write_target.get_function_from_signature("writeAllLocalVariables()")
    num_local_vars = len(write_local_function.local_variables)
    # check_num_local_vars_written(write_local_function, op_test.slithir_op, num_local_vars)

    for state_var in read_target.state_variables_ordered:
        assert read_state_function in read_target.get_functions_reading_from_variable(state_var)

    for state_var in write_target.state_variables_ordered:
        assert write_state_function in write_target.get_functions_writing_to_variable(state_var)

    for local_var in read_local_function.local_variables:
        assert read_local_function in read_target.get_functions_reading_from_variable(local_var)

    for local_var in write_local_function.local_variables:
        assert write_local_function in write_target.get_functions_writing_to_variable(local_var)
