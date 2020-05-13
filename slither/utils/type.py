import math
from typing import Union, List

from slither.core.solidity_types import (ArrayType, MappingType, ElementaryType, UserDefinedType, FunctionType)
from slither.core.solidity_types.type import Type
from slither.core.variables.variable import Variable


def _add_mapping_parameter(t: Type, l: List[Type]):
    while isinstance(t, MappingType):
        l.append(convert_type_for_solidity_signature(t.type_from))
        t = t.type_to

    if isinstance(t, ArrayType):
        _add_array_parameter(t, l)


def _add_array_parameter(t: Type, l: List[Type]):
    while isinstance(t, ArrayType):
        l.append(ElementaryType("uint256"))
        t = t.type

    if isinstance(t, MappingType):
        _add_mapping_parameter(t, l)


def convert_type_for_solidity_signature(t: Type) -> Type:
    from slither.core.declarations import Contract, Enum
    if isinstance(t, UserDefinedType) and isinstance(t.type, Contract):
        return ElementaryType("address")
    if isinstance(t, UserDefinedType) and isinstance(t.type, Enum):
        number_values = len(t.type.values)
        # IF below 65536, avoid calling log2
        if number_values <= 256:
            uint = "8"
        elif number_values <= 65536:
            uint = "16"
        else:
            uint = int(math.log2(number_values))
        return ElementaryType(f"uint{uint}")
    return t


def export_nested_types_from_variable(variable: Variable) -> List[Type]:
    """
    Export the list of nested types (mapping/array)
    :param variable:
    :return: list(Type)
    """
    l: List[Type] = []
    if isinstance(variable.type, MappingType):
        t = variable.type
        _add_mapping_parameter(t, l)

    if isinstance(variable.type, ArrayType):
        v = variable
        _add_array_parameter(v.type, l)

    return l


def export_return_type_from_variable(variable_or_type: Union[Type, Variable], all_types: bool = True) -> List[Type]:
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
        if isinstance(variable_or_type, MappingType):
            if not all_types:
                return []
            return export_return_type_from_variable(variable_or_type.type_to)

        if isinstance(variable_or_type, ArrayType):
            if not all_types:
                return []
            return export_return_type_from_variable(variable_or_type.type)

        if isinstance(variable_or_type, UserDefinedType) and isinstance(variable_or_type.type, Structure):
            ret = []
            for r in variable_or_type.type.elems_ordered:
                ret += export_return_type_from_variable(r, all_types=False)

            return ret

        return [variable_or_type]
    else:
        if isinstance(variable_or_type.type, MappingType):
            if not all_types:
                return []
            return export_return_type_from_variable(variable_or_type.type.type_to)

        if isinstance(variable_or_type.type, ArrayType):
            if not all_types:
                return []
            return export_return_type_from_variable(variable_or_type.type.type)

        if isinstance(variable_or_type.type, UserDefinedType) and isinstance(variable_or_type.type.type, Structure):
            ret = []
            for r in variable_or_type.type.type.elems_ordered:
                ret += export_return_type_from_variable(r, all_types=False)
            return ret

        return [variable_or_type.type]
