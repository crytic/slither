from typing import TYPE_CHECKING, Optional, Union, List, Tuple

from slither.core.declarations import Event, Enum, Structure
from slither.core.declarations.contract import Contract
from slither.core.declarations.custom_error import CustomError
from slither.core.declarations.custom_error_contract import CustomErrorContract
from slither.core.declarations.custom_error_top_level import CustomErrorTopLevel
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


def _get_pointer_name(variable: Variable) -> Optional[str]:
    curr_type = variable.type
    while isinstance(curr_type, (ArrayType, MappingType)):
        if isinstance(curr_type, ArrayType):
            curr_type = curr_type.type
        else:
            assert isinstance(curr_type, MappingType)
            curr_type = curr_type.type_to

    if isinstance(curr_type, FunctionType):
        return variable.name + curr_type.parameters_signature
    return None


def _find_variable_from_ref_declaration(
    referenced_declaration: Optional[int],
    all_contracts: List["Contract"],
    all_functions: List["Function"],
    function_parser: Optional["FunctionSolc"],
    contract_declarer: Optional["Contract"],
) -> Optional[Union[Contract, Function]]:
    """
    Reference declarations take the highest priority, but they are not available for legacy AST.
    """
    if referenced_declaration is None:
        return None
    # We look for variable declared with the referencedDeclaration attribute
    if function_parser is not None and referenced_declaration in function_parser.variables_renamed:
        return function_parser.variables_renamed[referenced_declaration].underlying_variable

    if (
        contract_declarer is not None
        and referenced_declaration in contract_declarer.state_variables_by_ref_id
    ):
        return contract_declarer.state_variables_by_ref_id[referenced_declaration]
    # Ccontracts  ids are the referenced declaration
    # This is not true for the functions, as we dont always have the referenced_declaration
    # But maybe we could? (TODO)
    for contract_candidate in all_contracts:
        if contract_candidate and contract_candidate.id == referenced_declaration:
            return contract_candidate
    for function_candidate in all_functions:
        if function_candidate.id == referenced_declaration and not function_candidate.is_shadowed:
            return function_candidate
    return None


def _find_variable_in_function_parser(
    var_name: str,
    function_parser: Optional["FunctionSolc"],
) -> Optional[Variable]:
    if function_parser is None:
        return None
    # If not found, check for name
    func_variables = function_parser.underlying_function.variables_as_dict
    if var_name in func_variables:
        return func_variables[var_name]
    # A local variable can be a pointer
    # for example
    # function test(function(uint) internal returns(bool) t) interna{
    # Will have a local variable t which will match the signature
    # t(uint256)
    func_variables_ptr = {
        _get_pointer_name(f): f for f in function_parser.underlying_function.variables
    }
    if var_name and var_name in func_variables_ptr:
        return func_variables_ptr[var_name]

    return None


def find_top_level(
    var_name: str, scope: "FileScope"
) -> Tuple[
    Optional[Union[Enum, Structure, SolidityImportPlaceHolder, CustomError, TopLevelVariable]], bool
]:
    """
    Return the top level variable use, and a boolean indicating if the variable returning was cretead
    If the variable was created, it has no source_mapping

    :param var_name:
    :type var_name:
    :param sl:
    :type sl:
    :return:
    :rtype:
    """
    if var_name in scope.type_aliases:
        return scope.type_aliases[var_name], False

    if var_name in scope.structures:
        return scope.structures[var_name], False

    if var_name in scope.enums:
        return scope.enums[var_name], False

    for import_directive in scope.imports:
        if import_directive.alias == var_name:
            new_val = SolidityImportPlaceHolder(import_directive)
            return new_val, True

    if var_name in scope.variables:
        return scope.variables[var_name], False

    # This path should be reached only after the top level custom error have been parsed
    # If not, slither will crash
    # It does not seem to be reacheable, but if so, we will have to adapt the order of logic
    # This must be at the end, because other top level objects might require to go over "_find_top_level"
    # Before the parsing of the top level custom error
    # For example, a top variable that use another top level variable
    # IF more top level objects are added to Solidity, we have to be careful with the order of the lookup
    # in this function
    try:
        for custom_error in scope.custom_errors:
            if custom_error.solidity_signature == var_name:
                return custom_error, False
    except ValueError:
        # This can happen as custom error sol signature might not have been built
        # when find_variable was called
        # TODO refactor find_variable to prevent this from happening
        pass

    return None, False


def _find_in_contract(
    var_name: str,
    contract: Optional[Contract],
    contract_declarer: Optional[Contract],
    is_super: bool,
    is_identifier_path: bool = False,
) -> Optional[Union[Variable, Function, Contract, Event, Enum, Structure, CustomError]]:
    if contract is None or contract_declarer is None:
        return None

    # variable are looked from the contract declarer
    contract_variables = contract_declarer.variables_as_dict
    if var_name in contract_variables:
        return contract_variables[var_name]

    # A state variable can be a pointer
    conc_variables_ptr = {_get_pointer_name(f): f for f in contract_declarer.variables}
    if var_name and var_name in conc_variables_ptr:
        return conc_variables_ptr[var_name]

    if is_super:
        getter_available = lambda f: f.functions_declared
        d = {f.canonical_name: f for f in contract.functions}
        functions = {
            f.full_name: f
            for f in contract_declarer.available_elements_from_inheritances(
                d, getter_available
            ).values()
        }
    else:
        functions = {f.full_name: f for f in contract.functions if not f.is_shadowed}
    if var_name in functions:
        return functions[var_name]

    if is_super:
        getter_available = lambda m: m.modifiers_declared
        d = {m.canonical_name: m for m in contract.modifiers}
        modifiers = {
            m.full_name: m
            for m in contract_declarer.available_elements_from_inheritances(
                d, getter_available
            ).values()
        }
    else:
        modifiers = contract.available_modifiers_as_dict()
    if var_name in modifiers:
        return modifiers[var_name]

    if is_identifier_path:
        for sig, modifier in modifiers.items():
            if "(" in sig:
                sig = sig[0 : sig.find("(")]
                if sig == var_name:
                    return modifier

    type_aliases = contract.type_aliases_as_dict
    if var_name in type_aliases:
        return type_aliases[var_name]

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


# pylint: disable=too-many-statements
def _find_variable_init(
    caller_context: CallerContextExpression,
) -> Tuple[List[Contract], List["Function"], FileScope,]:
    from slither.solc_parsing.declarations.contract import ContractSolc
    from slither.solc_parsing.declarations.function import FunctionSolc
    from slither.solc_parsing.declarations.structure_top_level import StructureTopLevelSolc
    from slither.solc_parsing.variables.top_level_variable import TopLevelVariableSolc
    from slither.solc_parsing.declarations.custom_error import CustomErrorSolc

    direct_contracts: List[Contract]
    direct_functions_parser: List[Function]
    scope: FileScope

    if isinstance(caller_context, FileScope):
        direct_contracts = []
        direct_functions_parser = []
        scope = caller_context
    elif isinstance(caller_context, ContractSolc):
        direct_contracts = [caller_context.underlying_contract]
        direct_functions_parser = [
            f.underlying_function
            for f in caller_context.functions_parser + caller_context.modifiers_parser
        ]
        scope = caller_context.underlying_contract.file_scope
    elif isinstance(caller_context, FunctionSolc):
        if caller_context.contract_parser:
            direct_contracts = [caller_context.contract_parser.underlying_contract]
            direct_functions_parser = [
                f.underlying_function
                for f in caller_context.contract_parser.functions_parser
                + caller_context.contract_parser.modifiers_parser
            ]
        else:
            # Top level functions
            direct_contracts = []
            direct_functions_parser = []
        underlying_function = caller_context.underlying_function
        if isinstance(underlying_function, FunctionTopLevel):
            scope = underlying_function.file_scope
        else:
            assert isinstance(underlying_function, FunctionContract)
            scope = underlying_function.contract.file_scope
    elif isinstance(caller_context, StructureTopLevelSolc):
        direct_contracts = []
        direct_functions_parser = []
        scope = caller_context.underlying_structure.file_scope
    elif isinstance(caller_context, TopLevelVariableSolc):
        direct_contracts = []
        direct_functions_parser = []
        scope = caller_context.underlying_variable.file_scope
    elif isinstance(caller_context, CustomErrorSolc):
        if caller_context.contract_parser:
            direct_contracts = [caller_context.contract_parser.underlying_contract]
            direct_functions_parser = [
                f.underlying_function
                for f in caller_context.contract_parser.functions_parser
                + caller_context.contract_parser.modifiers_parser
            ]
        else:
            # Top level custom error
            direct_contracts = []
            direct_functions_parser = []
        underlying_custom_error = caller_context.underlying_custom_error
        if isinstance(underlying_custom_error, CustomErrorTopLevel):
            scope = underlying_custom_error.file_scope
        else:
            assert isinstance(underlying_custom_error, CustomErrorContract)
            scope = underlying_custom_error.contract.file_scope
    else:
        raise SlitherError(
            f"{type(caller_context)} ({caller_context} is not valid for find_variable"
        )

    return direct_contracts, direct_functions_parser, scope


def find_variable(
    var_name: str,
    caller_context: CallerContextExpression,
    referenced_declaration: Optional[int] = None,
    is_super: bool = False,
    is_identifier_path: bool = False,
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
    :type referenced_declaration:
    :param is_super:
    :type is_super:
    :param is_identifier_path:
    :type is_identifier_path:
    :return:
    :rtype:
    """
    from slither.solc_parsing.declarations.function import FunctionSolc
    from slither.solc_parsing.declarations.contract import ContractSolc
    from slither.solc_parsing.declarations.custom_error import CustomErrorSolc

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

    direct_contracts, direct_functions, current_scope = _find_variable_init(caller_context)
    # Only look for reference declaration in the direct contract, see comment at the end
    # Reference looked are split between direct and all
    # Because functions are copied between contracts, two functions can have the same ref
    # So we need to first look with respect to the direct context

    if var_name in current_scope.renaming:
        var_name = current_scope.renaming[var_name]

    contract: Optional[Contract] = None
    contract_declarer: Optional[Contract] = None
    if isinstance(caller_context, ContractSolc):
        contract = caller_context.underlying_contract
        contract_declarer = caller_context.underlying_contract
    elif isinstance(caller_context, FunctionSolc):
        underlying_func = caller_context.underlying_function
        if isinstance(underlying_func, FunctionContract):
            contract = underlying_func.contract
            contract_declarer = underlying_func.contract_declarer
        else:
            assert isinstance(underlying_func, FunctionTopLevel)
    elif isinstance(caller_context, CustomErrorSolc):
        underlying_custom_error = caller_context.underlying_custom_error
        if isinstance(underlying_custom_error, CustomErrorContract):
            contract = underlying_custom_error.contract
            # We check for contract variables here because _find_in_contract
            # will return since in this case the contract_declarer is None
            for var in contract.variables:
                if var_name == var.name:
                    return var, False

    function_parser: Optional[FunctionSolc] = (
        caller_context if isinstance(caller_context, FunctionSolc) else None
    )
    # Use ret0/ret1 to help mypy
    ret0 = _find_variable_from_ref_declaration(
        referenced_declaration,
        direct_contracts,
        direct_functions,
        function_parser,
        contract_declarer,
    )
    if ret0:
        return ret0, False

    ret1 = _find_variable_in_function_parser(var_name, function_parser)
    if ret1:
        return ret1, False

    ret = _find_in_contract(var_name, contract, contract_declarer, is_super, is_identifier_path)
    if ret:
        return ret, False

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

    # Top level must be at the end, if nothing else was found
    ret, var_was_created = find_top_level(var_name, current_scope)
    if ret:
        return ret, var_was_created

    # Look from reference declaration in all the contracts at the end
    # Because they are many instances where this can't be trusted
    # For example in
    # contract A{
    #     function _f() internal view returns(uint){
    #         return 1;
    #     }
    #
    #     function get() public view returns(uint){
    #         return _f();
    #     }
    # }
    #
    # contract B is A{
    #     function _f() internal view returns(uint){
    #         return 2;
    #     }
    #
    # }
    # get's AST will say that the ref declaration for _f() is A._f(), but in the context of B, its not

    ret = _find_variable_from_ref_declaration(
        referenced_declaration,
        list(current_scope.contracts.values()),
        list(current_scope.functions),
        None,
        None,
    )
    if ret:
        return ret, False

    raise VariableNotFound(f"Variable not found: {var_name} (context {contract})")
