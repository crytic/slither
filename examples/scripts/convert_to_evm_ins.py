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
print("Contract evm instructions: " + str(contract_ins))

# Get the function evm instructions
function = contract.get_function_from_signature('foo()')
function_ins = get_evm_instructions(function)
print("Function evm instructions: " + str(function_ins))

# Get the node evm instructions
nodes = function.nodes
for node in nodes:
    print("Node: " + str(node))
    node_ins = get_evm_instructions(node)
    print("Node evm instructions: " + str(node_ins))

