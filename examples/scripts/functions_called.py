from slither.slither import Slither

# Init slither
slither = Slither('functions_called.sol')

# Get the contract
contract = slither.get_contract_from_name('Contract')

# Get the variable
entry_point = contract.get_function_from_signature('entry_point()')

all_calls = entry_point.all_calls()

all_calls_formated = [f.contract.name + '.' + f.name for f in all_calls]

# Print the result
print('From entry_point the functions reached are {}'.format(all_calls_formated))
