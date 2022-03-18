import sys
from slither import Slither

if len(sys.argv) != 2:
    print("python slithIR.py contract.sol")
    sys.exit(-1)

# Init slither
slither = Slither(sys.argv[1])

# Iterate over all the contracts
for contract in slither.contracts:

    # Iterate over all the functions
    for function in contract.functions:

        # Dont explore inherited functions
        if function.contract_declarer == contract:

            print(f"Function: {function.name}")

            # Iterate over the nodes of the function
            for node in function.nodes:

                # Print the Solidity expression of the nodes
                # And the SlithIR operations
                if node.expression:

                    print(f"\tSolidity expression: {node.expression}")
                    print("\tSlithIR:")
                    for ir in node.irs:
                        print(f"\t\t\t{ir}")
