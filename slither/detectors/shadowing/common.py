from slither.core.declarations import Contract
from slither.core.variables.state_variable import StateVariable
from slither.core.solidity_types import ArrayType, ElementaryType


def is_upgradable_gap_variable(contract: Contract, variable: StateVariable) -> bool:
    """Helper function that returns true if 'variable' is a gap variable used
    for upgradable contracts. More specifically, the function returns true if:
     - variable is named "__gap"
     - it is a uint256 array declared at the end of the contract
     - it has private visibility"""

    # Return early on if the variable name is != gap to avoid iterating over all the state variables
    if variable.name != "__gap":
        return False

    declared_variable_ordered = [
        v for v in contract.state_variables_ordered if v in contract.state_variables_declared
    ]

    if not declared_variable_ordered:
        return False

    variable_type = variable.type
    return (
        declared_variable_ordered[-1] is variable
        and isinstance(variable_type, ArrayType)
        and variable_type.type == ElementaryType("uint256")
        and variable.visibility == "private"
    )
