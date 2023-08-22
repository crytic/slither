from slither.core.solidity_types.elementary_type import (
    ElementaryType,
    ElementaryTypeName,
)  # TODO rename solidity type
from slither.core.solidity_types.array_type import ArrayType
from slither.core.solidity_types.mapping_type import MappingType

from slither.vyper_parsing.ast.types import Name, Subscript, Call, Index, Tuple
from typing import Union
from slither.core.solidity_types.user_defined_type import UserDefinedType

from slither.core.declarations.function_contract import FunctionContract

def parse_type(annotation: Union[Name, Subscript, Call], caller_context):
    from slither.vyper_parsing.expressions.expression_parsing import parse_expression

    if isinstance(caller_context, FunctionContract):
        contract =  caller_context.contract
    else:
        contract = caller_context

    assert isinstance(annotation, (Name, Subscript, Call))
    print(annotation)
    if isinstance(annotation, Name):
        name = annotation.id
    elif isinstance(annotation, Subscript):
        assert isinstance(annotation.slice, Index)
        # This is also a strange construct...
        if isinstance(annotation.slice.value, Tuple):
            assert isinstance(annotation.value, Name)
            if annotation.value.id == "DynArray":
                type_ = parse_type(annotation.slice.value.elements[0], caller_context)
                length = parse_expression(annotation.slice.value.elements[1], caller_context)
                return ArrayType(type_, length)
            else:
                assert annotation.value.id == "HashMap"
                type_from = parse_type(annotation.slice.value.elements[0], caller_context)
                type_to = parse_type(annotation.slice.value.elements[1], caller_context)

                return MappingType(type_from, type_to)

        elif isinstance(annotation.value, Subscript):
            type_ = parse_type(annotation.value, caller_context)
        
        elif isinstance(annotation.value, Name):
            # TODO it is weird that the ast_type is `Index` when it's a type annotation and not an expression, so we grab the value.
            # Subscript(src='13:10:0', node_id=7, value=Name(src='13:6:0', node_id=8, id='String'), slice=Index(src='13:10:0', node_id=12, value=Int(src='20:2:0', node_id=10, value=64)))
            type_ = parse_type(annotation.value, caller_context)
            if annotation.value.id == "String":
                return type_
            
        length = parse_expression(annotation.slice.value, caller_context)
        return ArrayType(type_, length)
        

    elif isinstance(annotation, Call):
        return parse_type(annotation.args[0], caller_context)

    else:
        assert False

    lname = name.lower()  # todo map String to string
    if lname in ElementaryTypeName:
        return ElementaryType(lname)



    if name in contract.structures_as_dict:
        return UserDefinedType(contract.structures_as_dict[name])

    print(contract.enums_as_dict)
    if name in contract.enums_as_dict:
        return UserDefinedType(contract.enums_as_dict[name])

    print(contract.file_scope.contracts)
    if name in contract.file_scope.contracts:
        return UserDefinedType(contract.file_scope.contracts[name])
    assert False
