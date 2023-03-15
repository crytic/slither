from slither import Slither
from crytic_compile import CryticCompile

from crytic_compile.utils.zip import load_from_zip,save_to_zip
from slither.printers.call.call_graph import (
    _create_dummy_declarers,
    _process_function,
    _process_functions,
    setup_functions,
    _process_internal_call,
    _process_external_call,
    _edge,
    _function_node,
    _solidity_function_node,
)
from slither.core.declarations.function_top_level import FunctionTopLevel
from slither.core.declarations.function import Function
from slither.core.declarations.solidity_variables import SolidityFunction
from collections import defaultdict
import os
import pytest


SLITHER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_FILE_PATH = os.path.join(SLITHER_ROOT, "tests/printers/TestTopLevels.sol")

@pytest.fixture
def setup():
    cc = CryticCompile(TEST_FILE_PATH,solc_standard_json=True)
    zip_file = os.path.join(SLITHER_ROOT,"tests/printers/TestTopLevelASTJSON.zip")
    save_to_zip([cc],zip_file)
    cc =load_from_zip(zip_file)[0]
    sl = Slither(cc)
    #sl = Slither("tests/printers/TestTopLevels.sol")
    compilation_units = sl.compilation_units
    regular_function_dict, top_level_dict = setup_functions(compilation_units)
    for fn_reg in regular_function_dict:
        assert isinstance(fn_reg, (Function))  # sanity check
    for fn_top in top_level_dict:
        assert isinstance(fn_top, (FunctionTopLevel))  # sanity check
    return (regular_function_dict, top_level_dict)


@pytest.fixture
def get_contract_and_fn_names():
    contracts = [
        "TestTopLevels",
        "TopLevelImported",
        "TestTopLevelInherit",
        "TopLevelUsingFor",
        "[Solidity]",
        "Hello"
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
    top_level_calls = ["setNumber","cry","getBit","fill","attempt"]

    external_calls = ["test", "beExternal"]

    total_functions = internal_calls + sol_calls + external_calls
    return (contracts,dummy_contract_names, total_contracts, sol_calls,internal_calls,external_calls,top_level_calls,total_functions)

@pytest.fixture
def get_edges():
    edges = ['"171_x3" -> "171_beExternal"',
    '"171_beExternal" -> "12_test"',
    '"TopLevelFunctions_TestTopLevels_setNumber" -> "12_test"',
    '"286_increment" -> "171_beExternal"',
    '"362_canTry" -> "TopLevelFunctions_TopLevelUsingFor_getBit"',
    '"362_canDoThing" -> "TopLevelFunctions_TopLevelUsingFor_getBit"',
    '"171_increment" -> "TopLevelFunctions_TopLevelImported_cry"',
    '"171_x3" -> "TopLevelFunctions_TestTopLevels_setNumber"',
    '"171_increment" -> "TopLevelFunctions_TestTopLevels_attempt"',
    '"171_increment" -> "171_x3"',
    '"171_increment" -> "362_canDoThing"',
    '"171_x3" -> "95_hi"',
    '"171_x3" -> "TopLevelFunctions_TestTopLevels_attempt"',
    '"171_x3" -> "171_increment"',
    '"171_x3" -> "TopLevelFunctions_TestTopLevels_fill"',
    '"TopLevelFunctions_TestTopLevels_attempt" -> "TopLevelFunctions_TestTopLevels_setNumber"',
    '"TopLevelFunctions_TestTopLevels_setNumber" -> "TopLevelFunctions_TestTopLevels_fill"',
    '"TopLevelFunctions_TestTopLevels_fill" -> "TopLevelFunctions_TopLevelImported_cry"',
    '"TopLevelFunctions_TopLevelImported_setNumber" -> "TopLevelFunctions_TopLevelImported_fill"',
    '"TopLevelFunctions_TopLevelImported_cry" -> "TopLevelFunctions_TopLevelImported_setNumber"',
    '"286_increment" -> "TopLevelFunctions_TopLevelImported_setNumber"',
    '"286_x2" -> "TopLevelFunctions_TopLevelImported_cry"',
    '"286_increment" -> "286_x2"',
    '"286_a3" -> "TopLevelFunctions_TopLevelImported_cry"',
    '"286_a3" -> "TopLevelFunctions_TopLevelImported_fill"',
    '"286_a3" -> "286_increment"',
    '"95_hi" -> "362_canDoThing"',
    '"95_hi" -> "TopLevelFunctions_TopLevelUsingFor_getBit"',
    '"95_hi" -> "TopLevelFunctions_TestTopLevels_setNumber"',
    '"TopLevelFunctions_TopLevelImported_fill" -> "abi.encode()"',
    '"286_a3" -> "abi.encode()"',
    '"286_a3" -> "ecrecover(bytes32,uint8,bytes32,bytes32)"',
    '"TopLevelFunctions_TestTopLevels_setNumber" -> "keccak256(bytes)"',
    '"TopLevelFunctions_TopLevelImported_setNumber" -> "keccak256(bytes)"',
    '"286_a3" -> "keccak256(bytes)"',
    '"TopLevelFunctions_TestTopLevels_setNumber" -> "abi.encode()"',
    '"366_canDoThing" -> "TopLevelFunctions_TopLevelUsingFor_getBit"']
    print(stringify(edges))
    return stringify(edges)

def stringify(target):
    return "".join("".join(target))




def test_internal_call(setup, get_contract_and_fn_names,get_edges):
    function_dict, top_level_dict = setup
    _,_, total_contracts, sol_calls,internal_calls,_,_,_ = get_contract_and_fn_names
    edges = get_edges
    #print(edges)
    solidity_functions = set()
    solidity_calls = set()
    contract_calls = defaultdict(set)
    combined_calls = internal_calls + sol_calls
    for function in function_dict:
        contract = function.contract_declarer
        print(contract.id)
        print(str(contract.id) in edges)
        assert contract.name in total_contracts  # sanity check we are getting the correct contracts
        for internal_fn in function.internal_calls:
            #print(internal_fn.name)
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
                assert internal_fn.name in sol_calls # sanity check we have solidity function
                sol_node = _solidity_function_node(internal_fn)
                edge = _edge(_function_node(function, top_level_dict), sol_node)
                print(edge)
                #print(edges)
                print(edge in edges)
                assert edge in edges
                new_edge = edge.strip().replace('"',"")
                sol_fns_trimmed = set()
                sol_calls_trimmed = set()
                for txt in solidity_functions:
                    new = txt.strip().replace('"',"")
                    sol_fns_trimmed.add(new)
                for txt in solidity_calls:
                    new = txt.strip().replace('"',"")
                    sol_calls_trimmed.add(new)

                assert sol_node in sol_fns_trimmed #nodes are correctly formed for solidity functions
                assert new_edge in sol_calls_trimmed #edges are correctly formed for solidity functions

            else:
                assert internal_fn.name in internal_calls
                edge = _edge(
                        _function_node(function, top_level_dict),
                        _function_node(internal_fn, top_level_dict),
                    )
                print(edge)
                #print(edges)
                print(edge in edges)
                assert edge in edges
                assert edge in contract_calls[contract] #sanity check edges are correctly formed for internal/toplevels
                assert(False)

def test_external_calls(setup,get_contract_and_fn_names, get_edges):
    _,_, total_contracts,_,_,external_calls,_,_ = get_contract_and_fn_names
    edges = get_edges



# "171_x3" -> "171_beExternal""171_beExternal" -> "12_test""TopLevelFunctions_TestTopLevels_setNumber" -> "12_test""286_increment" -> "171_beExternal""362_canTry" -> "TopLevelFunctions_TopLevelUsingFor_getBit""362_canDoThing" -> "TopLevelFunctions_TopLevelUsingFor_getBit""171_increment" -> "TopLevelFunctions_TopLevelImported_cry""171_x3" -> "TopLevelFunctions_TestTopLevels_setNumber""171_increment" -> "TopLevelFunctions_TestTopLevels_attempt""171_increment" -> "171_x3""171_increment" -> "362_canDoThing""171_x3" -> "95_hi""171_x3" -> "TopLevelFunctions_TestTopLevels_attempt""171_x3" -> "171_increment""171_x3" -> "TopLevelFunctions_TestTopLevels_fill""TopLevelFunctions_TestTopLevels_attempt" -> "TopLevelFunctions_TestTopLevels_setNumber""TopLevelFunctions_TestTopLevels_setNumber" -> "TopLevelFunctions_TestTopLevels_fill""TopLevelFunctions_TestTopLevels_fill" -> "TopLevelFunctions_TopLevelImported_cry""TopLevelFunctions_TopLevelImported_setNumber" -> "TopLevelFunctions_TopLevelImported_fill""TopLevelFunctions_TopLevelImported_cry" -> "TopLevelFunctions_TopLevelImported_setNumber""286_increment" -> "TopLevelFunctions_TopLevelImported_setNumber""286_x2" -> "TopLevelFunctions_TopLevelImported_cry""286_increment" -> "286_x2""286_a3" -> "TopLevelFunctions_TopLevelImported_cry""286_a3" -> "TopLevelFunctions_TopLevelImported_fill""286_a3" -> "286_increment""95_hi" -> "362_canDoThing""95_hi" -> "TopLevelFunctions_TopLevelUsingFor_getBit""95_hi" -> "TopLevelFunctions_TestTopLevels_setNumber""TopLevelFunctions_TopLevelImported_fill" -> "abi.encode()""286_a3" -> "abi.encode()""286_a3" -> "ecrecover(bytes32,uint8,bytes32,bytes32)""TopLevelFunctions_TestTopLevels_setNumber" -> "keccak256(bytes)""TopLevelFunctions_TopLevelImported_setNumber" -> "keccak256(bytes)""286_a3" -> "keccak256(bytes)""TopLevelFunctions_TestTopLevels_setNumber" -> "abi.encode()"
# "366_canDoThing" -> "TopLevelFunctions_TopLevelUsingFor_getBit"
