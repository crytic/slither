from slither.slither import Slither

slither = Slither("coin.sol")
coin = slither.get_contract_from_name("Coin")[0]

# Iterate over all the contracts
for contract in slither.contracts:
    # If the contract is derived from MyContract
    if coin in contract.inheritance:
        # Get the function definition
        mint = contract.get_function_from_signature("_mint(address,uint256)")
        # If the function was not declared by coin, there is a bug !
        # Detect error only for contracts overriding the '_mint' function
        if mint.contract_declarer == contract:
            print(f"Error, {contract} overrides {mint}")
