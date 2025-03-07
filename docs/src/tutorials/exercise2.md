# Exercise 2: Access Control

The [exercises/exercise2/coin.sol](./exercises/exercise2/coin.sol) file contains an access control implementation with the `onlyOwner` modifier. A common mistake is forgetting to add the modifier to a crucial function. In this exercise, we will use Slither to implement a conservative access control approach.

Our goal is to create a script that ensures all public and external functions call `onlyOwner`, except for the functions on the whitelist.

## Proposed Algorithm

```
Create a whitelist of signatures
Explore all the functions
    If the function is in the whitelist of signatures:
        Skip
    If the function is public or external:
        If onlyOwner is not in the modifiers:
            A bug is found
```

## Solution

Refer to [exercises/exercise2/solution.py](./exercises/exercise2/solution.py) for the solution.
