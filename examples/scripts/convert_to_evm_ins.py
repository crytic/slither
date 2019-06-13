import sys
from slither.slither import Slither
from slither.evm.convert import get_evm_instructions


if len(sys.argv) != 2:
    print('python function_called.py functions_called.sol')
    exit(-1)

# Init slither
slither = Slither(sys.argv[1])

# Get the contract evm instructions
contract = slither.get_contract_from_name('Test')
contract_ins = get_evm_instructions(contract)
print("## Contract evm instructions: {} ##".format(contract.name))
print(contract_ins)

# Get the function evm instructions
function = contract.get_function_from_signature('foo()')
print("## Function evm instructions: {} ##".format(function.name))
function_ins = get_evm_instructions(function)
print(function_ins)
    
# Get the node evm instructions
nodes = function.nodes
for node in nodes:
    node_ins = get_evm_instructions(node)
    print("Node evm instructions: {}".format(str(node)))
    print(node_ins)
