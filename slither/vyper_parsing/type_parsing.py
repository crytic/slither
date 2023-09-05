from typing import Union
from slither.core.solidity_types.elementary_type import (
    ElementaryType,
    ElementaryTypeName,
)  # TODO rename solidity type
from slither.core.solidity_types.array_type import ArrayType
from slither.core.solidity_types.mapping_type import MappingType
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.core.declarations import FunctionContract, Contract
from slither.vyper_parsing.ast.types import Name, Subscript, Call, Index, Tuple
from slither.solc_parsing.exceptions import ParsingError

# pylint: disable=too-many-branches,too-many-return-statements,import-outside-toplevel,too-many-locals
def parse_type(
    annotation: Union[Name, Subscript, Call, Tuple],
    caller_context: Union[FunctionContract, Contract],
):
    from slither.vyper_parsing.expressions.expression_parsing import parse_expression

    if isinstance(caller_context, FunctionContract):
        contract = caller_context.contract
    else:
        contract = caller_context

    assert isinstance(annotation, (Name, Subscript, Call, Tuple))

    if isinstance(annotation, Name):
        name = annotation.id
        lname = name.lower()  # map `String` to string
        if lname in ElementaryTypeName:
            return ElementaryType(lname)

        if name in contract.structures_as_dict:
            return UserDefinedType(contract.structures_as_dict[name])

        if name in contract.enums_as_dict:
            return UserDefinedType(contract.enums_as_dict[name])

        if name in contract.file_scope.contracts:
            return UserDefinedType(contract.file_scope.contracts[name])

        if name in contract.file_scope.structures:
            return UserDefinedType(contract.file_scope.structures[name])
    elif isinstance(annotation, Subscript):
        assert isinstance(annotation.slice, Index)
        # This is also a strange construct... https://github.com/vyperlang/vyper/issues/3577
        if isinstance(annotation.slice.value, Tuple):
            assert isinstance(annotation.value, Name)
            if annotation.value.id == "DynArray":
                type_ = parse_type(annotation.slice.value.elements[0], caller_context)
                length = parse_expression(annotation.slice.value.elements[1], caller_context)
                return ArrayType(type_, length)
            if annotation.value.id == "HashMap":
                type_from = parse_type(annotation.slice.value.elements[0], caller_context)
                type_to = parse_type(annotation.slice.value.elements[1], caller_context)

                return MappingType(type_from, type_to)

        elif isinstance(annotation.value, Subscript):
            type_ = parse_type(annotation.value, caller_context)

        elif isinstance(annotation.value, Name):
            # TODO it is weird that the ast_type is `Index` when it's a type annotation and not an expression, so we grab the value. https://github.com/vyperlang/vyper/issues/3577
            type_ = parse_type(annotation.value, caller_context)
            if annotation.value.id == "String":
                # This is an elementary type
                return type_

        length = parse_expression(annotation.slice.value, caller_context)
        return ArrayType(type_, length)

    elif isinstance(annotation, Call):
        # TODO event variable represented as Call https://github.com/vyperlang/vyper/issues/3579
        return parse_type(annotation.args[0], caller_context)

    elif isinstance(annotation, Tuple):
        # Vyper has tuple types like python x = f() where f() -> (y,z)
        # and tuple elements can be unpacked like x[0]: y and x[1]: z.
        # We model these as a struct and unpack each index into a field
        # e.g. accessing the 0th element is translated as x._0
        from slither.core.declarations.structure import Structure
        from slither.core.variables.structure_variable import StructureVariable

        st = Structure(caller_context.compilation_unit)
        st.set_offset("-1:-1:-1", caller_context.compilation_unit)
        st.name = "FAKE_TUPLE"
        for idx, elem_info in enumerate(annotation.elements):
            elem = StructureVariable()
            elem.type = parse_type(elem_info, caller_context)
            elem.name = f"_{idx}"
            elem.set_structure(st)
            elem.set_offset("-1:-1:-1", caller_context.compilation_unit)
            st.elems[elem.name] = elem
            st.add_elem_in_order(elem.name)
            st.name += elem.name

        return UserDefinedType(st)

    raise ParsingError(f"Type name not found {name} context {caller_context}")
