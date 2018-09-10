from slither.slither import Slither

# Init slither
slither = Slither('functions_writing.sol')

# Get the contract
contract = slither.get_contract_from_name('Contract')

# Get the variable
var_a = contract.get_state_variable_from_name('a')

# Get the functions writing the variable
functions_writing_a = contract.get_functions_writing_variable(var_a)

# Print the result
print('The function writing "a" are {}'.format([f.name for f in functions_writing_a]))
