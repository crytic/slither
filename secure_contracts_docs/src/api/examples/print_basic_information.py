import sys
from slither import Slither

# Init slither
slither = Slither('coin.sol')

for contract in slither.contracts:
    # Print the contract's name
    print(f'Contract: {contract.name}')
    # Print the name of the contract inherited
    print(f'\tInherit from{[c.name for c in contract.inheritance]}')
    for function in contract.functions:
        # For each function, print basic information
        print(f'\t{function.full_name}:')
        print(f'\t\tVisibility: {function.visibility}')
        print(f'\t\tContract: {function.contract}')
        print(f'\t\tModifier: {[m.name for m in function.modifiers]}')
        print(f'\t\tIs constructor? {function.is_constructor}')
