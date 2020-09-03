# pylint: disable=unused-import
from slither.tools.upgradeability.checks.initialization import (
    InitializablePresent,
    InitializableInherited,
    InitializableInitializer,
    MissingInitializerModifier,
    MissingCalls,
    MultipleCalls,
    InitializeTarget,
)

from slither.tools.upgradeability.checks.functions_ids import IDCollision, FunctionShadowing

from slither.tools.upgradeability.checks.variable_initialization import VariableWithInit

from slither.tools.upgradeability.checks.variables_order import (
    MissingVariable,
    DifferentVariableContractProxy,
    DifferentVariableContractNewContract,
    ExtraVariablesProxy,
    ExtraVariablesNewContract,
)

from slither.tools.upgradeability.checks.constant import WereConstant, BecameConstant
