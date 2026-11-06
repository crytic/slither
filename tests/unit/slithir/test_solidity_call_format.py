from slither.core.declarations.solidity_variables import SolidityFunction
from slither.core.variables.local_variable import LocalVariable
from slither.slithir.operations.solidity_call import SolidityCall


def test_solidity_call_nested_arguments_use_values():
    arguments = []
    for name in ("target", "x", "y"):
        variable = LocalVariable()
        variable.name = name
        arguments.append(variable)
    call = SolidityCall(SolidityFunction("abi.encodeCall()"), 2, None, "")
    call.arguments = [arguments[0], [arguments[1], [arguments[2]]]]
    assert str(call) == "SOLIDITY_CALL abi.encodeCall()(target,[x, [y]])"
    call.arguments = arguments
    assert str(call) == "SOLIDITY_CALL abi.encodeCall()(target,x,y)"
