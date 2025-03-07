# Exercise 1: Function Overridden Protection

The goal is to create a script that performs a feature that was not present in previous version of Solidity: function overriding protection.

[exercises/exercise1/coin.sol](./exercises/exercise1/coin.sol) contains a function that must never be overridden:

```solidity
_mint(address dst, uint256 val)
```

Use Slither to ensure that no contract inheriting Coin overrides this function.

Use `solc-select install 0.5.0 && solc-select use 0.5.0` to switch to solc 0.5.0

## Proposed Algorithm

```
Get the Coin contract
    For each contract in the project:
        If Coin is in the list of inherited contracts:
            Get the _mint function
            If the contract declaring the _mint function is not Coin:
                A bug is found.
```

## Tips

- To get a specific contract, use `slither.get_contract_from_name` (note: it returns a list)
- To get a specific function, use `contract.get_function_from_signature`

## Solution

See [exercises/exercise1/solution.py](./exercises/exercise1/solution.py).
