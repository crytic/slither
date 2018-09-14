import sys
from slither.slither import Slither

if len(sys.argv) != 2:
    print('python.py variable_in_condition.py variable_in_condition.sol')
    exit(-1)

# Init slither
slither = Slither(sys.argv[1])

# Get the contract
contract = slither.get_contract_from_name('Contract')

# Get the variable
var_a = contract.get_state_variable_from_name('a')

# Get the functions reading the variable
functions_reading_a = contract.get_functions_reading_variable(var_a)

function_using_a_as_condition = [f for f in functions_reading_a if\
                                 f.is_reading_in_conditional_node(var_a) or\
                                 f.is_reading_in_require_or_assert(var_a)]

# Print the result
print('The function using "a" in condition are {}'.format([f.name for f in function_using_a_as_condition]))
