# Functions for generating Solidity code
from typing import TYPE_CHECKING, Optional

from slither.utils.type import (
    convert_type_for_solidity_signature_to_string,
    export_nested_types_from_variable,
    export_return_type_from_variable,
)
from slither.core.solidity_types import Type, UserDefinedType, MappingType, ArrayType, ElementaryType
from slither.core.declarations import Structure, Enum, Contract

if TYPE_CHECKING:
    from slither.core.declarations import FunctionContract, CustomErrorContract
    from slither.core.variables import StateVariable


# pylint: disable=too-many-arguments
def generate_interface(
    contract: "Contract",
    unroll_structs: bool = True,
    skip_events: bool = False,
    skip_errors: bool = False,
    skip_enums: bool = False,
    skip_structs: bool = False,
) -> str:
    """
    Generates code for a Solidity interface to the contract.
    Args:
        contract: A Contract object.
        unroll_structs: Specifies whether to use structures' underlying types instead of the user-defined type.

    Returns:
        A string with the code for an interface, with function stubs for all public or external functions and
        state variables, as well as any events, custom errors and/or structs declared in the contract.
    """
    interface = f"interface I{contract.name} {{\n"
    if not skip_events:
        for event in contract.events:
            name, args = event.signature
            interface += f"    event {name}({', '.join(args)});\n"
    if not skip_errors:
        for error in contract.custom_errors:
            interface += f"    error {generate_custom_error_interface(error, unroll_structs)};\n"
    if not skip_enums:
        for enum in contract.enums:
            interface += f"    enum {enum.name} {{ {', '.join(enum.values)} }}\n"
    if not skip_structs:
        for struct in contract.structures:
            interface += generate_struct_interface_str(struct, indent=4)
    for var in contract.state_variables_entry_points:
        interface += f"    function {generate_interface_variable_signature(var, unroll_structs)};\n"
    for func in contract.functions_entry_points:
        if func.is_constructor or func.is_fallback or func.is_receive:
            continue
        interface += (
            f"    function {generate_interface_function_signature(func, unroll_structs)};\n"
        )
    interface += "}\n\n"
    return interface


def generate_interface_variable_signature(
    var: "StateVariable", unroll_structs: bool = True
) -> Optional[str]:
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

    Returns:
        The function interface as a str (contains the return values).
        Returns None if the function is private or internal, or is a constructor/fallback/receive.
    """

    name, _, _ = func.signature
    if (
        func not in func.contract.functions_entry_points
        or func.is_constructor
        or func.is_fallback
        or func.is_receive
    ):
        return None
    view = " view" if func.view else ""
    pure = " pure" if func.pure else ""
    payable = " payable" if func.payable else ""
    returns = [
        convert_type_for_solidity_signature_to_string(ret.type).replace("(", "").replace(")", "")
        if unroll_structs
        else convert_type_for_solidity_signature_to_string(ret.type)
        .replace("(", "")
        .replace(")", "")
        + f" {ret.location}"
        if isinstance(ret.type, ArrayType)
        and isinstance(ret.type.type, (UserDefinedType, ElementaryType))
        else f"{str(ret.type.type)} memory"
        if isinstance(ret.type, UserDefinedType) and isinstance(ret.type.type, (Structure, Enum))
        else "address"
        if isinstance(ret.type, UserDefinedType) and isinstance(ret.type.type, Contract)
        else f"{ret.type} {ret.location}"
        if ret.type.is_dynamic
        else str(ret.type)
        for ret in func.returns
    ]
    parameters = [
        convert_type_for_solidity_signature_to_string(param.type).replace("(", "").replace(")", "")
        if unroll_structs
        else convert_type_for_solidity_signature_to_string(param.type)
        .replace("(", "")
        .replace(")", "")
        + f" {param.location}"
        if isinstance(param.type, ArrayType)
        and isinstance(param.type.type, (UserDefinedType, ElementaryType))
        else f"{str(param.type.type)} memory"
        if isinstance(param.type, UserDefinedType)
        and isinstance(param.type.type, (Structure, Enum))
        else "address"
        if isinstance(param.type, UserDefinedType) and isinstance(param.type.type, Contract)
        else f"{param.type} {param.location}"
        if param.type.is_dynamic
        else str(param.type)
        for param in func.parameters
    ]
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
        if isinstance(elem.type, UserDefinedType):
            if isinstance(elem.type.type, (Structure, Enum)):
                definition += f"{spaces}    {elem.type.type} {elem.name};\n"
            elif isinstance(elem.type.type, Contract):
                definition += f"{spaces}    address {elem.name};\n"
        else:
            definition += f"{spaces}    {elem.type} {elem.name};\n"
    definition += f"{spaces}}}\n"
    return definition


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
