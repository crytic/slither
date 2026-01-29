from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    from slither.core.declarations import (
        Function,
        SolidityFunction,
        Contract,
        SolidityVariable,
    )
    from slither.core.variables.variable import Variable

### core.declaration

InternalCallType = Union["Function", "SolidityFunction"]
HighLevelCallType = tuple["Contract", Union["Function", "Variable"]]
LibraryCallType = tuple["Contract", "Function"]
LowLevelCallType = tuple[Union["Variable", "SolidityVariable"], str]
