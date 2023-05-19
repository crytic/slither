import math
from typing import List, Union, Set

from slither.core.solidity_types import (
    ArrayType,
    MappingType,
    ElementaryType,
    UserDefinedType,
    TypeAlias,
)
from slither.core.solidity_types.type import Type
from slither.core.variables.variable import Variable


def _convert_type_for_solidity_signature_to_string(
    types: Union[Type, List[Type]], seen: Set[Type]
) -> str:
    if isinstance(types, Type):
        # Array might be struct, so we need to go again through the conversion here
        # We could have this logic in convert_type_for_solidity_signature
        # But the slither type system is not straightforward to manipulate here
        # And it would require to create a new ArrayType, which a potential List[Type] as input
        # Which is currently not supported. This comes down to (uint, uint)[] not being possible in Solidity
        # While having an array of a struct of two uint leads to a (uint, uint)[] signature
        if isinstance(types, ArrayType):
            underlying_type = convert_type_for_solidity_signature(types.type, seen)
            underlying_type_str = _convert_type_for_solidity_signature_to_string(
                underlying_type, seen
            )
            return underlying_type_str + "[]"

        return str(types)

    first_item = True

    ret = "("
    for underlying_type in types:
        if first_item:
            ret += _convert_type_for_solidity_signature_to_string(underlying_type, seen)
        else:
            ret += "," + _convert_type_for_solidity_signature_to_string(underlying_type, seen)
        first_item = False

    ret += ")"
    return ret


def convert_type_for_solidity_signature_to_string(t: Type) -> str:
    seen: Set[Type] = set()
    types = convert_type_for_solidity_signature(t, seen)
    return _convert_type_for_solidity_signature_to_string(types, seen)


def convert_type_for_solidity_signature(t: Type, seen: Set[Type]) -> Union[Type, List[Type]]:
    # pylint: disable=import-outside-toplevel
    from slither.core.declarations import Contract, Enum, Structure

    # Solidity allows recursive type for structure definition if its not used in public /external
    # When this happens we can reach an infinite loop. If we detect a loop, we just stop converting the underlying type
    # This is ok, because it wont happen for public/external function
    #
    # contract A{
    #
    #   struct St{
    #       St[] a;
    #       uint b;
    #   }
    #
    #    function f(St memory s) internal{}
    #
    # }
    if t in seen:
        return t
    seen.add(t)

    if isinstance(t, UserDefinedType):
        underlying_type = t.type
        if isinstance(underlying_type, Contract):
            return ElementaryType("address")
        if isinstance(underlying_type, Enum):
            number_values = len(underlying_type.values)
            # IF below 65536, avoid calling log2
            if number_values <= 256:
                uint = "8"
            elif number_values <= 65536:
                uint = "16"
            else:
                uint = str(int(math.log2(number_values)))
            return ElementaryType(f"uint{uint}")
        if isinstance(underlying_type, Structure):
            # We can't have recursive types for structure, so recursion is ok here
            types = [
                convert_type_for_solidity_signature(x.type, seen)
                for x in underlying_type.elems_ordered
            ]
            return types

    if isinstance(t, TypeAlias):
        return t.type

    return t


def _export_nested_types_from_variable(
    current_type: Type, ret: List[Type], seen: Set[Type]
) -> None:
    """
    Export the list of nested types (mapping/array)
    :param variable:
    :return: list(Type)
    """
    if isinstance(current_type, MappingType):
        underlying_type = convert_type_for_solidity_signature(current_type.type_from, seen)
        if isinstance(underlying_type, list):
            ret.extend(underlying_type)
        else:
            ret.append(underlying_type)
        next_type = current_type.type_to

    elif isinstance(current_type, ArrayType):
        ret.append(ElementaryType("uint256"))
        next_type = current_type.type
    else:
        return
    _export_nested_types_from_variable(next_type, ret, seen)


def export_nested_types_from_variable(variable: Variable) -> List[Type]:
    """
    Export the list of nested types (mapping/array)
    :param variable:
    :return: list(Type)
    """
    l: List[Type] = []
    seen: Set[Type] = set()
    _export_nested_types_from_variable(variable.type, l, seen)
    return l


def _export_return_type_from_variable(underlying_type: Type, all_types: bool) -> List[Type]:
    # pylint: disable=import-outside-toplevel
    from slither.core.declarations import Structure

    if isinstance(underlying_type, MappingType):
        if not all_types:
            return []
        return export_return_type_from_variable(underlying_type.type_to)

    if isinstance(underlying_type, ArrayType):
        if not all_types:
            return []
        return export_return_type_from_variable(underlying_type.type)

    if isinstance(underlying_type, UserDefinedType) and isinstance(underlying_type.type, Structure):
        ret = []
        for r in underlying_type.type.elems_ordered:
            ret += export_return_type_from_variable(r, all_types=False)

        return ret

    return [underlying_type]


def export_return_type_from_variable(
    variable_or_type: Union[Type, Variable], all_types: bool = True
) -> List[Type]:
    """
    Return the type returned by a variable.
    If all_types set to false, filter array/mapping. This is useful as the mapping/array in a structure are not
    returned by solidity
    :param variable_or_type
    :param all_types
    :return: Type
    """
    # pylint: disable=import-outside-toplevel
    from slither.core.declarations import Structure

    if isinstance(variable_or_type, Type):
        return _export_return_type_from_variable(variable_or_type, all_types)

    if isinstance(variable_or_type.type, MappingType):
        if not all_types:
            return []
        return export_return_type_from_variable(variable_or_type.type.type_to)

    if isinstance(variable_or_type.type, ArrayType):
        if not all_types:
            return []
        return export_return_type_from_variable(variable_or_type.type.type)

    if isinstance(variable_or_type.type, UserDefinedType) and isinstance(
        variable_or_type.type.type, Structure
    ):
        ret = []
        for r in variable_or_type.type.type.elems_ordered:
            ret += export_return_type_from_variable(r, all_types=False)
        return ret

    return [variable_or_type.type]


def is_underlying_type_address(t: "Type") -> bool:
    """
    Return true if the underlying type is an address
    i.e. if the type is an address or a contract
    """
    # pylint: disable=import-outside-toplevel
    from slither.core.declarations.contract import Contract

    if t == ElementaryType("address"):
        return True
    if isinstance(t, UserDefinedType) and isinstance(t.type, Contract):
        return True
    return False
