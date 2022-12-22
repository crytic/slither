from slither import Slither
from slither.core.declarations import Function
from slither.core.variables.local_variable import LocalVariable
from slither.slithir.operations import Assignment
from slither.slithir.variables import Constant


def test_tuples() -> None:
    slither = Slither("./tests/slithir/tuples.sol")
    contract = slither.contracts[0]
    functions = contract.functions
    check_f1_f2(functions[0])
    check_f1_f2(functions[1])
    check_f3(functions[2])


def check_f1_f2(function: Function):
    assert len(function.slithir_operations) == 2
    op1 = function.slithir_operations[0]
    assert isinstance(op1, Assignment)
    assert isinstance(op1.lvalue, LocalVariable)
    assert isinstance(op1.rvalue, Constant)
    assert op1.lvalue.name == "x"
    assert op1.rvalue.name == "7"


def check_f3(function: Function):
    assert len(function.slithir_operations) == 5
    op1 = function.slithir_operations[0]
    op2 = function.slithir_operations[1]
    op3 = function.slithir_operations[2]
    op4 = function.slithir_operations[3]
    assert isinstance(op1, Assignment)
    assert isinstance(op2, Assignment)
    assert isinstance(op3, Assignment)
    assert isinstance(op4, Assignment)
    assert isinstance(op1.lvalue, LocalVariable)
    assert isinstance(op1.rvalue, Constant)
    assert isinstance(op2.lvalue, LocalVariable)
    assert isinstance(op2.rvalue, Constant)
    assert isinstance(op3.lvalue, LocalVariable)
    assert isinstance(op3.rvalue, Constant)
    assert isinstance(op4.lvalue, LocalVariable)
    assert isinstance(op4.rvalue, Constant)
    assert op1.lvalue.name == "x"
    assert op1.rvalue.name == "1"
    assert op2.lvalue.name == "y"
    assert op2.rvalue.name == "2"
    assert op3.lvalue.name == "z"
    assert op3.rvalue.name == "3"
    assert op4.lvalue.name == "t"
    assert op4.rvalue.name == "4"


if __name__ == "__main__":
    test_tuples()
