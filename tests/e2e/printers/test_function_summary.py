"""
Tests for the function-summary printer, specifically for issue #2073.

Issue #2073: The function-summary printer incorrectly reports all statements
with '.' as external calls, including:
- Solidity built-ins like abi.encode(), abi.decode()
- Library calls like SafeMath.add()
- Struct field access

This test verifies that only true external contract calls are reported
in the "External Calls" column of the function-summary printer.
"""

from pathlib import Path

from crytic_compile import CryticCompile
from crytic_compile.platform.solc_standard_json import SolcStandardJson

from slither import Slither


TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data" / "test_function_summary"


def _get_external_calls_from_summary(func):
    """Get external calls from function summary (index 7 in the tuple)."""
    summary = func.get_summary()
    return summary[7]  # external_calls is at index 7


def _assert_no_external_calls_in_summary(contract, contract_name):
    """Helper to assert a contract's functions have no external calls in summary."""
    for func in contract.functions:
        if func.is_constructor:
            continue
        external_calls = _get_external_calls_from_summary(func)
        assert len(external_calls) == 0, (
            f"{contract_name}.{func.name} should have no external calls, "
            f"but found: {external_calls}"
        )


def test_function_summary_external_calls(solc_binary_path) -> None:
    """
    Test that the function-summary correctly classifies external calls.

    - Solidity built-ins (abi.encode, etc.) should NOT be external calls
    - Library calls (SafeMath.add, etc.) should NOT be external calls
    - Struct field access should NOT be external calls
    - True external contract calls SHOULD be external calls
    """
    solc_path = solc_binary_path("0.8.0")
    standard_json = SolcStandardJson()
    standard_json.add_source_file(Path(TEST_DATA_DIR, "external_calls.sol").as_posix())
    compilation = CryticCompile(standard_json, solc=solc_path)
    slither = Slither(compilation)

    # Test TestBuiltins contract - should have NO external calls
    test_builtins = slither.get_contract_from_name("TestBuiltins")[0]
    _assert_no_external_calls_in_summary(test_builtins, "TestBuiltins")

    # Test TestLibraryCalls contract - should have NO external calls
    test_library = slither.get_contract_from_name("TestLibraryCalls")[0]
    _assert_no_external_calls_in_summary(test_library, "TestLibraryCalls")

    # Test TestStructAccess contract - should have NO external calls
    test_struct = slither.get_contract_from_name("TestStructAccess")[0]
    _assert_no_external_calls_in_summary(test_struct, "TestStructAccess")

    # Test TestExternalCalls contract - should have external calls
    test_external = slither.get_contract_from_name("TestExternalCalls")[0]

    call_external = test_external.get_function_from_signature("callExternal()")
    ext_calls = _get_external_calls_from_summary(call_external)
    assert len(ext_calls) == 1, "TestExternalCalls.callExternal should have 1 external call"

    call_with_arg = test_external.get_function_from_signature("callExternalWithArg(uint256)")
    ext_calls = _get_external_calls_from_summary(call_with_arg)
    assert len(ext_calls) == 1, "TestExternalCalls.callExternalWithArg should have 1 external call"

    call_multiple = test_external.get_function_from_signature("callMultipleExternal(uint256)")
    ext_calls = _get_external_calls_from_summary(call_multiple)
    assert len(ext_calls) == 2, (
        "TestExternalCalls.callMultipleExternal should have 2 external calls"
    )

    # Test TestMixed contract - mixedOperations should have exactly 1 external call
    test_mixed = slither.get_contract_from_name("TestMixed")[0]
    mixed_ops = test_mixed.get_function_from_signature("mixedOperations(uint256,uint256)")
    ext_calls = _get_external_calls_from_summary(mixed_ops)
    assert len(ext_calls) == 1, (
        f"TestMixed.mixedOperations should have 1 external call, "
        f"but found {len(ext_calls)}: {ext_calls}"
    )
