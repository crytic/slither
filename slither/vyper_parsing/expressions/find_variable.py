from typing import TYPE_CHECKING, Optional, Union, Tuple

from slither.core.declarations import Event, Enum, Structure
from slither.core.declarations.contract import Contract
from slither.core.declarations.custom_error import CustomError
from slither.core.declarations.function import Function
from slither.core.declarations.function_contract import FunctionContract
from slither.core.declarations.solidity_variables import (
    SOLIDITY_FUNCTIONS,
    SOLIDITY_VARIABLES,
    SolidityFunction,
    SolidityVariable,
)
from slither.core.variables.variable import Variable
from slither.solc_parsing.exceptions import VariableNotFound

if TYPE_CHECKING:
    from slither.vyper_parsing.declarations.function import FunctionVyper


def _find_variable_in_function_parser(
    var_name: str,
    function_parser: Optional["FunctionVyper"],
) -> Optional[Variable]:
    if function_parser is None:
        return None
    func_variables = function_parser.variables_as_dict
    if var_name in func_variables:
        return func_variables[var_name]

    return None


def _find_in_contract(
    var_name: str,
    contract: Optional[Contract],
    contract_declarer: Optional[Contract],
) -> Optional[Union[Variable, Function, Contract, Event, Enum, Structure, CustomError]]:
    if contract is None or contract_declarer is None:
        return None

    # variable are looked from the contract declarer
    contract_variables = contract.variables_as_dict
    if var_name in contract_variables:
        return contract_variables[var_name]

    functions = {f.name: f for f in contract.functions if not f.is_shadowed}
    if var_name in functions:
        return functions[var_name]

    # structures are looked on the contract declarer
    structures = contract.structures_as_dict
    if var_name in structures:
        return structures[var_name]

    events = contract.events_as_dict
    if var_name in events:
        return events[var_name]

    enums = contract.enums_as_dict
    if var_name in enums:
        return enums[var_name]

    # If the enum is referred as its name rather than its canonicalName
    enums = {e.name: e for e in contract.enums}
    if var_name in enums:
        return enums[var_name]

    return None


def find_variable(
    var_name: str,
    caller_context: Union[FunctionContract, Contract],
    is_self: bool = False,
) -> Tuple[
    Union[
        Variable,
        Function,
        Contract,
        SolidityVariable,
        SolidityFunction,
        Event,
        Enum,
        Structure,
    ]
]:
    """
    Return the variable found and a boolean indicating if the variable was created
    If the variable was created, it has no source mapping, and it the caller must add it

    :param var_name:
    :type var_name:
    :param caller_context:
    :type caller_context:
    :param is_self:
    :type is_self:
    :return:
    :rtype:
    """
    # pylint: disable=import-outside-toplevel
    from slither.vyper_parsing.declarations.function import (
        FunctionVyper,
    )

    if isinstance(caller_context, Contract):
        current_scope = caller_context.file_scope
        next_context = caller_context
    else:
        current_scope = caller_context.contract.file_scope
        next_context = caller_context.contract

    function_parser: Optional[FunctionVyper] = (
        caller_context if isinstance(caller_context, FunctionContract) else None
    )

    # If a local shadows a state variable but the attribute is `self`, we want to
    # return the state variable and not the local.
    if not is_self:
        ret1 = _find_variable_in_function_parser(var_name, function_parser)
        if ret1:
            return ret1

    ret = _find_in_contract(var_name, next_context, caller_context)
    if ret:
        return ret

    if var_name in current_scope.variables:
        return current_scope.variables[var_name]

    # Could refer to any enum
    all_enumss = [c.enums_as_dict for c in current_scope.contracts.values()]
    all_enums = {k: v for d in all_enumss for k, v in d.items()}
    if var_name in all_enums:
        return all_enums[var_name]

    contracts = current_scope.contracts
    if var_name in contracts:
        return contracts[var_name]

    if var_name in SOLIDITY_VARIABLES:
        return SolidityVariable(var_name)

    if f"{var_name}()" in SOLIDITY_FUNCTIONS:
        return SolidityFunction(f"{var_name}()")

    if f"{var_name}()" in next_context.events_as_dict:
        return next_context.events_as_dict[f"{var_name}()"]

    raise VariableNotFound(f"Variable not found: {var_name} (context {caller_context})")
