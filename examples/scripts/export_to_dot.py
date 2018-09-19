import sys
from slither.slither import Slither


if len(sys.argv) != 4:
    print('python.py function_called.py functions_called.sol Contract function()')
    exit(-1)

# Init slither
slither = Slither(sys.argv[1])

contract = slither.get_contract_from_name(sys.argv[2])
test = contract.get_function_from_signature(sys.argv[3])

test.cfg_to_dot('/tmp/test.dot')


