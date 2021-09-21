from typing import TYPE_CHECKING, Optional, Union, List, Tuple

from slither.core.declarations import Event, Enum, Structure
from slither.core.declarations.contract import Contract
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
from slither.core.solidity_types import (
    ArrayType,
    FunctionType,
    MappingType,
)
from slither.core.variables.variable import Variable
from slither.exceptions import SlitherError
from slither.solc_parsing.exceptions import VariableNotFound

if TYPE_CHECKING:
    from slither.solc_parsing.declarations.function import FunctionSolc
    from slither.solc_parsing.declarations.contract import ContractSolc
    from slither.solc_parsing.slither_compilation_unit_solc import SlitherCompilationUnitSolc
    from slither.core.compilation_unit import SlitherCompilationUnit

# pylint: disable=import-outside-toplevel,too-many-branches,too-many-locals


CallerContext = Union["ContractSolc", "FunctionSolc"]


def _get_pointer_name(variable: Variable):
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
    all_functions_parser: List["FunctionSolc"],
) -> Optional[Union[Contract, Function]]:
    if referenced_declaration is None:
        return None
    # id of the contracts is the referenced declaration
    # This is not true for the functions, as we dont always have the referenced_declaration
    # But maybe we could? (TODO)
    for contract_candidate in all_contracts:
        if contract_candidate.id == referenced_declaration:
            return contract_candidate
    for function_candidate in all_functions_parser:
        if (
            function_candidate.referenced_declaration == referenced_declaration
            and not function_candidate.underlying_function.is_shadowed
        ):
            return function_candidate.underlying_function
    return None


def _find_variable_in_function_parser(
    var_name: str,
    function_parser: Optional["FunctionSolc"],
    referenced_declaration: Optional[int] = None,
) -> Optional[Variable]:
    if function_parser is None:
        return None
    # We look for variable declared with the referencedDeclaration attr
    func_variables_renamed = function_parser.variables_renamed
    if referenced_declaration and referenced_declaration in func_variables_renamed:
        return func_variables_renamed[referenced_declaration].underlying_variable
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


def _find_top_level(
    var_name: str, sl: "SlitherCompilationUnit"
) -> Tuple[Optional[Union[Enum, Structure, SolidityImportPlaceHolder]], bool]:
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
    structures_top_level = sl.structures_top_level
    for st in structures_top_level:
        if st.name == var_name:
            return st, False

    enums_top_level = sl.enums_top_level
    for enum in enums_top_level:
        if enum.name == var_name:
            return enum, False

    for import_directive in sl.import_directives:
        if import_directive.alias == var_name:
            new_val = SolidityImportPlaceHolder(import_directive)
            return new_val, True

    return None, False


def _find_in_contract(
    var_name: str,
    contract: Optional[Contract],
    contract_declarer: Optional[Contract],
    is_super: bool,
) -> Optional[Union[Variable, Function, Contract, Event, Enum, Structure,]]:

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
        functions = contract.available_functions_as_dict()
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

    # If the enum is refered as its name rather than its canonicalName
    enums = {e.name: e for e in contract.enums}
    if var_name in enums:
        return enums[var_name]

    return None


def _find_variable_init(
    caller_context: CallerContext,
) -> Tuple[
    List[Contract],
    Union[List["FunctionSolc"]],
    "SlitherCompilationUnit",
    "SlitherCompilationUnitSolc",
]:
    from slither.solc_parsing.slither_compilation_unit_solc import SlitherCompilationUnitSolc
    from slither.solc_parsing.declarations.contract import ContractSolc
    from slither.solc_parsing.declarations.function import FunctionSolc

    direct_contracts: List[Contract]
    direct_functions_parser: List[FunctionSolc]

    if isinstance(caller_context, SlitherCompilationUnitSolc):
        direct_contracts = []
        direct_functions_parser = []
        sl = caller_context.compilation_unit
        sl_parser = caller_context
    elif isinstance(caller_context, ContractSolc):
        direct_contracts = [caller_context.underlying_contract]
        direct_functions_parser = caller_context.functions_parser + caller_context.modifiers_parser
        sl = caller_context.slither_parser.compilation_unit
        sl_parser = caller_context.slither_parser
    elif isinstance(caller_context, FunctionSolc):
        if caller_context.contract_parser:
            direct_contracts = [caller_context.contract_parser.underlying_contract]
            direct_functions_parser = (
                caller_context.contract_parser.functions_parser
                + caller_context.contract_parser.modifiers_parser
            )
        else:
            # Top level functions
            direct_contracts = []
            direct_functions_parser = []
        sl = caller_context.underlying_function.compilation_unit
        sl_parser = caller_context.slither_parser
    else:
        raise SlitherError(
            f"{type(caller_context)} ({caller_context} is not valid for find_variable"
        )

    return direct_contracts, direct_functions_parser, sl, sl_parser


def find_variable(
    var_name: str,
    caller_context: CallerContext,
    referenced_declaration: Optional[int] = None,
    is_super=False,
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
    :return:
    :rtype:
    """
    from slither.solc_parsing.declarations.function import FunctionSolc
    from slither.solc_parsing.declarations.contract import ContractSolc

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

    direct_contracts, direct_functions_parser, sl, sl_parser = _find_variable_init(caller_context)

    all_contracts = sl.contracts
    all_functions_parser = sl_parser.all_functions_and_modifiers_parser

    # Only look for reference declaration in the direct contract, see comment at the end
    # Reference looked are split between direct and all
    # Because functions are copied between contracts, two functions can have the same ref
    # So we need to first look with respect to the direct context

    ret = _find_variable_from_ref_declaration(
        referenced_declaration, direct_contracts, direct_functions_parser
    )
    if ret:
        return ret, False

    function_parser: Optional[FunctionSolc] = (
        caller_context if isinstance(caller_context, FunctionSolc) else None
    )
    ret = _find_variable_in_function_parser(var_name, function_parser, referenced_declaration)
    if ret:
        return ret, False

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

    ret = _find_in_contract(var_name, contract, contract_declarer, is_super)
    if ret:
        return ret, False

    # Could refer to any enum
    all_enumss = [c.enums_as_dict for c in sl.contracts]
    all_enums = {k: v for d in all_enumss for k, v in d.items()}
    if var_name in all_enums:
        return all_enums[var_name], False

    contracts = sl.contracts_as_dict
    if var_name in contracts:
        return contracts[var_name], False

    if var_name in SOLIDITY_VARIABLES:
        return SolidityVariable(var_name), False

    if var_name in SOLIDITY_FUNCTIONS:
        return SolidityFunction(var_name), False

    # Top level must be at the end, if nothing else was found
    ret, var_was_created = _find_top_level(var_name, sl)
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
        referenced_declaration, all_contracts, all_functions_parser
    )
    if ret:
        return ret, False

    raise VariableNotFound("Variable not found: {} (context {})".format(var_name, caller_context))
