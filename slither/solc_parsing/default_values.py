from slither.core.expressions.literal import Literal
from slither.core.solidity_types.type import Type
from slither.core.declarations.contract import Contract
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.core.declarations.structure import Structure
from slither.core.declarations.enum import Enum
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.expression import Expression
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.member_access import MemberAccess
from slither.core.expressions.new_array import NewArray
from slither.core.expressions.tuple_expression import TupleExpression
from slither.core.expressions.type_conversion import TypeConversion
from slither.core.solidity_types.array_type import ArrayType
from slither.core.solidity_types.elementary_type import Byte, ElementaryType, Int, Uint
from slither.core.solidity_types.user_defined_type import UserDefinedType

def get_default_value(ty : Type) -> Expression:
    """
    When a Solidity variable declaration does not have an initializer expression,
    we use the expression returned by this function as a default initializer.
    """
    if isinstance(ty, ElementaryType) and (ty.type in Int + Uint + Byte + ["address"]):
        return Literal("0", ElementaryType(ty.type))
    elif isinstance(ty, ElementaryType) and (ty.type == "string"):
        return Literal("", ElementaryType("string"))
    elif isinstance(ty, ElementaryType) and (ty.type == "bool"):
        return Literal("false", ElementaryType("bool"))
    elif isinstance(ty, ArrayType) and ty.is_dynamic_array:
        return CallExpression(
            NewArray(1, ty.type),
            [Literal("0", ElementaryType("uint256"))],
            f"{ty.type}[] memory"
        )
    elif isinstance(ty, ArrayType) and ty.is_fixed_array:
        length = int(ty.length_value.value)
        return TupleExpression([get_default_value(ty.type) for _ in range(0, length)])
    elif isinstance(ty, UserDefinedType) and isinstance(ty.type, Enum):
        return MemberAccess(
            "min",
            ty,
            CallExpression(
                Identifier(SolidityFunction("type()")),
                [Identifier(ty.type)],
                f"type(enum {ty.type.name})"
            )
        )
    elif isinstance(ty, UserDefinedType) and isinstance(ty.type, Structure):
        return CallExpression(
            Identifier(ty.type),
            [get_default_value(field.type) for field in ty.type.elems_ordered],
            f"struct {ty.type.name} memory"
        )
    elif isinstance(ty, UserDefinedType) and isinstance(ty.type, Contract):
        return TypeConversion(
            TypeConversion(Literal("0", ElementaryType("uint256")), ElementaryType("address")),
            UserDefinedType(ty.type)
        )
    assert False # unreachable
