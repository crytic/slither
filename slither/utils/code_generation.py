# Functions for generating Solidity code
from typing import TYPE_CHECKING, Optional

from slither.utils.type import (
    convert_type_for_solidity_signature_to_string,
    export_nested_types_from_variable,
    export_return_type_from_variable,
)
from slither.core.solidity_types import (
    Type,
    UserDefinedType,
    MappingType,
    ArrayType,
    ElementaryType,
    TypeAlias,
)
from slither.core.declarations import Structure, StructureContract, Enum, Contract

if TYPE_CHECKING:
    from slither.core.declarations import FunctionContract, CustomErrorContract
    from slither.core.variables.state_variable import StateVariable
    from slither.core.variables.local_variable import LocalVariable
    from slither.core.variables.structure_variable import StructureVariable


# pylint: disable=too-many-arguments,too-many-locals,too-many-branches
def generate_interface(
    contract: "Contract",
    unroll_structs: bool = True,
    include_events: bool = True,
    include_errors: bool = True,
    include_enums: bool = True,
    include_structs: bool = True,
) -> str:
    """
    Generates code for a Solidity interface to the contract.
    Args:
        contract: A Contract object.
        unroll_structs: Whether to use structures' underlying types instead of the user-defined type (default: True).
        include_events: Whether to include event signatures in the interface (default: True).
        include_errors: Whether to include custom error signatures in the interface (default: True).
        include_enums: Whether to include enum definitions in the interface (default: True).
        include_structs: Whether to include struct definitions in the interface (default: True).

    Returns:
        A string with the code for an interface, with function stubs for all public or external functions and
        state variables, as well as any events, custom errors and/or structs declared in the contract.
    """
    interface = f"interface I{contract.name} {{\n"
    if include_events:
        for event in contract.events:
            name, args = event.signature
            interface += f"    event {name}({', '.join(args)});\n"
    if include_errors:
        for error in contract.custom_errors:
            interface += f"    error {generate_custom_error_interface(error, unroll_structs)};\n"
    if include_enums:
        for enum in contract.enums:
            interface += f"    enum {enum.name} {{ {', '.join(enum.values)} }}\n"
    if include_structs:
        # Include structures defined in this contract and at the top level
        structs = contract.structures + contract.compilation_unit.structures_top_level
        # Function signatures may reference other structures as well
        # Include structures defined in libraries used for them
        for _for in contract.using_for.keys():
            if (
                isinstance(_for, UserDefinedType)
                and isinstance(_for.type, StructureContract)
                and _for.type not in structs
            ):
                structs.append(_for.type)
        # Include any other structures used as function arguments/returns
        for func in contract.functions_entry_points:
            for arg in func.parameters + func.returns:
                _type = arg.type
                if isinstance(_type, ArrayType):
                    _type = _type.type
                while isinstance(_type, MappingType):
                    _type = _type.type_to
                if isinstance(_type, UserDefinedType):
                    _type = _type.type
                if isinstance(_type, Structure) and _type not in structs:
                    structs.append(_type)
        for struct in structs:
            interface += generate_struct_interface_str(struct, indent=4)
            for elem in struct.elems_ordered:
                if (
                    isinstance(elem.type, UserDefinedType)
                    and isinstance(elem.type.type, StructureContract)
                    and elem.type.type not in structs
                ):
                    structs.append(elem.type.type)
    for var in contract.state_variables_entry_points:
        # if any(func.name == var.name for func in contract.functions_entry_points):
        #     # ignore public variables that override a public function
        #     continue
        var_sig = generate_interface_variable_signature(var, unroll_structs)
        if var_sig is not None and var_sig != "":
            interface += f"    function {var_sig};\n"
    for func in contract.functions_entry_points:
        if func.is_constructor or func.is_fallback or func.is_receive or not func.is_implemented:
            continue
        interface += (
            f"    function {generate_interface_function_signature(func, unroll_structs)};\n"
        )
    interface += "}\n\n"
    return interface


def generate_interface_variable_signature(
    var: "StateVariable", unroll_structs: bool = True
) -> Optional[str]:
    if var.visibility in ["private", "internal"]:
        return None
    if isinstance(var.type, UserDefinedType) and isinstance(var.type.type, Structure):
        for elem in var.type.type.elems_ordered:
            if isinstance(elem.type, MappingType):
                return ""
    if unroll_structs:
        params = [
            convert_type_for_solidity_signature_to_string(x).replace("(", "").replace(")", "")
            for x in export_nested_types_from_variable(var)
        ]
        returns = [
            convert_type_for_solidity_signature_to_string(x).replace("(", "").replace(")", "")
            for x in export_return_type_from_variable(var)
        ]
    else:
        _, params, _ = var.signature
        params = [p + " memory" if p in ["bytes", "string"] else p for p in params]
        returns = []
        _type = var.type
        while isinstance(_type, MappingType):
            _type = _type.type_to
        while isinstance(_type, (ArrayType, UserDefinedType)):
            _type = _type.type
        if isinstance(_type, TypeAlias):
            _type = _type.type
        if isinstance(_type, Structure):
            if any(isinstance(elem.type, MappingType) for elem in _type.elems_ordered):
                return ""
        ret = str(_type)
        if isinstance(_type, Structure) or (isinstance(_type, Type) and _type.is_dynamic):
            ret += " memory"
        elif isinstance(_type, Contract):
            ret = "address"
        returns.append(ret)
    return f"{var.name}({','.join(params)}) external returns ({', '.join(returns)})"


def generate_interface_function_signature(
    func: "FunctionContract", unroll_structs: bool = True
) -> Optional[str]:
    """
    Generates a string of the form:
        func_name(type1,type2) external {payable/view/pure} returns (type3)

    Args:
        func: A FunctionContract object
        unroll_structs: Determines whether structs are unrolled into underlying types (default: True)

    Returns:
        The function interface as a str (contains the return values).
        Returns None if the function is private or internal, or is a constructor/fallback/receive.
    """

    def format_var(var: "LocalVariable", unroll: bool) -> str:
        if unroll:
            return (
                convert_type_for_solidity_signature_to_string(var.type)
                .replace("(", "")
                .replace(")", "")
            )
        if var.type.is_dynamic:
            return f"{_handle_dynamic_struct_elem(var.type)} {var.location}"
        if isinstance(var.type, ArrayType) and isinstance(
            var.type.type, (UserDefinedType, ElementaryType)
        ):
            return (
                convert_type_for_solidity_signature_to_string(var.type)
                .replace("(", "")
                .replace(")", "")
                + f" {var.location}"
            )
        if isinstance(var.type, UserDefinedType):
            if isinstance(var.type.type, Structure):
                return f"{str(var.type.type)} memory"
            if isinstance(var.type.type, Enum):
                return str(var.type.type)
            if isinstance(var.type.type, Contract):
                return "address"
        if isinstance(var.type, TypeAlias):
            return str(var.type.type)
        return str(var.type)

    name, _, _ = func.signature
    if (
        func not in func.contract.functions_entry_points
        or func.is_constructor
        or func.is_fallback
        or func.is_receive
    ):
        return None
    view = " view" if func.view and not func.pure else ""
    pure = " pure" if func.pure else ""
    payable = " payable" if func.payable else ""
    # Make sure the function doesn't return a struct with nested mappings
    for ret in func.returns:
        if isinstance(ret.type, UserDefinedType) and isinstance(ret.type.type, Structure):
            for elem in ret.type.type.elems_ordered:
                if isinstance(elem.type, MappingType):
                    return ""
    returns = [format_var(ret, unroll_structs) for ret in func.returns]
    parameters = [format_var(param, unroll_structs) for param in func.parameters]
    _interface_signature_str = (
        name + "(" + ",".join(parameters) + ") external" + payable + pure + view
    )
    if len(returns) > 0:
        _interface_signature_str += " returns (" + ",".join(returns) + ")"
    return _interface_signature_str


def generate_struct_interface_str(struct: "Structure", indent: int = 0) -> str:
    """
    Generates code for a structure declaration in an interface of the form:
        struct struct_name {
            elem1_type elem1_name;
            elem2_type elem2_name;
            ...        ...
        }
    Args:
        struct: A Structure object.
        indent: Number of spaces to indent the code block with.

    Returns:
        The structure declaration code as a string.
    """
    spaces = ""
    for _ in range(0, indent):
        spaces += " "
    definition = f"{spaces}struct {struct.name} {{\n"
    for elem in struct.elems_ordered:
        if elem.type.is_dynamic:
            definition += f"{spaces}    {_handle_dynamic_struct_elem(elem.type)} {elem.name};\n"
        elif isinstance(elem.type, UserDefinedType):
            if isinstance(elem.type.type, Structure):
                definition += f"{spaces}    {elem.type.type} {elem.name};\n"
            else:
                definition += f"{spaces}    {convert_type_for_solidity_signature_to_string(elem.type)} {elem.name};\n"
        elif isinstance(elem.type, TypeAlias):
            definition += f"{spaces}    {elem.type.type} {elem.name};\n"
        else:
            definition += f"{spaces}    {elem.type} {elem.name};\n"
    definition += f"{spaces}}}\n"
    return definition


def _handle_dynamic_struct_elem(elem_type: Type) -> str:
    assert elem_type.is_dynamic
    if isinstance(elem_type, ElementaryType):
        return f"{elem_type}"
    if isinstance(elem_type, ArrayType):
        base_type = elem_type.type
        if isinstance(base_type, UserDefinedType):
            if isinstance(base_type.type, Contract):
                return "address[]"
            if isinstance(base_type.type, Enum):
                return convert_type_for_solidity_signature_to_string(elem_type)
            return f"{base_type.type.name}[]"
        return f"{base_type}[]"
    if isinstance(elem_type, MappingType):
        type_to = elem_type.type_to
        type_from = elem_type.type_from
        if isinstance(type_from, UserDefinedType) and isinstance(type_from.type, Contract):
            type_from = ElementaryType("address")
        if isinstance(type_to, MappingType):
            return f"mapping({type_from} => {_handle_dynamic_struct_elem(type_to)})"
        if isinstance(type_to, UserDefinedType):
            if isinstance(type_to.type, Contract):
                return f"mapping({type_from} => address)"
            return f"mapping({type_from} => {type_to.type.name})"
        return f"{elem_type}"
    return ""


def generate_custom_error_interface(
    error: "CustomErrorContract", unroll_structs: bool = True
) -> str:
    args = [
        convert_type_for_solidity_signature_to_string(arg.type).replace("(", "").replace(")", "")
        if unroll_structs
        else str(arg.type.type)
        if isinstance(arg.type, UserDefinedType) and isinstance(arg.type.type, (Structure, Enum))
        else str(arg.type)
        for arg in error.parameters
    ]
    return f"{error.name}({', '.join(args)})"
