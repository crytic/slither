from slither.core.declarations import Contract
from slither.core.variables.state_variable import StateVariable
from slither.core.solidity_types import ArrayType, ElementaryType


def is_upgradable_gap_variable(contract: Contract, variable: StateVariable) -> bool:
    """Helper function that returns true if 'variable' is a gap variable used
    for upgradable contracts. More specifically, the function returns true if:
     - variable is named "__gap"
     - it is a uint256 array declared at the end of the contract
     - it has private visibility"""

    last_declared_variable = [
        v for v in contract.state_variables_ordered if v in contract.state_variables_declared
    ][-1]
    return (
        variable.name == "__gap"
        and last_declared_variable is variable
        and isinstance(variable.type, ArrayType)
        and variable.type.type == ElementaryType("uint256")
        and variable.visibility == "private"
    )
