# Data dependency

Data dependency allows knowing if the value of a given variable is influenced by another variable's value.

Because smart contracts have a state machine based architecture, the results of the data dependency depend on the context (function/contract) of the analysis. Consider the following example:
```solidity
contract MyContract{
    uint a = 0;
    uint b = 0;

    function setA(uint input_a) public{
        a = input_a;
    }

    function setB() public{
        b = a;
    }

}
```

In this example, if we consider only `setA`, we have the following dependency:
- `a` is dependent on `input_a` 

If we consider only `setB`, we have:
- `b` is dependent on `a`

If we consider the contract entirely (with all the functions), we have:
- `a` is dependent on `input_a` 
- `b` is dependent on `a` and `input_a` (by transitivity)

`slither.analyses.is_dependent(variable, variable_source, context)` allows to know if `variable` is dependent on `variable_source` on the given context.

As a result, in our previous example, `is_dependent(b, a, funcA)` will return `False`, while `is_dependent(b, a, myContract)` will return `True`:
```
from slither import Slither
from slither.analyses import is_dependent

slither = Slither('data_dependency_simple_example.sol')

myContract = slither.get_contract_from_name('MyContract')
funcA = myContract.get_function_from_signature('setA(uint256)')
input_a = funcA.parameters[0]

a = myContract.get_state_variable_from_name('a')
b = myContract.get_state_variable_from_name('b')

print(f'{b.name} is dependant from {input_a.name}?: {is_dependent(b, a, funcA)}')
print(f'{b.name} is dependant from {input_a.name}?: {is_dependent(b, a, myContract)}')
```

