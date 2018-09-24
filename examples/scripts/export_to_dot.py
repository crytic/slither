import sys
from slither.slither import Slither


if len(sys.argv) != 2:
    print('python.py function_called.py')
    exit(-1)

# Init slither
slither = Slither(sys.argv[1])

for contract in slither.contracts:
    for function in contract.functions:
        filename = "{}-{}-{}.dot".format(sys.argv[1], contract.name, function.full_name)
        print('Export {}'.format(filename))
        function.slithir_cfg_to_dot(filename)


