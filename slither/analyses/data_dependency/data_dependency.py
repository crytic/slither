"""
    Compute the data depenency between all the SSA variables
"""
from collections import defaultdict
from typing import Union, Set, Dict, TYPE_CHECKING, List

from slither.core.cfg.node import Node
from slither.core.declarations import (
    Contract,
    Enum,
    Function,
    SolidityFunction,
    SolidityVariable,
    SolidityVariableComposed,
    Structure,
    FunctionContract,
)
from slither.core.declarations.solidity_import_placeholder import SolidityImportPlaceHolder
from slither.core.solidity_types.type import Type
from slither.core.variables.top_level_variable import TopLevelVariable
from slither.core.variables.variable import Variable
from slither.slithir.operations import Index, OperationWithLValue, InternalCall, Operation
from slither.slithir.utils.utils import LVALUE
from slither.slithir.variables import (
    Constant,
    LocalIRVariable,
    ReferenceVariable,
    ReferenceVariableSSA,
    StateIRVariable,
    TemporaryVariableSSA,
    TupleVariableSSA,
)
from slither.slithir.variables.variable import SlithIRVariable

if TYPE_CHECKING:
    from slither.core.compilation_unit import SlitherCompilationUnit

###################################################################################
###################################################################################
# region User APIs
###################################################################################
###################################################################################


SUPPORTED_TYPES = Union[Variable, SolidityVariable]

# TODO refactor the data deps to be better suited for top level function object
# Right now we allow to pass a node to ease the API, but we need something
# better
# The deps propagation for top level elements is also not working as expected
Context_types_API = Union[Contract, Function, Node]
Context_types = Union[Contract, Function]


def is_dependent(
    variable: SUPPORTED_TYPES,
    source: SUPPORTED_TYPES,
    context: Context_types_API,
    only_unprotected: bool = False,
) -> bool:
    """
    If Node is provided as context, the context will be the broader context, either the contract or the function,
    depending on if the node is in a top level function or not

    Args:
        variable (Variable)
        source (Variable)
        context (Contract|Function|Node).
        only_unprotected (bool): True only unprotected function are considered
    Returns:
        bool
    """
    assert isinstance(context, (Contract, Function, Node))
    if isinstance(context, Node):
        func = context.function
        context = func.contract if isinstance(func, FunctionContract) else func

    if isinstance(variable, Constant):
        return False
    if variable == source:
        return True
    context_dict = context.context

    if only_unprotected:
        return (
            variable in context_dict[KEY_NON_SSA_UNPROTECTED]
            and source in context_dict[KEY_NON_SSA_UNPROTECTED][variable]
        )
    return variable in context_dict[KEY_NON_SSA] and source in context_dict[KEY_NON_SSA][variable]


def is_dependent_ssa(
    variable: SUPPORTED_TYPES,
    source: SUPPORTED_TYPES,
    context: Context_types_API,
    only_unprotected: bool = False,
) -> bool:
    """
    If Node is provided as context, the context will be the broader context, either the contract or the function,
    depending on if the node is in a top level function or not

    Args:
        variable (Variable)
        taint (Variable)
        context (Contract|Function)
        only_unprotected (bool): True only unprotected function are considered
    Returns:
        bool
    """
    assert isinstance(context, (Contract, Function, Node))
    if isinstance(context, Node):
        func = context.function
        context = func.contract if isinstance(func, FunctionContract) else func
    context_dict = context.context
    if isinstance(variable, Constant):
        return False
    if variable == source:
        return True
    if only_unprotected:
        return (
            variable in context_dict[KEY_SSA_UNPROTECTED]
            and source in context_dict[KEY_SSA_UNPROTECTED][variable]
        )
    return variable in context_dict[KEY_SSA] and source in context_dict[KEY_SSA][variable]


GENERIC_TAINT = {
    SolidityVariableComposed("msg.sender"),
    SolidityVariableComposed("msg.value"),
    SolidityVariableComposed("msg.data"),
    SolidityVariableComposed("tx.origin"),
    SolidityVariableComposed("tx.gasprice"),
}


def is_tainted(
    variable: SUPPORTED_TYPES,
    context: Context_types_API,
    only_unprotected: bool = False,
    ignore_generic_taint: bool = False,
) -> bool:
    """
    If Node is provided as context, the context will be the broader context, either the contract or the function,
    depending on if the node is in a top level function or not

        Args:
        variable
        context (Contract|Function)
        only_unprotected (bool): True only unprotected function are considered
    Returns:
        bool
    """
    assert isinstance(context, (Contract, Function, Node))
    if isinstance(context, Node):
        func = context.function
        context = func.contract if isinstance(func, FunctionContract) else func
    assert isinstance(only_unprotected, bool)
    if isinstance(variable, Constant):
        return False
    compilation_unit = context.compilation_unit
    taints = compilation_unit.context[KEY_INPUT]
    if not ignore_generic_taint:
        taints |= GENERIC_TAINT
    return variable in taints or any(
        is_dependent(variable, t, context, only_unprotected) for t in taints
    )


def is_tainted_ssa(
    variable: SUPPORTED_TYPES,
    context: Context_types_API,
    only_unprotected: bool = False,
    ignore_generic_taint: bool = False,
) -> bool:
    """
    If Node is provided as context, the context will be the broader context, either the contract or the function,
    depending on if the node is in a top level function or not

    Args:
        variable
        context (Contract|Function)
        only_unprotected (bool): True only unprotected function are considered
    Returns:
        bool
    """
    assert isinstance(context, (Contract, Function, Node))
    if isinstance(context, Node):
        func = context.function
        context = func.contract if isinstance(func, FunctionContract) else func
    assert isinstance(only_unprotected, bool)
    if isinstance(variable, Constant):
        return False
    compilation_unit = context.compilation_unit
    taints = compilation_unit.context[KEY_INPUT_SSA]
    if not ignore_generic_taint:
        taints |= GENERIC_TAINT
    return variable in taints or any(
        is_dependent_ssa(variable, t, context, only_unprotected) for t in taints
    )


def get_dependencies(
    variable: SUPPORTED_TYPES,
    context: Context_types_API,
    only_unprotected: bool = False,
) -> Set[Variable]:
    """
    Return the variables for which `variable` depends on.
    If Node is provided as context, the context will be the broader context, either the contract or the function,
    depending on if the node is in a top level function or not

    :param variable: The target
    :param context: Either a function (interprocedural) or a contract (inter transactional)
    :param only_unprotected: True if consider only protected functions
    :return: set(Variable)
    """
    assert isinstance(context, (Contract, Function, Node))
    if isinstance(context, Node):
        func = context.function
        context = func.contract if isinstance(func, FunctionContract) else func
    assert isinstance(only_unprotected, bool)
    if only_unprotected:
        return context.context[KEY_NON_SSA_UNPROTECTED].get(variable, set())
    return context.context[KEY_NON_SSA].get(variable, set())


def get_all_dependencies(
    context: Context_types_API, only_unprotected: bool = False
) -> Dict[Variable, Set[Variable]]:
    """
    Return the dictionary of dependencies.
    If Node is provided as context, the context will be the broader context, either the contract or the function,
    depending on if the node is in a top level function or not

    :param context: Either a function (interprocedural) or a contract (inter transactional)
    :param only_unprotected: True if consider only protected functions
    :return: Dict(Variable, set(Variable))
    """
    assert isinstance(context, (Contract, Function, Node))
    if isinstance(context, Node):
        func = context.function
        context = func.contract if isinstance(func, FunctionContract) else func
    assert isinstance(only_unprotected, bool)
    if only_unprotected:
        return context.context[KEY_NON_SSA_UNPROTECTED]
    return context.context[KEY_NON_SSA]


def get_dependencies_ssa(
    variable: SUPPORTED_TYPES,
    context: Context_types_API,
    only_unprotected: bool = False,
) -> Set[Variable]:
    """
    Return the variables for which `variable` depends on (SSA version).
    If Node is provided as context, the context will be the broader context, either the contract or the function,
    depending on if the node is in a top level function or not

    :param variable: The target (must be SSA variable)
    :param context: Either a function (interprocedural) or a contract (inter transactional)
    :param only_unprotected: True if consider only protected functions
    :return: set(Variable)
    """
    assert isinstance(context, (Contract, Function, Node))
    if isinstance(context, Node):
        func = context.function
        context = func.contract if isinstance(func, FunctionContract) else func
    assert isinstance(only_unprotected, bool)
    if only_unprotected:
        return context.context[KEY_SSA_UNPROTECTED].get(variable, set())
    return context.context[KEY_SSA].get(variable, set())


def get_all_dependencies_ssa(
    context: Context_types_API, only_unprotected: bool = False
) -> Dict[Variable, Set[Variable]]:
    """
    Return the dictionary of dependencies.
    If Node is provided as context, the context will be the broader context, either the contract or the function,
    depending on if the node is in a top level function or not

    :param context: Either a function (interprocedural) or a contract (inter transactional)
    :param only_unprotected: True if consider only protected functions
    :return: Dict(Variable, set(Variable))
    """
    assert isinstance(context, (Contract, Function, Node))
    if isinstance(context, Node):
        func = context.function
        context = func.contract if isinstance(func, FunctionContract) else func
    assert isinstance(only_unprotected, bool)
    if only_unprotected:
        return context.context[KEY_SSA_UNPROTECTED]
    return context.context[KEY_SSA]


# endregion
###################################################################################
###################################################################################
# region Module constants
###################################################################################
###################################################################################

KEY_SSA = "DATA_DEPENDENCY_SSA"
KEY_NON_SSA = "DATA_DEPENDENCY"

# Only for unprotected functions
KEY_SSA_UNPROTECTED = "DATA_DEPENDENCY_SSA_UNPROTECTED"
KEY_NON_SSA_UNPROTECTED = "DATA_DEPENDENCY_UNPROTECTED"

KEY_INPUT = "DATA_DEPENDENCY_INPUT"
KEY_INPUT_SSA = "DATA_DEPENDENCY_INPUT_SSA"


# endregion
###################################################################################
###################################################################################
# region Debug
###################################################################################
###################################################################################


def pprint_dependency(caller_context: Context_types) -> None:
    print("#### SSA ####")
    context = caller_context.context
    for k, values in context[KEY_SSA].items():
        print(f"{k} ({id(k)}):")
        for v in values:
            print(f"\t- {v}")

    print("#### NON SSA ####")
    for k, values in context[KEY_NON_SSA].items():
        print(f"{k} ({hex(id(k))}):")
        for v in values:
            print(f"\t- {v} ({hex(id(v))})")


# endregion
###################################################################################
###################################################################################
# region Analyses
###################################################################################
###################################################################################


def compute_dependency(compilation_unit: "SlitherCompilationUnit") -> None:
    compilation_unit.context[KEY_INPUT] = set()
    compilation_unit.context[KEY_INPUT_SSA] = set()

    for contract in compilation_unit.contracts:
        compute_dependency_contract(contract, compilation_unit)


def compute_dependency_contract(
    contract: Contract, compilation_unit: "SlitherCompilationUnit"
) -> None:
    if KEY_SSA in contract.context:
        return

    contract.context[KEY_SSA] = {}
    contract.context[KEY_SSA_UNPROTECTED] = {}

    for function in contract.functions + list(contract.modifiers):
        compute_dependency_function(function)

        propagate_function(contract, function, KEY_SSA, KEY_NON_SSA)
        propagate_function(contract, function, KEY_SSA_UNPROTECTED, KEY_NON_SSA_UNPROTECTED)

        # pylint: disable=expression-not-assigned
        if function.visibility in ["public", "external"]:
            [compilation_unit.context[KEY_INPUT].add(p) for p in function.parameters]
            [compilation_unit.context[KEY_INPUT_SSA].add(p) for p in function.parameters_ssa]

    propagate_contract(contract, KEY_SSA, KEY_NON_SSA)
    propagate_contract(contract, KEY_SSA_UNPROTECTED, KEY_NON_SSA_UNPROTECTED)


def propagate_function(
    contract: Contract, function: Function, context_key: str, context_key_non_ssa: str
) -> None:
    transitive_close_dependencies(function, context_key, context_key_non_ssa)
    # Propage data dependency
    data_depencencies = function.context[context_key]
    for (key, values) in data_depencencies.items():
        if not key in contract.context[context_key]:
            contract.context[context_key][key] = set(values)
        else:
            contract.context[context_key][key].union(values)


def transitive_close_dependencies(
    context: Context_types, context_key: str, context_key_non_ssa: str
) -> None:
    # transitive closure
    changed = True
    keys = context.context[context_key].keys()
    while changed:
        changed = False
        to_add = defaultdict(set)
        for key, items in context.context[context_key].items():
            for item in items & keys:
                to_add[key].update(context.context[context_key][item] - {key} - items)
        for k, v in to_add.items():
            # Because we dont have any check on the update operation
            # We might update an empty set with an empty set
            if v:
                changed = True
                context.context[context_key][k] |= v
    context.context[context_key_non_ssa] = convert_to_non_ssa(context.context[context_key])


def propagate_contract(contract: Contract, context_key: str, context_key_non_ssa: str) -> None:
    transitive_close_dependencies(contract, context_key, context_key_non_ssa)


def add_dependency(lvalue: Variable, function: Function, ir: Operation, is_protected: bool) -> None:
    if not lvalue in function.context[KEY_SSA]:
        function.context[KEY_SSA][lvalue] = set()
        if not is_protected:
            function.context[KEY_SSA_UNPROTECTED][lvalue] = set()
    read: Union[List[Union[LVALUE, SolidityVariableComposed]], List[SlithIRVariable]]
    if isinstance(ir, Index):
        read = [ir.variable_left]
    elif isinstance(ir, InternalCall) and ir.function:
        read = ir.function.return_values_ssa
    else:
        read = ir.read
    for v in read:
        if not isinstance(v, Constant):
            function.context[KEY_SSA][lvalue].add(v)
    if not is_protected:
        for v in read:
            if not isinstance(v, Constant):
                function.context[KEY_SSA_UNPROTECTED][lvalue].add(v)


def compute_dependency_function(function: Function) -> None:
    if KEY_SSA in function.context:
        return

    function.context[KEY_SSA] = {}
    function.context[KEY_SSA_UNPROTECTED] = {}

    is_protected = function.is_protected()
    for node in function.nodes:
        for ir in node.irs_ssa:
            if isinstance(ir, OperationWithLValue) and ir.lvalue:
                if isinstance(ir.lvalue, LocalIRVariable) and ir.lvalue.is_storage:
                    continue
                if isinstance(ir.lvalue, ReferenceVariable):
                    lvalue = ir.lvalue.points_to
                    if lvalue:
                        add_dependency(lvalue, function, ir, is_protected)
                add_dependency(ir.lvalue, function, ir, is_protected)

    function.context[KEY_NON_SSA] = convert_to_non_ssa(function.context[KEY_SSA])
    function.context[KEY_NON_SSA_UNPROTECTED] = convert_to_non_ssa(
        function.context[KEY_SSA_UNPROTECTED]
    )


def convert_variable_to_non_ssa(v: SUPPORTED_TYPES) -> SUPPORTED_TYPES:
    if isinstance(
        v,
        (
            LocalIRVariable,
            StateIRVariable,
            TemporaryVariableSSA,
            ReferenceVariableSSA,
            TupleVariableSSA,
        ),
    ):
        return v.non_ssa_version
    assert isinstance(
        v,
        (
            Constant,
            SolidityVariable,
            Contract,
            Enum,
            SolidityFunction,
            Structure,
            Function,
            Type,
            SolidityImportPlaceHolder,
            TopLevelVariable,
        ),
    )
    return v


def convert_to_non_ssa(
    data_depencies: Dict[SUPPORTED_TYPES, Set[SUPPORTED_TYPES]]
) -> Dict[SUPPORTED_TYPES, Set[SUPPORTED_TYPES]]:
    # Need to create new set() as its changed during iteration
    ret: Dict[SUPPORTED_TYPES, Set[SUPPORTED_TYPES]] = {}
    for (k, values) in data_depencies.items():
        var = convert_variable_to_non_ssa(k)
        if not var in ret:
            ret[var] = set()
        ret[var] = ret[var].union({convert_variable_to_non_ssa(v) for v in values})

    return ret
