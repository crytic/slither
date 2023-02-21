from slither import Slither
from slither.printers.call.call_graph import _create_dummy_declarers, _process_function
from slither.core.declarations.function_top_level import FunctionTopLevel
from slither.core.declarations.function import Function
from collections import defaultdict
import pytest


@pytest.fixture
def setup():
    sl = Slither("tests/printers/TestTopLevels.sol")
    all_functionss = [compilation_unit.functions for compilation_unit in sl.compilation_units]
    all_functions = [item for sublist in all_functionss for item in sublist]
    for func in all_functions:
        assert isinstance(func, (Function))  # sanity check we are getting functions
    top_levels = [compilation_unit.functions_top_level for compilation_unit in sl.compilation_units]
    top_levels_flat = [item for sublist in top_levels for item in sublist]
    for func in top_levels_flat:
        assert isinstance(
            func, (FunctionTopLevel)
        )  # sanity check we are getting top level functions
    top_level_dict = _create_dummy_declarers(top_levels_flat)
    dummy_contract_names = [
        "TopLevel_TopLevelImported",
        "TopLevel_TestTopLevels",
        "TopLevel_TopLevelUsingFor",
    ]
    for contract in top_level_dict.values():
        assert contract.name in dummy_contract_names #check we process the top level fns correctly

    regular_function_dict = {
            function.canonical_name: function for function in all_functions if function not in top_level_dict
        }
    return (regular_function_dict.values(),top_level_dict)

def stringify(target):
    return "".join("".join(target))

def test_processing(setup):
    #print(filter_functions)
    function_dict, top_level_dict = setup
    contracts = ["TestTopLevels", "TopLevelImported", "TestTopLevelInherit", "TopLevelUsingFor", "[Solidity]"]
    dummy_contract_names = [
        "TopLevel_TopLevelImported",
        "TopLevel_TestTopLevels",
        "TopLevel_TopLevelUsingFor",
    ]
    total_contracts = contracts + dummy_contract_names
    sol_fns = ["ecrecover(bytes32,uint8,bytes32,bytes32)","abi.encode()","keccak256(bytes)"]
    reg_fns = ["increment()","hi()","x3()","a3()","x2()","canDoThing()","canTry()","getBit(Bitmap,uint8)"]
    external_fns = ["test()","beExternal()"]
    top_level_fns = ["fill(uint256)","attempt(uint256)","setNumber(uint256)","cry(uint256)"]
    total_functions = reg_fns + top_level_fns + external_fns
    #State to pass around, copied for more granularity
    contract_functions = defaultdict(set)  # contract -> contract functions nodes
    contract_calls = defaultdict(set)  # contract -> contract calls edges

    solidity_functions = set()  # solidity function nodes
    solidity_calls = set()  # solidity calls edges
    external_calls = set()  # external calls edges

    all_contracts = set()
    for function in function_dict:
        all_contracts.add(function.contract_declarer)

    for function in function_dict:
        _process_function(
            function.contract_declarer,
            function,
            contract_functions,
            contract_calls,
            solidity_functions,
            solidity_calls,
            external_calls,
            all_contracts,
            top_level_dict,
        )

    for top_level in top_level_dict.keys():
        all_contracts.add(top_level_dict[top_level])
    for top_level in top_level_dict.keys():
        _process_function(
                top_level_dict[top_level],
                top_level,
                contract_functions,
                contract_calls,
                solidity_functions,
                solidity_calls,
                external_calls,
                all_contracts,
                top_level_dict,
            )
    #Assertions:

    assert(contract in all_contracts for contract in total_contracts) #we analyzed all contracts +dummys
    for sol in solidity_functions:
        sol = sol.replace("\"","").strip()
        assert sol in sol_fns #we successfully added every solidity function
    my_str = ""
    for val in contract_functions.values():
        my_str += stringify(val)

    for fn in total_functions:
        stripped = fn[:fn.find("(")]
        print(stripped)
        analyzed = stripped in my_str
        print(analyzed)
        assert analyzed # we sucessfully hit every function

    external_calls_stringified = stringify(external_calls)
    for ex in external_fns:
        stripped = ex[:ex.find("(")]
        assert stripped in external_calls_stringified  #external calls are correctly added





