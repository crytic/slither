from typing import List, Union

from slither.core.solidity_types import ArrayType, MappingType, ElementaryType
from slither.core.solidity_types.type import Type
from slither.core.variables.variable import Variable


def _add_mapping_parameter(t: Type, l: List[Type]):
    while isinstance(t, MappingType):
        l.append(t.type_from)
        t = t.type_to
    _add_array_parameter(t, l)


def _add_array_parameter(t: Type, l: List[Type]):
    while isinstance(t, ArrayType):
        l.append(ElementaryType("uint256"))
        t = t.type


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


def export_return_type_from_variable(variable: Union[Type, Variable]):
    """
    Return the type returned by a variable
    :param variable
    :return: Type
    """
    if isinstance(variable, MappingType):
        return export_return_type_from_variable(variable.type_to)

    if isinstance(variable, ArrayType):
        return variable.type

    if isinstance(variable.type, MappingType):
        return export_return_type_from_variable(variable.type.type_to)

    if isinstance(variable.type, ArrayType):
        return variable.type.type

    return variable.type
