from typing import Union

from slither.core import variables
from slither.core.declarations import (
    SolidityVariable,
    SolidityVariableComposed,
    Structure,
    Enum,
    Contract,
)
from slither.core import solidity_types
from slither.slithir import operations
from slither.slithir import variables as SlitherIRVariable


# pylint: disable=too-many-branches
def ntype(_type: Union[solidity_types.Type, str]) -> str:
    if isinstance(_type, solidity_types.ElementaryType):
        _type = str(_type)
    elif isinstance(_type, solidity_types.ArrayType):
        if isinstance(_type.type, solidity_types.ElementaryType):
            _type = str(_type)
        else:
            _type = "user_defined_array"
    elif isinstance(_type, Structure):
        _type = str(_type)
    elif isinstance(_type, Enum):
        _type = str(_type)
    elif isinstance(_type, solidity_types.MappingType):
        _type = str(_type)
    elif isinstance(_type, solidity_types.UserDefinedType):
        if isinstance(_type.type, Contract):
            _type = f"contract({_type.type.name})"
        elif isinstance(_type.type, Structure):
            _type = f"struct({_type.type.name})"
        elif isinstance(_type.type, Enum):
            _type = f"enum({_type.type.name})"
    else:
        _type = str(_type)

    _type = _type.replace(" memory", "")
    _type = _type.replace(" storage ref", "")

    if "struct" in _type:
        return "struct"
    if "enum" in _type:
        return "enum"
    if "tuple" in _type:
        return "tuple"
    if "contract" in _type:
        return "contract"
    if "mapping" in _type:
        return "mapping"
    return _type.replace(" ", "_")


# pylint: disable=too-many-branches
def encode_var_for_compare(var: Union[variables.Variable, SolidityVariable]) -> str:

    # variables
    if isinstance(var, SlitherIRVariable.Constant):
        return f"constant({ntype(var.type)},{var.value})"
    if isinstance(var, SolidityVariableComposed):
        return f"solidity_variable_composed({var.name})"
    if isinstance(var, SolidityVariable):
        return f"solidity_variable{var.name}"
    if isinstance(var, SlitherIRVariable.TemporaryVariable):
        return "temporary_variable"
    if isinstance(var, SlitherIRVariable.ReferenceVariable):
        return f"reference({ntype(var.type)})"
    if isinstance(var, variables.LocalVariable):
        return f"local_solc_variable({ntype(var.type)},{var.location})"
    if isinstance(var, variables.StateVariable):
        if not (var.is_constant or var.is_immutable):
            try:
                slot, _ = var.contract.compilation_unit.storage_layout_of(var.contract, var)
            except KeyError:
                slot = var.name
        else:
            slot = var.name
        return f"state_solc_variable({ntype(var.type)},{slot})"
    if isinstance(var, variables.LocalVariableInitFromTuple):
        return "local_variable_init_tuple"
    if isinstance(var, SlitherIRVariable.TupleVariable):
        return "tuple_variable"

    # default
    return ""


# pylint: disable=too-many-branches
def encode_ir_for_upgradeability_compare(ir: operations.Operation) -> str:
    # operations
    if isinstance(ir, operations.Assignment):
        return f"({encode_var_for_compare(ir.lvalue)}):=({encode_var_for_compare(ir.rvalue)})"
    if isinstance(ir, operations.Index):
        return f"index({ntype(ir.variable_right.type)})"
    if isinstance(ir, operations.Member):
        return "member"  # .format(ntype(ir._type))
    if isinstance(ir, operations.Length):
        return "length"
    if isinstance(ir, operations.Binary):
        return f"binary({encode_var_for_compare(ir.variable_left)}{ir.type}{encode_var_for_compare(ir.variable_right)})"
    if isinstance(ir, operations.Unary):
        return f"unary({str(ir.type)})"
    if isinstance(ir, operations.Condition):
        return f"condition({encode_var_for_compare(ir.value)})"
    if isinstance(ir, operations.NewStructure):
        return "new_structure"
    if isinstance(ir, operations.NewContract):
        return "new_contract"
    if isinstance(ir, operations.NewArray):
        return f"new_array({ntype(ir.array_type)})"
    if isinstance(ir, operations.NewElementaryType):
        return f"new_elementary({ntype(ir.type)})"
    if isinstance(ir, operations.Delete):
        return f"delete({encode_var_for_compare(ir.lvalue)},{encode_var_for_compare(ir.variable)})"
    if isinstance(ir, operations.SolidityCall):
        return f"solidity_call({ir.function.full_name})"
    if isinstance(ir, operations.InternalCall):
        return f"internal_call({ntype(ir.type_call)})"
    if isinstance(ir, operations.EventCall):  # is this useful?
        return "event"
    if isinstance(ir, operations.LibraryCall):
        return "library_call"
    if isinstance(ir, operations.InternalDynamicCall):
        return "internal_dynamic_call"
    if isinstance(ir, operations.HighLevelCall):  # TODO: improve
        return "high_level_call"
    if isinstance(ir, operations.LowLevelCall):  # TODO: improve
        return "low_level_call"
    if isinstance(ir, operations.TypeConversion):
        return f"type_conversion({ntype(ir.type)})"
    if isinstance(ir, operations.Return):  # this can be improved using values
        return "return"  # .format(ntype(ir.type))
    if isinstance(ir, operations.Transfer):
        return f"transfer({encode_var_for_compare(ir.call_value)})"
    if isinstance(ir, operations.Send):
        return f"send({encode_var_for_compare(ir.call_value)})"
    if isinstance(ir, operations.Unpack):  # TODO: improve
        return "unpack"
    if isinstance(ir, operations.InitArray):  # TODO: improve
        return "init_array"

    # default
    return ""


def encode_ir_for_halstead(ir: operations.Operation) -> str:
    # operations
    if isinstance(ir, operations.Assignment):
        return "assignment"
    if isinstance(ir, operations.Index):
        return "index"
    if isinstance(ir, operations.Member):
        return "member"  # .format(ntype(ir._type))
    if isinstance(ir, operations.Length):
        return "length"
    if isinstance(ir, operations.Binary):
        return f"binary({str(ir.type)})"
    if isinstance(ir, operations.Unary):
        return f"unary({str(ir.type)})"
    if isinstance(ir, operations.Condition):
        return f"condition({encode_var_for_compare(ir.value)})"
    if isinstance(ir, operations.NewStructure):
        return "new_structure"
    if isinstance(ir, operations.NewContract):
        return "new_contract"
    if isinstance(ir, operations.NewArray):
        return f"new_array({ntype(ir.array_type)})"
    if isinstance(ir, operations.NewElementaryType):
        return f"new_elementary({ntype(ir.type)})"
    if isinstance(ir, operations.Delete):
        return "delete"
    if isinstance(ir, operations.SolidityCall):
        return f"solidity_call({ir.function.full_name})"
    if isinstance(ir, operations.InternalCall):
        return f"internal_call({ntype(ir.type_call)})"
    if isinstance(ir, operations.EventCall):  # is this useful?
        return "event"
    if isinstance(ir, operations.LibraryCall):
        return "library_call"
    if isinstance(ir, operations.InternalDynamicCall):
        return "internal_dynamic_call"
    if isinstance(ir, operations.HighLevelCall):  # TODO: improve
        return "high_level_call"
    if isinstance(ir, operations.LowLevelCall):  # TODO: improve
        return "low_level_call"
    if isinstance(ir, operations.TypeConversion):
        return f"type_conversion({ntype(ir.type)})"
    if isinstance(ir, operations.Return):  # this can be improved using values
        return "return"  # .format(ntype(ir.type))
    if isinstance(ir, operations.Transfer):
        return "transfer"
    if isinstance(ir, operations.Send):
        return "send"
    if isinstance(ir, operations.Unpack):  # TODO: improve
        return "unpack"
    if isinstance(ir, operations.InitArray):  # TODO: improve
        return "init_array"
    # default
    raise NotImplementedError(f"encode_ir_for_halstead: {ir}")
