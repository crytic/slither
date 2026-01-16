# Exercise 3: Find function that use a given variable in a condition

The [exercises/exercise3/find.sol](./exercises/exercise3/find.sol) file contains a contract that use `my_variable` variable in multiple locations.

Our goal is to create a script that list all the functions that use `my_variable` in a conditional or require statement.

## Proposed Approach

Explore all the helpers provided by [`Function`](https://github.com/crytic/slither/blob/master/slither/core/declarations/function.py) object to find an easy way to reach the goal

## Solution

Refer to [exercises/exercise3/solution.py](./exercises/exercise3/solution.py) for the solution.
