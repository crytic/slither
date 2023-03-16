from typing import Optional
from slither.analyses.data_dependency.data_dependency import get_dependencies
from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function
from slither.core.variables.variable import Variable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.local_variable import LocalVariable
from slither.core.expressions.literal import Literal
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.assignment_operation import AssignmentOperation
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.cfg.node import Node, NodeType
from slither.slithir.operations import LowLevelCall
from slither.tools.read_storage.read_storage import SlotInfo, SlitherReadStorage
from slither.tools.similarity.encode import encode_ir


# pylint: disable=too-many-locals
def compare(v1: Contract, v2: Contract) -> dict:
    """
    Compares two versions of a contract. Most useful for upgradeable (logic) contracts,
    but does not require that Contract.is_upgradeable returns true for either contract.

    Args:
        v1: Original version of (upgradeable) contract
        v2: Updated version of (upgradeable) contract

    Returns: dict {
        "missing-vars-in-v2": list[Variable],
        "new-variables": list[Variable],
        "tainted-variables": list[Variable],
        "new-functions": list[Function],
        "modified-functions": list[Function],
        "tainted-functions": list[Function]
    }
    """

    order_vars1 = [v for v in v1.state_variables if not v.is_constant and not v.is_immutable]
    order_vars2 = [v for v in v2.state_variables if not v.is_constant and not v.is_immutable]
    func_sigs1 = [function.solidity_signature for function in v1.functions]
    func_sigs2 = [function.solidity_signature for function in v2.functions]

    results = {
        "missing-vars-in-v2": [],
        "new-variables": [],
        "tainted-variables": [],
        "new-functions": [],
        "modified-functions": [],
        "tainted-functions": [],
    }

    # Since this is not a detector, include any missing variables in the v2 contract
    if len(order_vars2) < len(order_vars1):
        for variable in order_vars1:
            if variable.name not in [v.name for v in order_vars2]:
                results["missing-vars-in-v2"].append(variable)

    # Find all new and modified functions in the v2 contract
    new_modified_functions = []
    new_modified_function_vars = []
    for sig in func_sigs2:
        function = v2.get_function_from_signature(sig)
        orig_function = v1.get_function_from_signature(sig)
        if sig not in func_sigs1:
            new_modified_functions.append(function)
            results["new-functions"].append(function)
            new_modified_function_vars += (
                function.state_variables_read + function.state_variables_written
            )
        elif not function.name.startswith("slither") and is_function_modified(
            orig_function, function
        ):
            new_modified_functions.append(function)
            results["modified-functions"].append(function)
            new_modified_function_vars += (
                function.state_variables_read + function.state_variables_written
            )

    # Find all unmodified functions that call a modified function or read/write the
    # same state variable(s) as a new/modified function, i.e., tainted functions
    for function in v2.functions:
        if (
            function in new_modified_functions
            or function.is_constructor
            or function.name.startswith("slither")
        ):
            continue
        modified_calls = [
            func for func in new_modified_functions if func in function.internal_calls
        ]
        tainted_vars = [
            var
            for var in set(new_modified_function_vars)
            if var in function.variables_read_or_written
            and not var.is_constant
            and not var.is_immutable
        ]
        if len(modified_calls) > 0 or len(tainted_vars) > 0:
            results["tainted-functions"].append(function)

    # Find all new or tainted variables, i.e., variables that are read or written by a new/modified/tainted function
    for _, var in enumerate(order_vars2):
        read_by = v2.get_functions_reading_from_variable(var)
        written_by = v2.get_functions_writing_to_variable(var)
        if v1.get_state_variable_from_name(var.name) is None:
            results["new-variables"].append(var)
        elif any(
            func in read_by or func in written_by
            for func in new_modified_functions + results["tainted-functions"]
        ):
            results["tainted-variables"].append(var)

    return results


def is_function_modified(f1: Function, f2: Function) -> bool:
    """
    Compares two versions of a function, and returns True if the function has been modified.
    First checks whether the functions' content hashes are equal to quickly rule out identical functions.
    Walks the CFGs and compares IR operations if hashes differ to rule out false positives, i.e., from changed comments.

    Args:
        f1: Original version of the function
        f2: New version of the function

    Returns:
        True if the functions differ, otherwise False
    """
    # If the function content hashes are the same, no need to investigate the function further
    if f1.source_mapping.content_hash == f2.source_mapping.content_hash:
        return False
    # If the hashes differ, it is possible a change in a name or in a comment could be the only difference
    # So we need to resort to walking through the CFG and comparing the IR operations
    queue_f1 = [f1.entry_point]
    queue_f2 = [f2.entry_point]
    visited = []
    while len(queue_f1) > 0 and len(queue_f2) > 0:
        node_f1 = queue_f1.pop(0)
        node_f2 = queue_f2.pop(0)
        visited.extend([node_f1, node_f2])
        queue_f1.extend(son for son in node_f1.sons if son not in visited)
        queue_f2.extend(son for son in node_f2.sons if son not in visited)
        for i, ir in enumerate(node_f1.irs):
            if encode_ir(ir) != encode_ir(node_f2.irs[i]):
                return True
    return False


def get_proxy_implementation_slot(proxy: Contract) -> Optional[SlotInfo]:
    """
    Gets information about the storage slot where a proxy's implementation address is stored.
    Args:
        proxy: A Contract object (proxy.is_upgradeable_proxy should be true).

    Returns:
        (`SlotInfo`) | None : A dictionary of the slot information.
    """

    delegate = get_proxy_implementation_var(proxy)
    if isinstance(delegate, StateVariable):
        if not delegate.is_constant and not delegate.is_immutable:
            srs = SlitherReadStorage([proxy], 20)
            return srs.get_storage_slot(delegate, proxy)
        if delegate.is_constant and delegate.type.name == "bytes32":
            return SlotInfo(
                name=delegate.name,
                type_string="address",
                slot=int(delegate.expression.value, 16),
                size=160,
                offset=0,
            )
    return None


def get_proxy_implementation_var(proxy: Contract) -> Optional[Variable]:
    """
    Gets the Variable that stores a proxy's implementation address. Uses data dependency to trace any LocalVariable
    that is passed into a delegatecall as the target address back to its data source, ideally a StateVariable.
    Args:
        proxy: A Contract object (proxy.is_upgradeable_proxy should be true).

    Returns:
        (`Variable`) | None : The variable, ideally a StateVariable, which stores the proxy's implementation address.
    """
    available_functions = proxy.available_functions_as_dict()
    if not proxy.is_upgradeable_proxy or not available_functions["fallback()"]:
        return None

    delegate = find_delegate_in_fallback(proxy)
    if isinstance(delegate, LocalVariable):
        dependencies = get_dependencies(delegate, proxy)
        try:
            delegate = next(var for var in dependencies if isinstance(var, StateVariable))
        except StopIteration:
            return delegate
    return delegate


def find_delegate_in_fallback(proxy: Contract) -> Optional[Variable]:
    """
    Searches a proxy's fallback function for a delegatecall, then extracts the Variable being passed in as the target.
    Should typically be called by get_proxy_implementation_var(proxy).
    Args:
        proxy: A Contract object (should have a fallback function).

    Returns:
        (`Variable`) | None : The variable being passed as the destination argument in a delegatecall in the fallback.
    """
    delegate: Optional[Variable] = None
    fallback = proxy.available_functions_as_dict()["fallback()"]
    for node in fallback.all_nodes():
        for ir in node.irs:
            if isinstance(ir, LowLevelCall) and ir.function_name == "delegatecall":
                delegate = ir.destination
        if delegate is not None:
            break
        if (
            node.type == NodeType.ASSEMBLY
            and isinstance(node.inline_asm, str)
            and "delegatecall" in node.inline_asm
        ):
            delegate = extract_delegate_from_asm(proxy, node)
        elif node.type == NodeType.EXPRESSION:
            expression = node.expression
            if isinstance(expression, AssignmentOperation):
                expression = expression.expression_right
            if (
                isinstance(expression, CallExpression)
                and "delegatecall" in str(expression.called)
                and len(expression.arguments) > 1
            ):
                dest = expression.arguments[1]
                if isinstance(dest, CallExpression) and "sload" in str(dest.called):
                    dest = dest.arguments[0]
                if isinstance(dest, Identifier):
                    delegate = dest.value
                    break
                if isinstance(dest, Literal) and len(dest.value) == 66:
                    delegate = StateVariable()
                    delegate.is_constant = True
                    delegate.expression = dest
                    delegate.name = dest.value
                    delegate.type = ElementaryType("bytes32")
                    break
    return delegate


def extract_delegate_from_asm(contract: Contract, node: Node) -> Optional[Variable]:
    """
    Finds a Variable with a name matching the argument passed into a delegatecall, when all we have is an Assembly node
    with a block of code as one long string. Usually only the case for solc versions < 0.6.0.
    Should typically be called by find_delegate_in_fallback(proxy).
    Args:
        contract: The parent Contract.
        node: The Assembly Node (i.e., node.type == NodeType.ASSEMBLY)

    Returns:
        (`Variable`) | None : The variable being passed as the destination argument in a delegatecall in the fallback.
    """
    asm_split = str(node.inline_asm).split("\n")
    asm = next(line for line in asm_split if "delegatecall" in line)
    params = asm.split("call(")[1].split(", ")
    dest = params[1]
    if dest.endswith(")"):
        dest = params[2]
    if dest.startswith("sload("):
        dest = dest.replace(")", "(").split("(")[1]
        for v in node.function.variables_read_or_written:
            if v.name == dest:
                if isinstance(v, LocalVariable) and v.expression is not None:
                    e = v.expression
                    if isinstance(e, Identifier) and isinstance(e.value, StateVariable):
                        v = e.value
                        # Fall through, return constant storage slot
                if isinstance(v, StateVariable) and v.is_constant:
                    return v
    if "_fallback_asm" in dest or "_slot" in dest:
        dest = dest.split("_")[0]
    return find_delegate_from_name(contract, dest, node.function)


def find_delegate_from_name(
    contract: Contract, dest: str, parent_func: Function
) -> Optional[Variable]:
    """
    Searches for a variable with a given name, starting with StateVariables declared in the contract, followed by
    LocalVariables in the parent function, either declared in the function body or as parameters in the signature.
    Args:
        contract: The Contract object to search.
        dest: The variable name to search for.
        parent_func: The Function object to search.

    Returns:
        (`Variable`) | None : The variable with the matching name, if found
    """
    for sv in contract.state_variables:
        if sv.name == dest:
            return sv
    for lv in parent_func.local_variables:
        if lv.name == dest:
            return lv
    for pv in parent_func.parameters:
        if pv.name == dest:
            return pv
    return None
