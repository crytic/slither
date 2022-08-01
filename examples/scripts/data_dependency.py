import sys

from slither import Slither
from slither.analyses.data_dependency.data_dependency import (
    is_dependent,
    is_tainted,
)
from slither.core.declarations.solidity_variables import SolidityVariableComposed

if len(sys.argv) != 2:
    print("Usage: python data_dependency.py file.sol")
    sys.exit(-1)

slither = Slither(sys.argv[1])

contracts = slither.get_contract_from_name("Simple")
assert len(contracts) == 1
contract = contracts[0]
destination = contract.get_state_variable_from_name("destination")
source = contract.get_state_variable_from_name("source")

print(f"{source} is dependent of {destination}: {is_dependent(source, destination, contract)}")
assert not is_dependent(source, destination, contract)
print(f"{destination} is dependent of {source}: {is_dependent(destination, source, contract)}")
assert is_dependent(destination, source, contract)
print(f"{source} is tainted {is_tainted(source, contract)}")
assert not is_tainted(source, contract)
print(f"{destination} is tainted {is_tainted(destination, contract)}")
assert is_tainted(destination, contract)

contracts = slither.get_contract_from_name("Reference")
assert len(contracts) == 1
contract = contracts[0]
destination = contract.get_state_variable_from_name("destination")
assert destination
source = contract.get_state_variable_from_name("source")
assert source

print("Reference contract")
print(f"{source} is dependent of {destination}: {is_dependent(source, destination, contract)}")
assert not is_dependent(source, destination, contract)
print(f"{destination} is dependent of {source}: {is_dependent(destination, source, contract)}")
assert is_dependent(destination, source, contract)
print(f"{source} is tainted {is_tainted(source, contract)}")
assert not is_tainted(source, contract)
print(f"{destination} is tainted {is_tainted(destination, contract)}")
assert is_tainted(destination, contract)

destination_indirect_1 = contract.get_state_variable_from_name("destination_indirect_1")
print(f"{destination_indirect_1} is tainted {is_tainted(destination_indirect_1, contract)}")
assert is_tainted(destination_indirect_1, contract)
destination_indirect_2 = contract.get_state_variable_from_name("destination_indirect_2")
print(f"{destination_indirect_2} is tainted {is_tainted(destination_indirect_2, contract)}")
assert is_tainted(destination_indirect_2, contract)

print("SolidityVar contract")

contracts = slither.get_contract_from_name("SolidityVar")
assert len(contracts) == 1
contract = contracts[0]
addr_1 = contract.get_state_variable_from_name("addr_1")
assert addr_1
addr_2 = contract.get_state_variable_from_name("addr_2")
assert addr_2
msgsender = SolidityVariableComposed("msg.sender")
print(f"{addr_1} is dependent of {msgsender}: {is_dependent(addr_1, msgsender, contract)}")
assert is_dependent(addr_1, msgsender, contract)
print(f"{addr_2} is dependent of {msgsender}: {is_dependent(addr_2, msgsender, contract)}")
assert not is_dependent(addr_2, msgsender, contract)


print("Intermediate contract")
contracts = slither.get_contract_from_name("Intermediate")
assert len(contracts) == 1
contract = contracts[0]
destination = contract.get_state_variable_from_name("destination")
assert destination
source = contract.get_state_variable_from_name("source")
assert source

print(f"{destination} is dependent of {source}: {is_dependent(destination, source, contract)}")
assert is_dependent(destination, source, contract)

print("Base Derived contract")
contracts = slither.get_contract_from_name("Base")
assert len(contracts) == 1
contract = contracts[0]
contract_derived = slither.get_contract_from_name("Derived")[0]
destination = contract.get_state_variable_from_name("destination")
source = contract.get_state_variable_from_name("source")

print(f"{destination} is dependent of {source}: {is_dependent(destination, source, contract)}")
assert not is_dependent(destination, source, contract)
print(
    f"{destination} is dependent of {source}: {is_dependent(destination, source, contract_derived)}"
)
assert is_dependent(destination, source, contract_derived)

print("PropagateThroughArguments contract")
contracts = slither.get_contract_from_name("PropagateThroughArguments")
assert len(contracts) == 1
contract = contracts[0]
var_tainted = contract.get_state_variable_from_name("var_tainted")
assert var_tainted
var_not_tainted = contract.get_state_variable_from_name("var_not_tainted")
assert var_not_tainted
var_dependant = contract.get_state_variable_from_name("var_dependant")
assert var_dependant

f = contract.get_function_from_signature("f(uint256)")
assert f
user_input = f.parameters[0]
f2 = contract.get_function_from_signature("f2(uint256,uint256)")

print(
    f"{var_dependant} is dependent of {user_input}: {is_dependent(var_dependant, user_input, contract)} (base)"
)
assert is_dependent(var_dependant, user_input, contract)
print(f"{var_tainted} is tainted: {is_tainted(var_tainted, contract)}")
assert is_tainted(var_tainted, contract)
print(f"{var_not_tainted} is tainted: {is_tainted(var_not_tainted, contract)}")
assert not is_tainted(var_not_tainted, contract)
