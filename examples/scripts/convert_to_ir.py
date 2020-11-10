import sys
from slither.slither import Slither
from slither.slithir.convert import convert_expression


if len(sys.argv) != 2:
    print("python function_called.py functions_called.sol")
    sys.exit(-1)

# Init slither
slither = Slither(sys.argv[1])

# Get the contract
contract = slither.get_contract_from_name("Test")
assert contract
# Get the variable
test = contract.get_function_from_signature("one()")
assert test
nodes = test.nodes

for node in nodes:
    if node.expression:
        print("Expression:\n\t{}".format(node.expression))
        irs = convert_expression(node.expression, node)
        print("IR expressions:")
        for ir in irs:
            print("\t{}".format(ir))
        print()
