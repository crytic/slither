from slither import Slither
from slither.analyses.data_dependency.data_dependency import is_dependent, is_tainted, pprint_dependency
from slither.core.declarations.solidity_variables import SolidityVariableComposed

slither = Slither('data_dependency.sol')

contract = slither.get_contract_from_name('Simple')

destination = contract.get_state_variable_from_name('destination')
source = contract.get_state_variable_from_name('source')

print('{} is dependent of {}: {}'.format(source, destination, is_dependent(source, destination, contract)))
assert not is_dependent(source, destination, contract)
print('{} is dependent of {}: {}'.format(destination, source, is_dependent(destination, source, contract)))
assert is_dependent(destination, source, contract)
print('{} is tainted {}'.format(source, is_tainted(source, contract, slither)))
assert not is_tainted(source, contract, slither)
print('{} is tainted {}'.format(destination, is_tainted(destination, contract, slither)))
assert is_tainted(destination, contract, slither)

contract = slither.get_contract_from_name('Reference')

destination = contract.get_state_variable_from_name('destination')
source = contract.get_state_variable_from_name('source')

print('Reference contract')
print('{} is dependent of {}: {}'.format(source, destination, is_dependent(source, destination, contract)))
assert not is_dependent(source, destination, contract)
print('{} is dependent of {}: {}'.format(destination, source, is_dependent(destination, source, contract)))
assert is_dependent(destination, source, contract)
print('{} is tainted {}'.format(source, is_tainted(source, contract, slither)))
assert not is_tainted(source, contract, slither)
print('{} is tainted {}'.format(destination, is_tainted(destination, contract, slither)))
assert is_tainted(destination, contract, slither)

destination_indirect_1 = contract.get_state_variable_from_name('destination_indirect_1')
print('{} is tainted {}'.format(destination_indirect_1, is_tainted(destination_indirect_1, contract, slither)))
assert is_tainted(destination_indirect_1, contract, slither)
destination_indirect_2 = contract.get_state_variable_from_name('destination_indirect_2')
print('{} is tainted {}'.format(destination_indirect_2, is_tainted(destination_indirect_2, contract, slither)))
assert is_tainted(destination_indirect_2, contract, slither)

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

