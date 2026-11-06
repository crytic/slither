from types import SimpleNamespace

import pytest

from slither.analyses.data_dependency.data_dependency import (
    GENERIC_TAINT,
    KEY_INPUT,
    KEY_INPUT_SSA,
    KEY_NON_SSA,
    KEY_NON_SSA_UNPROTECTED,
    KEY_SSA,
    KEY_SSA_UNPROTECTED,
    is_tainted,
    is_tainted_ssa,
)
from slither.core.declarations import Contract, SolidityVariableComposed
from slither.core.variables.local_variable import LocalVariable
from slither.slithir.variables import Constant


@pytest.mark.parametrize(
    "query,input_key,dependency_key,unprotected_key",
    [
        (is_tainted, KEY_INPUT, KEY_NON_SSA, KEY_NON_SSA_UNPROTECTED),
        (is_tainted_ssa, KEY_INPUT_SSA, KEY_SSA, KEY_SSA_UNPROTECTED),
    ],
)
def test_taint_queries_observe_current_context(query, input_key, dependency_key, unprotected_key):
    source, target, unrelated = LocalVariable(), LocalVariable(), LocalVariable()
    unit = SimpleNamespace(context={input_key: set()})
    contract = Contract(unit, None)

    # Empty input sets and constants do not require computed dependency maps.
    assert not query(target, contract, ignore_generic_taint=True)
    assert not query(Constant("1"), contract)
    unit.context[input_key].add(source)
    assert query(source, contract, ignore_generic_taint=True)

    contract.context[dependency_key] = {target: {source}}
    contract.context[unprotected_key] = {target: {unrelated}}
    assert query(target, contract, ignore_generic_taint=True)
    assert not query(target, contract, only_unprotected=True, ignore_generic_taint=True)
    assert not query(unrelated, contract, ignore_generic_taint=True)

    # Changes to either side must affect the next query (no stale memoization).
    unit.context[input_key].clear()
    assert not query(target, contract, ignore_generic_taint=True)
    unit.context[input_key].add(unrelated)
    assert query(target, contract, only_unprotected=True, ignore_generic_taint=True)
    contract.context[unprotected_key][target].clear()
    assert not query(target, contract, only_unprotected=True, ignore_generic_taint=True)

    # Preserve the existing generic-taint union into the compilation-unit inputs.
    contract.context[dependency_key][target] = {SolidityVariableComposed("msg.sender")}
    assert not query(target, contract, ignore_generic_taint=True)
    assert query(target, contract)
    assert GENERIC_TAINT <= unit.context[input_key]
    assert query(target, contract, ignore_generic_taint=True)


@pytest.mark.parametrize("ssa", [False, True])
def test_taint_queries_match_dependency_queries(slither_from_solidity_source, ssa):
    from slither.analyses.data_dependency.data_dependency import is_dependent, is_dependent_ssa

    source = """
    pragma solidity ^0.8.19;
    contract C {
        uint value;
        function f(uint x) external { value = x + 1; }
        function g(uint y) external { uint z = value + y; value = z; }
    }
    """
    with slither_from_solidity_source(source) as slither:
        contract = slither.contracts[0]
        query = is_tainted_ssa if ssa else is_tainted
        dependent = is_dependent_ssa if ssa else is_dependent
        input_key = KEY_INPUT_SSA if ssa else KEY_INPUT
        dependency_key = KEY_SSA if ssa else KEY_NON_SSA
        for function in contract.functions_declared:
            for context in [contract, function, *function.nodes]:
                for variable in function.context[dependency_key]:
                    for unprotected in [False, True]:
                        taints = contract.compilation_unit.context[input_key]
                        expected = variable in taints or any(
                            dependent(variable, t, context, unprotected) for t in taints
                        )
                        assert query(variable, context, unprotected, True) == expected
