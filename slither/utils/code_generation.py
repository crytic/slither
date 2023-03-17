# Functions for generating Solidity code
from typing import TYPE_CHECKING, Optional

from slither.core.declarations.contract import Contract
from slither.core.solidity_types.user_defined_type import UserDefinedType

if TYPE_CHECKING:
    from slither.core.declarations import FunctionContract, Structure


def generate_interface(contract: "Contract") -> str:
    """
    Generates code for a Solidity interface to the contract.
    Args:
        contract: A Contract object

    Returns:
        A string with the code for an interface, with function stubs for all public or external functions and
        state variables, as well as any events, custom errors and/or structs declared in the contract.
    """
    interface = f"interface I{contract.name} {{\n"
    for event in contract.events:
        name, args = event.signature
        interface += f"    event {name}({','.join(args)});\n"
    for error in contract.custom_errors:
        interface += f"    error {error.solidity_signature};\n"
    for struct in contract.structures:
        interface += generate_struct_interface_str(struct)
    for var in contract.state_variables_entry_points:
        interface += f"    function {var.signature_str.replace('returns', 'external returns ')};\n"
    for func in contract.functions_entry_points:
        if func.is_constructor or func.is_fallback or func.is_receive:
            continue
        interface += f"    function {generate_interface_function_signature(func)};\n"
    interface += "}\n\n"
    return interface


def generate_interface_function_signature(func: "FunctionContract") -> Optional[str]:
    """
    Generates a string of the form:
        func_name(type1,type2) external {payable/view/pure} returns (type3)

    Args:
        func: A FunctionContract object

    Returns:
        The function interface as a str (contains the return values).
        Returns None if the function is private or internal, or is a constructor/fallback/receive.
    """

    name, parameters, return_vars = func.signature
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
        "address"
        if isinstance(ret.type, UserDefinedType) and isinstance(ret.type.type, Contract)
        else str(ret.type)
        for ret in func.returns
    ]
    _interface_signature_str = (
        name + "(" + ",".join(parameters) + ") external" + payable + pure + view
    )
    if len(return_vars) > 0:
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
        definition += f"        {elem.type} {elem.name};\n"
    definition += "    }\n"
    return definition
