from slither import Slither
from crytic_compile import CryticCompile
from crytic_compile.platform.solc_standard_json import SolcStandardJson
from crytic_compile.utils.zip import load_from_zip, save_to_zip
from slither.printers.call.call_graph import (
    _setup_functions,
    _process_internal_call,
    _process_external_call,
    _edge,
    _function_node,
    _solidity_function_node,
    PrinterCallGraph,
)
from deepdiff import DeepDiff
from slither.core.declarations.function_top_level import FunctionTopLevel
from slither.core.declarations.function import Function
from slither.core.declarations.solidity_variables import SolidityFunction
from collections import defaultdict
import os
import pytest


SLITHER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_FILE_PATH = os.path.join(SLITHER_ROOT, "tests", "printers/")


def setup():
    solc_standard_json = SolcStandardJson()
    solc_standard_json.add_source_file(os.path.join(TEST_FILE_PATH, "TestTopLevels.sol"))
    solc_standard_json.add_source_file(os.path.join(TEST_FILE_PATH, "TopLevelImported.sol"))
    solc_standard_json.add_source_file(os.path.join(TEST_FILE_PATH, "TopLevelUsingFor.sol"))
    cc = CryticCompile(solc_standard_json)
    zip_file = os.path.join(SLITHER_ROOT, "tests/printers/TestTopLevelASTJSON.zip")
    save_to_zip([cc], zip_file)
    crytic_compile_units = load_from_zip(zip_file)[0]
    sl = Slither(crytic_compile_units)
    compilation_units = sl.compilation_units
    regular_function_dict, top_level_dict = _setup_functions(compilation_units)
    for fn_reg in regular_function_dict:
        assert isinstance(fn_reg, (Function))  # sanity check
    for fn_top in top_level_dict:
        assert isinstance(fn_top, (FunctionTopLevel))  # sanity check
    return (regular_function_dict, top_level_dict)


def get_contract_and_fn_names():
    contracts = [
        "TestTopLevels",
        "TopLevelImported",
        "TestTopLevelInherit",
        "TopLevelUsingFor",
        "[Solidity]",
        "Hello",
    ]
    dummy_contract_names = [
        "TopLevel_TopLevelImported",
        "TopLevel_TestTopLevels",
        "TopLevel_TopLevelUsingFor",
    ]
    total_contracts = contracts + dummy_contract_names
    sol_calls = ["ecrecover(bytes32,uint8,bytes32,bytes32)", "abi.encode()", "keccak256(bytes)"]

    internal_calls = [
        "setNumber",
        "cry",
        "getBit",
        "attempt",
        "canDoThing",
        "x2",
        "x3",
        "hi",
        "increment",
        "fill",
    ]
    top_level_calls = ["setNumber", "cry", "getBit", "fill", "attempt"]

    external_calls = ["test", "beExternal"]

    total_functions = internal_calls + sol_calls + external_calls
    return (
        contracts,
        dummy_contract_names,
        total_contracts,
        sol_calls,
        internal_calls,
        external_calls,
        top_level_calls,
        total_functions,
    )


def get_edges():
    edges = [
        '"175_x3" -> "175_beExternal"',
        '"175_beExternal" -> "12_test"',
        '"TopLevelFunctions_TestTopLevels_setNumber" -> "12_test"',
        '"290_increment" -> "175_beExternal"',
        '"366_canTry" -> "TopLevelFunctions_TopLevelUsingFor_getBit"',
        '"366_canDoThing" -> "TopLevelFunctions_TopLevelUsingFor_getBit"',
        '"175_increment" -> "TopLevelFunctions_TopLevelImported_cry"',
        '"175_x3" -> "TopLevelFunctions_TestTopLevels_setNumber"',
        '"175_increment" -> "TopLevelFunctions_TestTopLevels_attempt"',
        '"175_increment" -> "175_x3"',
        '"175_increment" -> "366_canDoThing"',
        '"175_x3" -> "95_hi"',
        '"175_x3" -> "TopLevelFunctions_TestTopLevels_attempt"',
        '"175_x3" -> "175_increment"',
        '"175_x3" -> "TopLevelFunctions_TestTopLevels_fill"',
        '"TopLevelFunctions_TestTopLevels_attempt" -> "TopLevelFunctions_TestTopLevels_setNumber"',
        '"TopLevelFunctions_TestTopLevels_setNumber" -> "TopLevelFunctions_TestTopLevels_fill"',
        '"TopLevelFunctions_TestTopLevels_fill" -> "TopLevelFunctions_TopLevelImported_cry"',
        '"TopLevelFunctions_TopLevelImported_setNumber" -> "TopLevelFunctions_TopLevelImported_fill"',
        '"TopLevelFunctions_TopLevelImported_cry" -> "TopLevelFunctions_TopLevelImported_setNumber"',
        '"290_increment" -> "TopLevelFunctions_TopLevelImported_setNumber"',
        '"290_x2" -> "TopLevelFunctions_TopLevelImported_cry"',
        '"290_increment" -> "290_x2"',
        '"290_a3" -> "TopLevelFunctions_TopLevelImported_cry"',
        '"290_a3" -> "TopLevelFunctions_TopLevelImported_fill"',
        '"290_a3" -> "290_increment"',
        '"95_hi" -> "366_canDoThing"',
        '"95_hi" -> "TopLevelFunctions_TopLevelUsingFor_getBit"',
        '"95_hi" -> "TopLevelFunctions_TestTopLevels_setNumber"',
        '"TopLevelFunctions_TopLevelImported_fill" -> "abi.encode()"',
        '"290_a3" -> "abi.encode()"',
        '"290_a3" -> "ecrecover(bytes32,uint8,bytes32,bytes32)"',
        '"TopLevelFunctions_TestTopLevels_setNumber" -> "keccak256(bytes)"',
        '"TopLevelFunctions_TopLevelImported_setNumber" -> "keccak256(bytes)"',
        '"290_a3" -> "keccak256(bytes)"',
        '"TopLevelFunctions_TestTopLevels_setNumber" -> "abi.encode()"',
        '"366_canDoThing" -> "TopLevelFunctions_TopLevelUsingFor_getBit"',
    ]
    return stringify(edges)


def stringify(target):
    return "".join("".join(target))


def test_internal_call():
    function_dict, top_level_dict = setup()
    _, _, total_contracts, sol_calls, internal_calls, _, _, _ = get_contract_and_fn_names()
    edges = get_edges()
    solidity_functions = set()
    solidity_calls = set()
    contract_calls = defaultdict(set)
    combined_calls = internal_calls + sol_calls
    for function in function_dict:
        contract = function.contract_declarer
        assert contract.name in total_contracts  # sanity check we are getting the correct contracts
        for internal_fn in function.internal_calls:
            assert internal_fn.name in combined_calls  # sanity check we have an internal function
            _process_internal_call(
                contract,
                function,
                internal_fn,
                contract_calls,
                solidity_functions,
                solidity_calls,
                top_level_dict,
            )
            if isinstance(internal_fn, (SolidityFunction)):
                assert internal_fn.name in sol_calls  # sanity check we have solidity function
                sol_node = _solidity_function_node(internal_fn)
                edge = _edge(_function_node(function, top_level_dict), sol_node)
                assert edge in edges
                new_edge = edge.strip().replace('"', "")
                sol_fns_trimmed = set()
                sol_calls_trimmed = set()
                for txt in solidity_functions:
                    new = txt.strip().replace('"', "")
                    sol_fns_trimmed.add(new)
                for txt in solidity_calls:
                    new = txt.strip().replace('"', "")
                    sol_calls_trimmed.add(new)

                assert (
                    sol_node in sol_fns_trimmed
                )  # nodes are correctly formed for solidity functions
                assert (
                    new_edge in sol_calls_trimmed
                )  # edges are correctly formed for solidity functions

            else:
                assert internal_fn.name in internal_calls
                edge = _edge(
                    _function_node(function, top_level_dict),
                    _function_node(internal_fn, top_level_dict),
                )
                assert edge in edges
                assert (
                    edge in contract_calls[contract]
                )  # edges are correctly formed for internal/toplevels


def test_external_calls():
    function_dict, top_level_dict = setup()
    _, _, total_contracts, _, _, external_calls, _, _ = get_contract_and_fn_names()
    edges = get_edges()
    external_calls_list = set()  # external calls edges
    contract_calls = defaultdict(set)  # contract -> contract calls
    all_contracts = set()
    for function in function_dict:
        contract = function.contract_declarer
        all_contracts.add(contract)
        assert contract.name in total_contracts
    for function in function_dict:
        for external_function in function.high_level_calls:

            _, external_func = external_function
            assert external_func.name in external_calls
            _process_external_call(
                function,
                external_function,
                contract_calls,
                external_calls_list,
                all_contracts,
                top_level_dict,
            )

            edge = _edge(
                _function_node(function, top_level_dict),
                _function_node(external_func, top_level_dict),
            )

            assert edge in edges
            assert edge in external_calls_list


def test_generate_dot():
    solc_standard_json = SolcStandardJson()
    solc_standard_json.add_source_file(os.path.join(TEST_FILE_PATH, "TestTopLevels.sol"))
    solc_standard_json.add_source_file(os.path.join(TEST_FILE_PATH, "TopLevelImported.sol"))
    solc_standard_json.add_source_file(os.path.join(TEST_FILE_PATH, "TopLevelUsingFor.sol"))
    cc = CryticCompile(solc_standard_json)
    zip_file = os.path.join(SLITHER_ROOT, "tests/printers/TestTopLevelASTJSON.zip")
    save_to_zip([cc], zip_file)
    crytic_compile_units = load_from_zip(zip_file)[0]
    sl = Slither(crytic_compile_units)
    printer = PrinterCallGraph(sl, logger=None)
    printer.output(os.path.join(TEST_FILE_PATH, "AllContractsTestGeneration"))
    with open(
        os.path.join(TEST_FILE_PATH, "TestTopLevels.sol.all_contracts.call-graph.dot"), "rb"
    ) as f:
        expected = f.read()
        f.close()
    with open(
        os.path.join(TEST_FILE_PATH, "AllContractsTestGeneration.all_contracts.call-graph.dot"),
        "rb",
    ) as g:
        actual = g.read()
        g.close()
    assert DeepDiff(expected, actual) == {}
