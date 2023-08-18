from typing import TYPE_CHECKING, Optional, Union, List, Tuple

from slither.core.declarations import Event, Enum, Structure
from slither.core.declarations.contract import Contract
from slither.core.declarations.custom_error import CustomError
from slither.core.declarations.function import Function
from slither.core.declarations.function_contract import FunctionContract
from slither.core.declarations.function_top_level import FunctionTopLevel
from slither.core.declarations.solidity_import_placeholder import SolidityImportPlaceHolder
from slither.core.declarations.solidity_variables import (
    SOLIDITY_FUNCTIONS,
    SOLIDITY_VARIABLES,
    SolidityFunction,
    SolidityVariable,
)
from slither.core.scope.scope import FileScope
from slither.core.solidity_types import (
    ArrayType,
    FunctionType,
    MappingType,
    TypeAlias,
)
from slither.core.variables.top_level_variable import TopLevelVariable
from slither.core.variables.variable import Variable
from slither.exceptions import SlitherError
from slither.solc_parsing.declarations.caller_context import CallerContextExpression
from slither.solc_parsing.exceptions import VariableNotFound

if TYPE_CHECKING:
    from slither.solc_parsing.declarations.function import FunctionSolc
    from slither.solc_parsing.declarations.contract import ContractSolc

# pylint: disable=import-outside-toplevel,too-many-branches,too-many-locals


# CallerContext =Union["ContractSolc", "FunctionSolc", "CustomErrorSolc", "StructureTopLevelSolc"]



def _find_variable_in_function_parser(
    var_name: str,
    function_parser: Optional["FunctionSolc"],
) -> Optional[Variable]:
    if function_parser is None:
        return None
    func_variables = function_parser.underlying_function.variables_as_dict
    print("func_variables", func_variables)
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
    print(contract)
    contract_variables = contract.variables_as_dict
    print(contract_variables)
    if var_name in contract_variables:
        return contract_variables[var_name]



    functions = {f.name: f for f in contract.functions if not f.is_shadowed}
    print(functions)
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

    # Note: contract.custom_errors_as_dict uses the name (not the sol sig) as key
    # This is because when the dic is populated the underlying object is not yet parsed
    # As a result, we need to iterate over all the custom errors here instead of using the dict
    custom_errors = contract.custom_errors
    try:
        for custom_error in custom_errors:
            if var_name in [custom_error.solidity_signature, custom_error.full_name]:
                return custom_error
    except ValueError:
        # This can happen as custom error sol signature might not have been built
        # when find_variable was called
        # TODO refactor find_variable to prevent this from happening
        pass

    # If the enum is refered as its name rather than its canonicalName
    enums = {e.name: e for e in contract.enums}
    if var_name in enums:
        return enums[var_name]


    return None


def _find_variable_init(
    caller_context: CallerContextExpression,
) -> Tuple[List[Contract], List["Function"], FileScope,]:
    from slither.vyper_parsing.declarations.contract import ContractVyper
    from slither.vyper_parsing.declarations.function import FunctionVyper


    direct_contracts: List[Contract]
    direct_functions_parser: List[Function]
    scope: FileScope

    if isinstance(caller_context, FileScope):
        direct_contracts = []
        direct_functions_parser = []
        scope = caller_context
    elif isinstance(caller_context, ContractVyper):
        direct_contracts = [caller_context.underlying_contract]
        direct_functions_parser = [
            f.underlying_function
            for f in caller_context.functions_parser + caller_context.modifiers_parser
        ]
        scope = caller_context.underlying_contract.file_scope
    elif isinstance(caller_context, FunctionVyper):

        direct_contracts = [caller_context.underlying_contract]
        direct_functions_parser = [
            f.underlying_function
            for f in caller_context.functions_parser
        ]


        scope = contract.file_scope
    else:
        raise SlitherError(
            f"{type(caller_context)} ({caller_context} is not valid for find_variable"
        )

    return direct_contracts, direct_functions_parser, scope


def find_variable(
    var_name: str,
    caller_context: CallerContextExpression,
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
        CustomError,
        TypeAlias,
    ],
    bool,
]:
    """
    Return the variable found and a boolean indicating if the variable was created
    If the variable was created, it has no source mapping, and it the caller must add it

    :param var_name:
    :type var_name:
    :param caller_context:
    :type caller_context:
    :param referenced_declaration:
    :return:
    :rtype:
    """

    # variable are looked from the contract declarer
    # functions can be shadowed, but are looked from the contract instance, rather than the contract declarer
    # the difference between function and variable come from the fact that an internal call, or an variable access
    # in a function does not behave similariy, for example in:
    # contract C{
    #   function f(){
    #     state_var = 1
    #     f2()
    #  }
    # state_var will refer to C.state_var, no mater if C is inherited
    # while f2() will refer to the function definition of the inherited contract (C.f2() in the context of C, or
    # the contract inheriting from C)
    # for events it's unclear what should be the behavior, as they can be shadowed, but there is not impact
    # structure/enums cannot be shadowed

    direct_contracts = [caller_context]
    direct_functions = caller_context.functions_declared
    print(direct_functions)
    current_scope = caller_context.file_scope

    # Only look for reference declaration in the direct contract, see comment at the end
    # Reference looked are split between direct and all
    # Because functions are copied between contracts, two functions can have the same ref
    # So we need to first look with respect to the direct context

    from slither.vyper_parsing.declarations.contract import ContractVyper
    from slither.vyper_parsing.declarations.function import FunctionVyper
    function_parser: Optional[FunctionVyper] = (
        caller_context if isinstance(caller_context, FunctionVyper) else None
    )
    print("function_parser", function_parser)
    ret1 = _find_variable_in_function_parser(var_name, function_parser)
    if ret1:
        return ret1, False

    ret = _find_in_contract(var_name, caller_context, caller_context)
    if ret:
        return ret, False

    print(current_scope.variables)
    if var_name in current_scope.variables:
        return current_scope.variables[var_name], False

    # Could refer to any enum
    all_enumss = [c.enums_as_dict for c in current_scope.contracts.values()]
    all_enums = {k: v for d in all_enumss for k, v in d.items()}
    if var_name in all_enums:
        return all_enums[var_name], False

    contracts = current_scope.contracts
    if var_name in contracts:
        return contracts[var_name], False

    if var_name in SOLIDITY_VARIABLES:
        return SolidityVariable(var_name), False

    if var_name in SOLIDITY_FUNCTIONS:
        return SolidityFunction(var_name), False



    raise VariableNotFound(f"Variable not found: {var_name} (context {caller_context})")
