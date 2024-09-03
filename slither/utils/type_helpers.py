from typing import Union, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from slither.core.declarations import (
        Function,
        SolidityFunction,
        Contract,
        SolidityVariable,
    )
    from slither.core.variables.variable import Variable
    from slither.core.cfg.node import Node

### core.declaration
# pylint: disable=used-before-assignment
InternalCallType = Tuple[Union["Function", "SolidityFunction"], "Node"]
SolidityCallType = Tuple["SolidityFunction", "Node"]
HighLevelCallType = Tuple["Contract", Union["Function", "Variable"], "Node"]
LibraryCallType = Tuple["Contract", "Function", "Node"]
LowLevelCallType = Tuple[Union["Variable", "SolidityVariable"], str, "Node"]
