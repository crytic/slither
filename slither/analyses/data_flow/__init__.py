from slither.analyses.data_flow.direction import Forward
from slither import Slither

slither = Slither("../contracts/Storage.sol")

contracts = slither.contracts
for contract in contracts:
    functions = contract.functions
    for function in functions:
        nodes = function.nodes
        Forward().apply_transfer_function(nodes=nodes)


