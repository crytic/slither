from typing import Dict, List, TYPE_CHECKING, Union
from slither.core.solidity_types.type import Type

if TYPE_CHECKING:
    from slither.core.declarations import Function

USING_FOR_KEY = Union[str, Type]
USING_FOR_ITEM = List[Union[Type, "Function"]]
USING_FOR = Dict[USING_FOR_KEY, USING_FOR_ITEM]


def _merge_using_for(uf1: USING_FOR, uf2: USING_FOR) -> USING_FOR:
    result = {**uf1, **uf2}
    for key, value in result.items():
        if key in uf1 and key in uf2:
            result[key] = value + uf1[key]
    return result
