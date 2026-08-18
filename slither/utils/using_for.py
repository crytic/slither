from typing import TYPE_CHECKING, TypeAlias
from slither.core.solidity_types import Type, UserDefinedType

if TYPE_CHECKING:
    from slither.core.declarations import Function

USING_FOR_KEY: TypeAlias = "str | Type"  # "*" is wildcard
USING_FOR_ITEM: TypeAlias = "list[UserDefinedType | Function]"  # UserDefinedType.type is a library
USING_FOR: TypeAlias = "dict[USING_FOR_KEY, USING_FOR_ITEM]"


def merge_using_for(uf1: USING_FOR, uf2: USING_FOR) -> USING_FOR:
    result = {**uf1, **uf2}
    for key, value in result.items():
        if key in uf1 and key in uf2:
            result[key] = value + uf1[key]
    return result
