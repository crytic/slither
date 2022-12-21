"""
Detects various properties of inheritance in provided contracts.
"""

from collections import defaultdict
from typing import TYPE_CHECKING, List, Dict, Set, Tuple

if TYPE_CHECKING:
    from slither.core.declarations import Contract, Function
    from slither.core.variables.state_variable import StateVariable


def detect_c3_function_shadowing(contract: "Contract",) -> Dict["Function", Set["Function"]]:
    """
    Detects and obtains functions which are indirectly shadowed via multiple inheritance by C3 linearization
    properties, despite not directly inheriting from each other.

    :param contract: The contract to check for potential C3 linearization shadowing within.
    :return: A dict (function winner -> [shadowed functions])
    """

    targets: Dict[str, "Function"] = {
        f.full_name: f
        for f in contract.functions_inherited
        if f.shadows and not f.is_constructor and not f.is_constructor_variables
    }

    collisions: Dict["Function", Set["Function"]] = defaultdict(set)

    for contract_inherited in contract.immediate_inheritance:
        for candidate in contract_inherited.functions:
            if candidate.full_name not in targets or candidate.is_shadowed:
                continue
            if targets[candidate.full_name].canonical_name != candidate.canonical_name:
                collisions[targets[candidate.full_name]].add(candidate)
    return collisions


def detect_state_variable_shadowing(
    contracts: List["Contract"],
) -> Set[Tuple["Contract", "StateVariable", "Contract", "StateVariable"]]:
    """
    Detects all overshadowing and overshadowed state variables in the provided contracts.
    :param contracts: The contracts to detect shadowing within.
    :return: Returns a set of tuples (overshadowing_contract, overshadowing_state_var, overshadowed_contract,
    overshadowed_state_var).
    The contract-variable pair's variable does not need to be defined in its paired contract, it may have been
    inherited. The contracts are simply included to denote the immediate inheritance path from which the shadowed
    variable originates.
    """
    results: Set[Tuple["Contract", "StateVariable", "Contract", "StateVariable"]] = set()
    for contract in contracts:
        variables_declared: Dict[str, "StateVariable"] = {
            variable.name: variable for variable in contract.state_variables_declared
        }
        for immediate_base_contract in contract.immediate_inheritance:
            for variable in immediate_base_contract.variables:
                if variable.name in variables_declared:
                    results.add(
                        (
                            contract,
                            variables_declared[variable.name],
                            immediate_base_contract,
                            variable,
                        )
                    )
    return results
