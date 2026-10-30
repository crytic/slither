import math

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
    types: Type | list[Type], seen: frozenset[Type]
) -> str:
    if isinstance(types, Type):
        # Array might be struct, so we need to go again through the conversion here
        # We could have this logic in convert_type_for_solidity_signature
        # But the slither type system is not straightforward to manipulate here
        # And it would require to create a new ArrayType, which a potential List[Type] as input
        # Which is currently not supported. This comes down to (uint, uint)[] not being possible in Solidity
        # While having an array of a struct of two uint leads to a (uint, uint)[] signature
        if isinstance(types, ArrayType):
            from slither.core.declarations import Structure

            underlying_type = convert_type_for_solidity_signature(types.type, seen)
            # Carry the array's element structure on the rendering descent so
            # that a genuinely recursive structure (e.g. struct St { St[] kids; })
            # terminates. `seen` is an ancestor path, not a global visited set:
            # repeated non-recursive fields/types must still be converted.
            element_seen = seen
            if isinstance(types.type, UserDefinedType) and isinstance(types.type.type, Structure):
                element_seen = seen | {types.type}
            underlying_type_str = _convert_type_for_solidity_signature_to_string(
                underlying_type, element_seen
            )

            if types.length is None:
                return underlying_type_str + "[]"
            return underlying_type_str + f"[{types.length_value}]"

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
    types = convert_type_for_solidity_signature(t, frozenset())
    # When the top-level type is an expanded structure, it is its own ancestor
    # while the (possibly array-deferred) fields are rendered below.
    render_seen: frozenset[Type] = frozenset()
    if isinstance(t, UserDefinedType):
        from slither.core.declarations import Structure

        if isinstance(t.type, Structure):
            render_seen = frozenset({t})
    return _convert_type_for_solidity_signature_to_string(types, render_seen)


def convert_type_for_solidity_signature(t: Type, seen: frozenset[Type]) -> Type | list[Type]:
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
    #
    # `seen` holds the structures on the current descent (an ancestor path),
    # passed by value. It only stops expanding a structure that is its own
    # ancestor. Leaf conversions (contracts, enums, user-defined value types /
    # aliases and elementary types) are never inserted: otherwise a type
    # repeated across sibling fields (e.g. two `Amount` fields) would be
    # misread as a recursive back-edge and left unconverted after its first
    # occurrence (issue #3064).
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
            if t in seen:
                return t
            child_seen = seen | {t}
            # We can't have recursive types for structure, so recursion is ok here
            types = [
                convert_type_for_solidity_signature(x.type, child_seen)
                for x in underlying_type.elems_ordered
            ]
            return types

    if isinstance(t, TypeAlias):
        return t.type

    return t


def _export_nested_types_from_variable(
    current_type: Type, ret: list[Type], seen: frozenset[Type]
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


def export_nested_types_from_variable(variable: Variable) -> list[Type]:
    """
    Export the list of nested types (mapping/array)
    :param variable:
    :return: list(Type)
    """
    l: list[Type] = []
    seen: frozenset[Type] = frozenset()
    _export_nested_types_from_variable(variable.type, l, seen)
    return l


def _export_return_type_from_variable(underlying_type: Type, all_types: bool) -> list[Type]:
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
    variable_or_type: Type | Variable, all_types: bool = True
) -> list[Type]:
    """
    Return the type returned by a variable.
    If all_types set to false, filter array/mapping. This is useful as the mapping/array in a structure are not
    returned by solidity
    :param variable_or_type
    :param all_types
    :return: Type
    """

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

    from slither.core.declarations.contract import Contract

    if t == ElementaryType("address"):
        return True
    if isinstance(t, UserDefinedType) and isinstance(t.type, Contract):
        return True
    return False
