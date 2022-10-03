from typing import List, Tuple, Union, Optional, Set

from slither import Slither
from slither.core.declarations import Function, FunctionContract
from slither.core.slither_core import SlitherCore


class ResolveFunctionException(Exception):
    pass


def resolve_function(slither: SlitherCore, contract_name: str, function_name: str) -> Function:
    """
    Resolves a function instance, given a contract name and function.
    :param contract_name: The name of the contract the function is declared in.
    :param function_name: The name of the function to resolve.
    :return: Returns the resolved function, raises an exception otherwise.
    """
    # Obtain the target contract
    contracts = slither.get_contract_from_name(contract_name)

    # Verify the contract was resolved successfully
    if len(contracts) != 1:
        raise ResolveFunctionException(f"Could not resolve target contract: {contract_name}")
    contract = contracts[0]
    # Obtain the target function
    target_function = next(
        (function for function in contract.functions if function.name == function_name),
        None,
    )

    # Verify we have resolved the function specified.
    if target_function is None:
        raise ResolveFunctionException(
            f"Could not resolve target function: {contract_name}.{function_name}"
        )

    # Add the resolved function to the new list.
    return target_function


def resolve_functions(
    slither: Slither, functions: List[Union[str, Tuple[str, str]]]
) -> List[Function]:
    """
    Resolves the provided function descriptors.
    :param functions: A list of tuples (contract_name, function_name) or str (of form "ContractName.FunctionName")
    to resolve into function objects.
    :return: Returns a list of resolved functions.
    """
    # Create the resolved list.
    resolved: List[Function] = []

    # Verify that the provided argument is a list.
    if not isinstance(functions, list):
        raise ResolveFunctionException("Provided functions to resolve must be a list type.")

    # Loop for each item in the list.
    for item in functions:
        if isinstance(item, str):
            # If the item is a single string, we assume it is of form 'ContractName.FunctionName'.
            parts = item.split(".")
            if len(parts) < 2:
                raise ResolveFunctionException(
                    "Provided string descriptor must be of form 'ContractName.FunctionName'"
                )
            resolved.append(resolve_function(slither, parts[0], parts[1]))
        elif isinstance(item, tuple):
            # If the item is a tuple, it should be a 2-tuple providing contract and function names.
            if len(item) != 2:
                raise ResolveFunctionException(
                    "Provided tuple descriptor must provide a contract and function name."
                )
            resolved.append(resolve_function(slither, item[0], item[1]))
        else:
            raise ResolveFunctionException(
                f"Unexpected function descriptor type to resolve in list: {type(item)}"
            )

    # Return the resolved list.
    return resolved


def all_function_definitions(function: Function) -> List[Function]:
    """
    Obtains a list of representing this function and any base definitions
    :param function: The function to obtain all definitions at and beneath.
    :return: Returns a list composed of the provided function definition and any base definitions.
    """
    # TODO implement me
    if not isinstance(function, FunctionContract):
        return []
    ret: List[Function] = [function]
    ret += [
        f
        for c in function.contract.inheritance
        for f in c.functions_and_modifiers_declared
        if f.full_name == function.full_name
    ]
    return ret


def __find_target_paths(
    slither: SlitherCore, target_function: Function, current_path: Optional[List[Function]] = None
) -> Set[Tuple[Function, ...]]:
    current_path = current_path if current_path else []
    # Create our results list
    results: Set[Tuple[Function, ...]] = set()

    # Add our current function to the path.
    current_path = [target_function] + current_path

    # Obtain this target function and any base definitions.
    all_target_functions = set(all_function_definitions(target_function))

    # Look through all functions
    for contract in slither.contracts:
        for function in contract.functions_and_modifiers_declared:

            # If the function is already in our path, skip it.
            if function in current_path:
                continue

            # Find all function calls in this function (except for low level)
            called_functions_list = [
                f for (_, f) in function.high_level_calls if isinstance(f, Function)
            ]
            called_functions_list += [f for (_, f) in function.library_calls]
            called_functions_list += [f for f in function.internal_calls if isinstance(f, Function)]
            called_functions = set(called_functions_list)

            # If any of our target functions are reachable from this function, it's a result.
            if all_target_functions.intersection(called_functions):
                path_results = __find_target_paths(slither, function, current_path.copy())
                if path_results:
                    results = results.union(path_results)

    # If this path is external accessible from this point, we add the current path to the list.
    if target_function.visibility in ["public", "external"] and len(current_path) > 1:
        results.add(tuple(current_path))

    return results


def find_target_paths(
    slither: SlitherCore, target_functions: List[Function]
) -> Set[Tuple[Function, ...]]:
    """
    Obtains all functions which can lead to any of the target functions being called.
    :param target_functions: The functions we are interested in reaching.
    :return: Returns a list of all functions which can reach any of the target_functions.
    """
    # Create our results list
    results: Set[Tuple[Function, ...]] = set()

    # Loop for each target function
    for target_function in target_functions:
        results = results.union(__find_target_paths(slither, target_function))

    return results
