import sys
from slither import Slither
from slither.analyses.data_dependency.data_dependency import is_dependent, is_tainted, pprint_dependency
from slither.core.declarations.solidity_variables import SolidityVariableComposed

if len(sys.argv) != 2:
    print('Usage: python data_dependency.py file.sol')
    exit(-1)

slither = Slither(sys.argv[1])

contract = slither.get_contract_from_name('Simple')

destination = contract.get_state_variable_from_name('destination')
source = contract.get_state_variable_from_name('source')

print('{} is dependent of {}: {}'.format(source, destination, is_dependent(source, destination, contract)))
assert not is_dependent(source, destination, contract)
print('{} is dependent of {}: {}'.format(destination, source, is_dependent(destination, source, contract)))
assert is_dependent(destination, source, contract)
print('{} is tainted {}'.format(source, is_tainted(source, contract)))
assert not is_tainted(source, contract)
print('{} is tainted {}'.format(destination, is_tainted(destination, contract)))
assert is_tainted(destination, contract)

contract = slither.get_contract_from_name('Reference')

destination = contract.get_state_variable_from_name('destination')
source = contract.get_state_variable_from_name('source')

print('Reference contract')
print('{} is dependent of {}: {}'.format(source, destination, is_dependent(source, destination, contract)))
assert not is_dependent(source, destination, contract)
print('{} is dependent of {}: {}'.format(destination, source, is_dependent(destination, source, contract)))
assert is_dependent(destination, source, contract)
print('{} is tainted {}'.format(source, is_tainted(source, contract)))
assert not is_tainted(source, contract)
print('{} is tainted {}'.format(destination, is_tainted(destination, contract)))
assert is_tainted(destination, contract)

destination_indirect_1 = contract.get_state_variable_from_name('destination_indirect_1')
print('{} is tainted {}'.format(destination_indirect_1, is_tainted(destination_indirect_1, contract)))
assert is_tainted(destination_indirect_1, contract)
destination_indirect_2 = contract.get_state_variable_from_name('destination_indirect_2')
print('{} is tainted {}'.format(destination_indirect_2, is_tainted(destination_indirect_2, contract)))
assert is_tainted(destination_indirect_2, contract)

print('SolidityVar contract')

contract = slither.get_contract_from_name('SolidityVar')

addr_1 = contract.get_state_variable_from_name('addr_1')
addr_2 = contract.get_state_variable_from_name('addr_2')
msgsender = SolidityVariableComposed('msg.sender')
print('{} is dependent of {}: {}'.format(addr_1, msgsender, is_dependent(addr_1, msgsender, contract)))
assert is_dependent(addr_1, msgsender, contract)
print('{} is dependent of {}: {}'.format(addr_2, msgsender, is_dependent(addr_2, msgsender, contract)))
assert not is_dependent(addr_2, msgsender, contract)


print('Intermediate contract')
contract = slither.get_contract_from_name('Intermediate')
destination = contract.get_state_variable_from_name('destination')
source = contract.get_state_variable_from_name('source')

print('{} is dependent of {}: {}'.format(destination, source, is_dependent(destination, source, contract)))
assert is_dependent(destination, source, contract)

print('Base Derived contract')
contract = slither.get_contract_from_name('Base')
contract_derived = slither.get_contract_from_name('Derived')
destination = contract.get_state_variable_from_name('destination')
source = contract.get_state_variable_from_name('source')

print('{} is dependent of {}: {} (base)'.format(destination, source, is_dependent(destination, source, contract)))
assert not is_dependent(destination, source, contract)
print('{} is dependent of {}: {} (derived)'.format(destination, source, is_dependent(destination, source, contract_derived)))
assert is_dependent(destination, source, contract_derived)

print('PropagateThroughArguments contract')
contract = slither.get_contract_from_name('PropagateThroughArguments')
var_tainted = contract.get_state_variable_from_name('var_tainted')
var_not_tainted = contract.get_state_variable_from_name('var_not_tainted')
var_dependant = contract.get_state_variable_from_name('var_dependant')

f = contract.get_function_from_signature('f(uint256)')
user_input = f.parameters[0]
f2 = contract.get_function_from_signature('f2(uint256,uint256)')

print('{} is dependent of {}: {} (base)'.format(var_dependant, user_input, is_dependent(var_dependant, user_input, contract)))
assert is_dependent(var_dependant, user_input, contract)
print('{} is tainted: {}'.format(var_tainted, is_tainted(var_tainted, contract)))
assert is_tainted(var_tainted, contract)
print('{} is tainted: {}'.format(var_not_tainted, is_tainted(var_not_tainted, contract)))
assert not is_tainted(var_not_tainted, contract)
