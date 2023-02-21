# pylint: disable=unused-import
from slither.tools.upgradeability.checks.constant import BecameConstant, WereConstant
from slither.tools.upgradeability.checks.functions_ids import (
    FunctionShadowing,
    IDCollision,
)
from slither.tools.upgradeability.checks.initialization import (
    InitializableInherited,
    InitializableInitializer,
    InitializablePresent,
    InitializeTarget,
    MissingCalls,
    MissingInitializerModifier,
    MultipleCalls,
)
from slither.tools.upgradeability.checks.variable_initialization import VariableWithInit
from slither.tools.upgradeability.checks.variables_order import (
    DifferentVariableContractNewContract,
    DifferentVariableContractProxy,
    ExtraVariablesNewContract,
    ExtraVariablesProxy,
    MissingVariable,
)
