# Functions for generating Solidity code
from typing import TYPE_CHECKING, Optional

from slither.utils.type import (
    convert_type_for_solidity_signature_to_string,
    export_nested_types_from_variable,
    export_return_type_from_variable,
)
from slither.core.solidity_types import UserDefinedType, MappingType, ArrayType
from slither.core.declarations import Structure, Enum, Contract

if TYPE_CHECKING:
    from slither.core.declarations import FunctionContract, CustomErrorContract
    from slither.core.variables import StateVariable


def generate_interface(contract: "Contract", unroll_structs: bool = True) -> str:
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
    for event in contract.events:
        name, args = event.signature
        interface += f"    event {name}({', '.join(args)});\n"
    for error in contract.custom_errors:
        interface += generate_custom_error_interface(error, unroll_structs)
    for enum in contract.enums:
        interface += f"    enum {enum.name} {{ {', '.join(enum.values)} }}\n"
    for struct in contract.structures:
        interface += generate_struct_interface_str(struct)
    for var in contract.state_variables_entry_points:
        interface += generate_interface_variable_signature(var, unroll_structs)
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
        returns = []
        _type = var.type
        while isinstance(_type, MappingType):
            _type = _type.type_to
        while isinstance(_type, (ArrayType, UserDefinedType)):
            _type = _type.type
        ret = str(_type)
        if isinstance(_type, Structure):
            ret += " memory"
        elif isinstance(_type, Contract):
            ret = "address"
        returns.append(ret)
    return f"    function {var.name}({','.join(params)}) external returns ({', '.join(returns)});\n"


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
        else f"{str(ret.type.type)} memory"
        if isinstance(ret.type, UserDefinedType) and isinstance(ret.type.type, (Structure, Enum))
        else "address"
        if isinstance(ret.type, UserDefinedType) and isinstance(ret.type.type, Contract)
        else str(ret.type)
        for ret in func.returns
    ]
    parameters = [
        convert_type_for_solidity_signature_to_string(param.type).replace("(", "").replace(")", "")
        if unroll_structs
        else f"{str(param.type.type)} memory"
        if isinstance(param.type, UserDefinedType)
        and isinstance(param.type.type, (Structure, Enum))
        else "address"
        if isinstance(param.type, UserDefinedType) and isinstance(param.type.type, Contract)
        else str(param.type)
        for param in func.parameters
    ]
    _interface_signature_str = (
        name + "(" + ",".join(parameters) + ") external" + payable + pure + view
    )
    if len(returns) > 0:
        _interface_signature_str += " returns (" + ",".join(returns) + ")"
    return _interface_signature_str


def generate_struct_interface_str(struct: "Structure") -> str:
    """
    Generates code for a structure declaration in an interface of the form:
        struct struct_name {
            elem1_type elem1_name;
            elem2_type elem2_name;
            ...        ...
        }
    Args:
        struct: A Structure object

    Returns:
        The structure declaration code as a string.
    """
    definition = f"    struct {struct.name} {{\n"
    for elem in struct.elems_ordered:
        if isinstance(elem.type, UserDefinedType):
            if isinstance(elem.type.type, (Structure, Enum)):
                definition += f"        {elem.type.type} {elem.name};\n"
            elif isinstance(elem.type.type, Contract):
                definition += f"        address {elem.name};\n"
        else:
            definition += f"        {elem.type} {elem.name};\n"
    definition += "    }\n"
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
    return f"    error {error.name}({', '.join(args)});\n"
