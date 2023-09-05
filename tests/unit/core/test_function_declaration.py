"""
tests for `slither.core.declarations.Function`.
tests that `tests/test_function.sol` gets translated into correct
`slither.core.declarations.Function` objects or its subclasses
and that these objects behave correctly.
"""
from pathlib import Path

from slither import Slither
from slither.core.declarations.function import FunctionType
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.mapping_type import MappingType

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"
FUNC_DELC_TEST_ROOT = Path(TEST_DATA_DIR, "function_declaration")


def test_functions(solc_binary_path):
    # pylint: disable=too-many-statements
    solc_path = solc_binary_path("0.6.12")
    file = Path(FUNC_DELC_TEST_ROOT, "test_function.sol").as_posix()
    slither = Slither(file, solc=solc_path)
    functions = slither.get_contract_from_name("TestFunction")[0].available_functions_as_dict()

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


def test_function_can_send_eth(solc_binary_path):
    solc_path = solc_binary_path("0.6.12")
    file = Path(FUNC_DELC_TEST_ROOT, "test_function.sol").as_posix()
    slither = Slither(file, solc=solc_path)
    compilation_unit = slither.compilation_units[0]
    functions = compilation_unit.get_contract_from_name("TestFunctionCanSendEth")[
        0
    ].available_functions_as_dict()

    assert functions["send_direct()"].can_send_eth() is True
    assert functions["transfer_direct()"].can_send_eth() is True
    assert functions["call_direct()"].can_send_eth() is True
    assert functions["highlevel_call_direct()"].can_send_eth() is True

    assert functions["send_via_internal()"].can_send_eth() is True
    assert functions["transfer_via_internal()"].can_send_eth() is True
    assert functions["call_via_internal()"].can_send_eth() is True
    assert functions["highlevel_call_via_internal()"].can_send_eth() is True

    assert functions["send_via_external()"].can_send_eth() is False
    assert functions["transfer_via_external()"].can_send_eth() is False
    assert functions["call_via_external()"].can_send_eth() is False
    assert functions["highlevel_call_via_external()"].can_send_eth() is False


def test_reentrant(solc_binary_path):
    solc_path = solc_binary_path("0.8.10")
    file = Path(FUNC_DELC_TEST_ROOT, "test_function_reentrant.sol").as_posix()
    slither = Slither(file, solc=solc_path)
    compilation_unit = slither.compilation_units[0]
    functions = compilation_unit.get_contract_from_name("TestReentrant")[
        0
    ].available_functions_as_dict()

    assert functions["is_reentrant()"].is_reentrant
    assert not functions["is_non_reentrant()"].is_reentrant
    assert not functions["internal_and_not_reentrant()"].is_reentrant
    assert not functions["internal_and_not_reentrant2()"].is_reentrant
    assert functions["internal_and_could_be_reentrant()"].is_reentrant
    assert functions["internal_and_reentrant()"].is_reentrant


def test_public_variable(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.6.12")
    file = Path(FUNC_DELC_TEST_ROOT, "test_function.sol").as_posix()
    slither = Slither(file, solc=solc_path)
    contracts = slither.get_contract_from_name("TestFunction")
    assert len(contracts) == 1
    contract = contracts[0]
    var = contract.get_state_variable_from_name("info")
    assert var
    assert var.solidity_signature == "info()"
    assert var.signature_str == "info() returns(bytes32)"
    assert var.visibility == "public"
    assert var.type == ElementaryType("bytes32")


# pylint: disable=too-many-statements
def test_vyper_functions(slither_from_vyper_source) -> None:
    with slither_from_vyper_source(
        """
balances: public(HashMap[address, uint256])
allowances: HashMap[address, HashMap[address, uint256]]
@pure
@internal
def add(x: int128, y: int128) -> int128:
    return x + y
@external
def __init__():
    pass
@external
def withdraw():
    raw_call(msg.sender, b"", value= self.balances[msg.sender])
@external
@nonreentrant("lock")
def withdraw_locked():
    raw_call(msg.sender, b"", value= self.balances[msg.sender])
@payable
@external
def __default__():
    pass
    """
    ) as sl:
        contract = sl.contracts[0]
        functions = contract.available_functions_as_dict()

        f = functions["add(int128,int128)"]
        assert f.function_type == FunctionType.NORMAL
        assert f.visibility == "internal"
        assert not f.payable
        assert f.view is False
        assert f.pure is True
        assert f.parameters[0].name == "x"
        assert f.parameters[0].type == ElementaryType("int128")
        assert f.parameters[1].name == "y"
        assert f.parameters[1].type == ElementaryType("int128")
        assert f.return_type[0] == ElementaryType("int128")

        f = functions["__init__()"]
        assert f.function_type == FunctionType.CONSTRUCTOR
        assert f.visibility == "external"
        assert not f.payable
        assert not f.view
        assert not f.pure
        assert not f.is_implemented
        assert f.is_empty

        f = functions["__default__()"]
        assert f.function_type == FunctionType.FALLBACK
        assert f.visibility == "external"
        assert f.payable
        assert not f.view
        assert not f.pure
        assert not f.is_implemented
        assert f.is_empty

        f = functions["withdraw()"]
        assert f.function_type == FunctionType.NORMAL
        assert f.visibility == "external"
        assert not f.payable
        assert not f.view
        assert not f.pure
        assert f.can_send_eth()
        assert f.can_reenter()
        assert f.is_implemented
        assert not f.is_empty

        f = functions["withdraw_locked()"]
        assert not f.is_reentrant
        assert f.is_implemented
        assert not f.is_empty

        var = contract.get_state_variable_from_name("balances")
        assert var
        assert var.solidity_signature == "balances(address)"
        assert var.signature_str == "balances(address) returns(uint256)"
        assert var.visibility == "public"
        assert var.type == MappingType(ElementaryType("address"), ElementaryType("uint256"))

        var = contract.get_state_variable_from_name("allowances")
        assert var
        assert var.solidity_signature == "allowances(address,address)"
        assert var.signature_str == "allowances(address,address) returns(uint256)"
        assert var.visibility == "internal"
        assert var.type == MappingType(
            ElementaryType("address"),
            MappingType(ElementaryType("address"), ElementaryType("uint256")),
        )
