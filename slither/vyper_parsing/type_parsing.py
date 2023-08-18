from slither.core.solidity_types.elementary_type import (
    ElementaryType,
    ElementaryTypeName,
)  # TODO rename solidity type
from slither.core.solidity_types.array_type import ArrayType
from slither.vyper_parsing.expressions.expression_parsing import parse_expression
from slither.vyper_parsing.ast.types import Name, Subscript, Call, Index, Tuple
from typing import Union
from slither.core.solidity_types.user_defined_type import UserDefinedType


def parse_type(annotation: Union[Name, Subscript, Call], contract):
    assert isinstance(annotation, (Name, Subscript, Call))
    print(annotation)
    if isinstance(annotation, Name):
        name = annotation.id
    elif isinstance(annotation, Subscript):
        assert isinstance(annotation.slice, Index)

        # This is also a strange construct...
        if isinstance(annotation.slice.value, Tuple):
            type_ = parse_type(annotation.slice.value.elements[0], contract)
            length = parse_expression(annotation.slice.value.elements[1], contract)
        else:
            # TODO it is weird that the ast_type is     `Index` when it's a type annotation and not an expression
            # so we grab the value
            type_ = parse_type(annotation.value, contract)
            length = parse_expression(annotation.slice.value, contract)

        # TODO this can also me `HashMaps`
        return ArrayType(type_, length)

    elif isinstance(annotation, Call):
        return parse_type(annotation.args[0], contract)

    else:
        assert False

    lname = name.lower()  # todo map String to string
    if lname in ElementaryTypeName:
        return ElementaryType(lname)

    print(contract.structures_as_dict)

    if name in contract.structures_as_dict:
        return UserDefinedType(contract.structures_as_dict[name])

    print(contract.enums_as_dict)
    if name in contract.enums_as_dict:
        return UserDefinedType(contract.enums_as_dict[name])

    print(contract.file_scope.contracts)
    if name in contract.file_scope.contracts:
        return UserDefinedType(contract.file_scope.contracts[name])
    assert False
