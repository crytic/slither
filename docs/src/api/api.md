# API Basics

Slither has an API that allows you to explore basic attributes of contracts and their functions.

On a high level there are 6 layers:

- `Slither` - main slither object
- `SlitherCompilationUnit` - group of files used by one call to solc
- `Contract` - contract level
- `Function` - function level
- `Node` - control flow graph
- `SlithrIR` - intermediate representation

Watch our [API walkthrough](https://www.youtube.com/watch?v=Ijf0pellvgw) for more details

## Slither object

To load a codebase:

```python
from slither import Slither
slither = Slither('/path/to/project')
```

To load a contract deployed:

```python
from slither import Slither
slither = Slither('0x..') # assuming the code is verified on etherscan
```

Use `etherscan_api_key` to provide an [Etherscan API KEY](https://docs.etherscan.io/getting-started/viewing-api-usage-statistics)

```python
slither = Slither('0x..', etherscan_api_key='..')
```

You can retrieve the list of compilation units with:

- `sl.compilation_units # array of SlitherCompilationUnit`

## SlitherCompilationUnit object

- ~ group of files used by one call to solc
- Most targets have 1 compilation, but not always true
  - Partial compilation for optimization
  - Multiple solc version used
  - Etc..
- Why compilation unit matters?
  - Some APIs might be not intuitive
  - Ex: looking for a contract based on the name?
    - Can have multiple contracts
- For hacking you can (probably) use the first compilation unit
  - `compilation_unit = sl.compilation_units[0]`

A [`SlitherCompilationUnit`](https://github.com/crytic/slither/blob/master/slither/core/compilation_unit.py) has:

- `contracts (list(Contract))`: A list of contracts
- `contracts_derived (list(Contract))`: A list of contracts that are not inherited by another contract (a subset of contracts)
- `get_contract_from_name (str)`: Returns a list of contracts matching the name
- `[structures | enums | events | variables | functions]_top_level`: Top level object

Example

```python
from slither import Slither
sl = Slither("0xdac17f958d2ee523a2206206994597c13d831ec7")
compilation_unit = sl.compilation_units[0]

# Print all the contracts from the USDT address
print([str(c) for c in compilation_unit.contracts])

# Print the most derived contracts from the USDT address
print([str(c) for c in compilation_unit.contracts_derived])
```

```bash
% python test.py
['SafeMath', 'Ownable', 'ERC20Basic', 'ERC20', 'BasicToken', 'StandardToken', 'Pausable', 'BlackList', 'UpgradedStandardToken', 'TetherToken']

['SafeMath', 'UpgradedStandardToken', 'TetherToken']
```

## Contract Object

A [`Contract`](https://github.com/crytic/slither/blob/master/slither/core/declarations/contract.py) object has:

- `name: str`: The name of the contract
- `functions: list[Function]`: A list of functions
- `modifiers: list[Modifier]`: A list of modifiers
- `all_functions_called: list[Function/Modifier]`: A list of all internal functions reachable by the contract
- `inheritance: list[Contract]`: A list of inherited contracts (c3 linearization order)
- `derived_contracts: list[Contract]`: contracts derived from it
- `get_function_from_signature(str): Function`: Returns a Function from its signature
- `get_modifier_from_signature(str): Modifier`: Returns a Modifier from its signature
- `get_state_variable_from_name(str): StateVariable`: Returns a StateVariable from its name
- `state_variables: List[StateVariable]`: list of accessible variables
- `state_variables_ordered: List[StateVariable]`: all variable ordered by declaration

Example

```python
from slither import Slither
sl = Slither("0xdac17f958d2ee523a2206206994597c13d831ec7")
compilation_unit = sl.compilation_units[0]

# Print all the state variables of the USDT token
contract = compilation_unit.get_contract_from_name("TetherToken")[0]
print([str(v) for v in contract.state_variables])
```

```bash
% python test.py
['owner', 'paused', '_totalSupply', 'balances', 'basisPointsRate', 'maximumFee', 'allowed', 'MAX_UINT', 'isBlackListed', 'name', 'symbol', 'decimals', 'upgradedAddress', 'deprecated']
```

## Function object

A [`Function`](https://github.com/crytic/slither/blob/master/slither/core/declarations/function.py) or a `Modifier` object has:

- `name: str`: The name of the function
- `contract: Contract`: The contract where the function is declared
- `nodes: list[Node]`: A list of nodes composing the CFG of the function/modifier
- `entry_point: Node`: The entry point of the CFG
- `[state |local]_variable_[read |write]: list[StateVariable]`: A list of local/state variables read/write
  - All can be prefixed by “all\_” for recursive lookup
  - Ex: `all_state_variable_read`: return all the state variables read in internal calls
- `slithir_operations: List[Operation]`: list of IR operations

```python
from slither import Slither
sl = Slither("0xdac17f958d2ee523a2206206994597c13d831ec7")
compilation_unit = sl.compilation_units[0]
contract = compilation_unit.get_contract_from_name("TetherToken")[0]

transfer = contract.get_function_from_signature("transfer(address,uint256)")

# Print all the state variables read by the transfer function
print([str(v) for v in transfer.state_variables_read])
# Print all the state variables read by the transfer function and its internal calls
print([str(v) for v in transfer.all_state_variables_read])
```

```bash
% python test.py
['deprecated', 'isBlackListed', 'upgradedAddress']
['owner', 'basisPointsRate', 'deprecated', 'paused', 'isBlackListed', 'maximumFee', 'upgradedAddress', 'balances']
```

## Node object

[Node](https://github.com/crytic/slither/blob/master/slither/core/cfg/node.py)

To explore the nodes:

- If order does not matter
  - `for node in function.nodes`
- If order matters, walk through the nodes

```python
def visit_node(node: Node, visited: List[Node]):

    if node in visited:
        return
    visited += [node]

    # custom action
    for son in node.sons:
        visit_node(son, visited)
```

- If need to iterate more than once (advanced usages)
- Bound the iteration X times
- Create a fix-point - abstract interpretation style analysis

## SlithIR

- [slither/slithir](https://github.com/crytic/slither/tree/master/slither/slithir)
- Every IR operation has its own methods
- Check if an operation is of a type:
  - `isinstance(ir, TYPE)`
  - Ex: `isinstance(ir, Call)`
- Check if the operation is an addition
- `isinstance(ir, Binary) & ir.type == BinaryType.ADDITION`
- Check if the operation is a call to MyContract
- `isinstance(ir, HighLevelCall) & ir.destination == MyContract`

```python
from slither import Slither
sl = Slither("0xdac17f958d2ee523a2206206994597c13d831ec7")
compilation_unit = sl.compilation_units[0]
contract = compilation_unit.get_contract_from_name("TetherToken")[0]
totalSupply = contract.get_function_from_signature("totalSupply()")

# Print the external call made in the totalSupply function
for ir in totalSupply.slithir_operations:
    if isinstance(ir, HighLevelCall):
        print(f"External call found {ir} ({ir.node.source_mapping})")
```

```bash
% python test.py
External call found HIGH_LEVEL_CALL, […]   (...TetherToken.sol#339)
```

### Example: Print Basic Information

[print_basic_information.py](./examples/print_basic_information.py) demonstrates how to print basic information about a project.
