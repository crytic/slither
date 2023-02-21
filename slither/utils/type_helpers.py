from typing import TYPE_CHECKING, Tuple, Union

if TYPE_CHECKING:
    from slither.core.declarations import (
        Contract,
        Function,
        SolidityFunction,
        SolidityVariable,
    )
    from slither.core.variables.variable import Variable

### core.declaration
# pylint: disable=used-before-assignment
InternalCallType = Union[Function, SolidityFunction]
HighLevelCallType = Tuple[Contract, Union[Function, Variable]]
LibraryCallType = Tuple[Contract, Function]
LowLevelCallType = Tuple[Union[Variable, SolidityVariable], str]
