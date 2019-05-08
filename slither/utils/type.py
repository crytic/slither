from slither.core.solidity_types import (ArrayType, MappingType, ElementaryType)


def _add_mapping_parameter(t, l):
    while isinstance(t, MappingType):
        l.append(t.type_from)
        t = t.type_to
    _add_array_parameter(t, l)


def _add_array_parameter(t, l):
    while isinstance(t, ArrayType):
        l.append(ElementaryType('uint256'))
        t = t.type


def export_nested_types_from_variable(variable):
    """
    Export the list of nested types (mapping/array)
    :param variable:
    :return: list(Type)
    """
    l = []
    if isinstance(variable.type, MappingType):
        t = variable.type
        _add_mapping_parameter(t, l)

    if isinstance(variable.type, ArrayType):
        v = variable
        _add_array_parameter(v.type, l)

    return l


