"""
tests for `slither.core.declarations.Function`.
tests that `tests/test_function.sol` gets translated into correct
`slither.core.declarations.Function` objects or its subclasses
and that these objects behave correctly.
"""

from slither import Slither
from slither.core.declarations.function import FunctionType
from slither.core.solidity_types.elementary_type import ElementaryType


def test_functions():
    # pylint: disable=too-many-statements
    slither = Slither("tests/test_function.sol")
    functions = slither.contracts_as_dict["TestFunction"].available_functions_as_dict()

    f = functions["external_payable(uint256)"]
    assert f.name == "external_payable"
    assert f.full_name == "external_payable(uint256)"
    assert f.canonical_name == "TestFunction.external_payable(uint256)"
    assert f.solidity_signature == "external_payable(uint256)"
    assert f.signature_str == "external_payable(uint256) returns(uint256)"
    assert f.function_type == FunctionType.NORMAL
    assert f.contains_assembly is False
    assert f.can_reenter() is False
    assert f.can_send_eth() is False
    assert f.is_constructor is False
    assert f.is_fallback is False
    assert f.is_receive is False
    assert f.payable is True
    assert f.visibility == "external"
    assert f.view is False
    assert f.pure is False
    assert f.is_implemented is True
    assert f.is_empty is False
    assert f.parameters[0].name == "_a"
    assert f.parameters[0].type == ElementaryType("uint256")
    assert f.return_type[0] == ElementaryType("uint256")

    f = functions["public_reenter()"]
    assert f.name == "public_reenter"
    assert f.full_name == "public_reenter()"
    assert f.canonical_name == "TestFunction.public_reenter()"
    assert f.solidity_signature == "public_reenter()"
    assert f.signature_str == "public_reenter() returns()"
    assert f.function_type == FunctionType.NORMAL
    assert f.contains_assembly is False
    assert f.can_reenter() is True
    assert f.can_send_eth() is False
    assert f.is_constructor is False
    assert f.is_fallback is False
    assert f.is_receive is False
    assert f.payable is False
    assert f.visibility == "public"
    assert f.view is False
    assert f.pure is False
    assert f.is_implemented is True
    assert f.is_empty is False
    assert f.parameters == []
    assert f.return_type is None

    f = functions["public_payable_reenter_send(bool)"]
    assert f.name == "public_payable_reenter_send"
    assert f.full_name == "public_payable_reenter_send(bool)"
    assert f.canonical_name == "TestFunction.public_payable_reenter_send(bool)"
    assert f.solidity_signature == "public_payable_reenter_send(bool)"
    assert f.signature_str == "public_payable_reenter_send(bool) returns()"
    assert f.function_type == FunctionType.NORMAL
    assert f.contains_assembly is False
    assert f.can_reenter() is True
    assert f.can_send_eth() is True
    assert f.is_constructor is False
    assert f.is_fallback is False
    assert f.is_receive is False
    assert f.payable is True
    assert f.visibility == "public"
    assert f.view is False
    assert f.pure is False
    assert f.is_implemented is True
    assert f.is_empty is False
    assert f.parameters[0].name == "_b"
    assert f.parameters[0].type == ElementaryType("bool")
    assert f.return_type is None

    f = functions["external_send(uint8)"]
    assert f.name == "external_send"
    assert f.full_name == "external_send(uint8)"
    assert f.canonical_name == "TestFunction.external_send(uint8)"
    assert f.solidity_signature == "external_send(uint8)"
    assert f.signature_str == "external_send(uint8) returns()"
    assert f.function_type == FunctionType.NORMAL
    assert f.contains_assembly is False
    assert f.can_reenter() is True
    assert f.can_send_eth() is True
    assert f.is_constructor is False
    assert f.is_fallback is False
    assert f.is_receive is False
    assert f.payable is False
    assert f.visibility == "external"
    assert f.view is False
    assert f.pure is False
    assert f.is_implemented is True
    assert f.is_empty is False
    assert f.parameters[0].name == "_c"
    assert f.parameters[0].type == ElementaryType("uint8")
    assert f.return_type is None

    f = functions["internal_assembly(bytes)"]
    assert f.name == "internal_assembly"
    assert f.full_name == "internal_assembly(bytes)"
    assert f.canonical_name == "TestFunction.internal_assembly(bytes)"
    assert f.solidity_signature == "internal_assembly(bytes)"
    assert f.signature_str == "internal_assembly(bytes) returns(uint256)"
    assert f.function_type == FunctionType.NORMAL
    assert f.contains_assembly is True
    assert f.can_reenter() is False
    assert f.can_send_eth() is False
    assert f.is_constructor is False
    assert f.is_fallback is False
    assert f.is_receive is False
    assert f.payable is False
    assert f.visibility == "internal"
    assert f.view is False
    assert f.pure is False
    assert f.is_implemented is True
    assert f.is_empty is False
    assert f.parameters[0].name == "_d"
    assert f.parameters[0].type == ElementaryType("bytes")
    assert f.return_type[0] == ElementaryType("uint256")

    f = functions["fallback()"]
    assert f.name == "fallback"
    assert f.full_name == "fallback()"
    assert f.canonical_name == "TestFunction.fallback()"
    assert f.solidity_signature == "fallback()"
    assert f.signature_str == "fallback() returns()"
    assert f.function_type == FunctionType.FALLBACK
    assert f.contains_assembly is False
    assert f.can_reenter() is False
    assert f.can_send_eth() is False
    assert f.is_constructor is False
    assert f.is_fallback is True
    assert f.is_receive is False
    assert f.payable is False
    assert f.visibility == "external"
    assert f.view is False
    assert f.pure is False
    assert f.is_implemented is True
    assert f.is_empty is True
    assert f.parameters == []
    assert f.return_type is None

    f = functions["receive()"]
    assert f.name == "receive"
    assert f.full_name == "receive()"
    assert f.canonical_name == "TestFunction.receive()"
    assert f.solidity_signature == "receive()"
    assert f.signature_str == "receive() returns()"
    assert f.function_type == FunctionType.RECEIVE
    assert f.contains_assembly is False
    assert f.can_reenter() is False
    assert f.can_send_eth() is False
    assert f.is_constructor is False
    assert f.is_fallback is False
    assert f.is_receive is True
    assert f.payable is True
    assert f.visibility == "external"
    assert f.view is False
    assert f.pure is False
    assert f.is_implemented is True
    assert f.is_empty is True
    assert f.parameters == []
    assert f.return_type is None

    f = functions["constructor(address)"]
    assert f.name == "constructor"
    assert f.full_name == "constructor(address)"
    assert f.canonical_name == "TestFunction.constructor(address)"
    assert f.solidity_signature == "constructor(address)"
    assert f.signature_str == "constructor(address) returns()"
    assert f.function_type == FunctionType.CONSTRUCTOR
    assert f.contains_assembly is False
    assert f.can_reenter() is False
    assert f.can_send_eth() is False
    assert f.is_constructor
    assert f.is_fallback is False
    assert f.is_receive is False
    assert f.payable is True
    assert f.visibility == "public"
    assert f.view is False
    assert f.pure is False
    assert f.is_implemented is True
    assert f.is_empty is True
    assert f.parameters[0].name == "_e"
    assert f.parameters[0].type == ElementaryType("address")
    assert f.return_type is None

    f = functions["private_view()"]
    assert f.name == "private_view"
    assert f.full_name == "private_view()"
    assert f.canonical_name == "TestFunction.private_view()"
    assert f.solidity_signature == "private_view()"
    assert f.signature_str == "private_view() returns(bool)"
    assert f.function_type == FunctionType.NORMAL
    assert f.contains_assembly is False
    assert f.can_reenter() is False
    assert f.can_send_eth() is False
    assert f.is_constructor is False
    assert f.is_fallback is False
    assert f.is_receive is False
    assert f.payable is False
    assert f.visibility == "private"
    assert f.view is True
    assert f.pure is False
    assert f.is_implemented is True
    assert f.is_empty is False
    assert f.parameters == []
    assert f.return_type[0] == ElementaryType("bool")

    f = functions["public_pure()"]
    assert f.name == "public_pure"
    assert f.full_name == "public_pure()"
    assert f.canonical_name == "TestFunction.public_pure()"
    assert f.solidity_signature == "public_pure()"
    assert f.signature_str == "public_pure() returns(bool)"
    assert f.function_type == FunctionType.NORMAL
    assert f.contains_assembly is False
    assert f.can_reenter() is False
    assert f.can_send_eth() is False
    assert f.is_constructor is False
    assert f.is_fallback is False
    assert f.is_receive is False
    assert f.payable is False
    assert f.visibility == "public"
    assert f.view is True
    assert f.pure is True
    assert f.is_implemented is True
    assert f.is_empty is False
    assert f.parameters == []
    assert f.return_type[0] == ElementaryType("bool")
