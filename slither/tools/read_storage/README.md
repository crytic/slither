# Slither-read-storage

Slither-read-storage is a tool to retrieve the storage slots and values of entire contracts or single variables.

## Usage

### CLI Interface

```shell
positional arguments:
  contract_source (DIR) ADDRESS     The deployed contract address if verified on etherscan. Prepend project directory for unverified contracts.

optional arguments:
  --variable-name VARIABLE_NAME     The name of the variable whose value will be returned.
  --rpc-url RPC_URL                 An endpoint for web3 requests.
  --key KEY                         The key/ index whose value will be returned from a mapping or array.
  --deep-key DEEP_KEY               The key/ index whose value will be returned from a deep mapping or multidimensional array.
  --struct-var STRUCT_VAR           The name of the variable whose value will be returned from a struct.
  --storage-address STORAGE_ADDRESS The address of the storage contract (if a proxy pattern is used).
  --contract-name CONTRACT_NAME     The name of the logic contract.
  --layout                          Toggle used to write a JSON file with the entire storage layout.
  --value                           Toggle used to include values in output.
  --max-depth MAX_DEPTH             Max depth to search in data structure.
```

### Examples

Retrieve the storage slots of a local contract:

```shell
slither-read-storage file.sol 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8 --layout 
```

Retrieve the storage slots of a contract verified on an Etherscan-like platform:

```shell
slither-read-storage 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8 --layout
```

To retrieve the values as well, pass `--value` and `--rpc-url $RPC_URL`:

```shell
slither-read-storage 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8 --layout --rpc-url $RPC_URL --value
```

To view only the slot of the `slot0` structure variable, pass `--variable-name slot0`:

```shell
slither-read-storage 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8 --variable-name slot0 --rpc-url $RPC_URL --value
```

To view a member of the `slot0` struct, pass `--struct-var tick`

```shell
slither-read-storage 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8 --variable-name slot0 --rpc-url $RPC_URL --value --struct-var tick
```

Retrieve the ERC20 balance slot of an account:

```shell
slither-read-storage 0xa2327a938Febf5FEC13baCFb16Ae10EcBc4cbDCF --variable-name balances --key 0xab5801a7d398351b8be11c439e05c5b3259aec9b
```

To retrieve the actual balance, pass `--variable-name balances` and `--key 0xab5801a7d398351b8be11c439e05c5b3259aec9b`. (`balances` is a `mapping(address => uint)`)
Since this contract uses the delegatecall-proxy pattern, the proxy address must be passed as the `--storage-address`. Otherwise, it is not required.

```shell
slither-read-storage 0xa2327a938Febf5FEC13baCFb16Ae10EcBc4cbDCF --variable-name balances --key 0xab5801a7d398351b8be11c439e05c5b3259aec9b --storage-address 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 --rpc-url $RPC_URL --value
```

## Troubleshooting/FAQ

- If the storage slots or values of a contract verified Etherscan are wrong, try passing `--contract $CONTRACT_NAME` explicitly. Otherwise, the storage may be retrieved from storage slots based off an unrelated contract (Etherscan includes these). (Also, make sure that the RPC is for the correct network.)

- If Etherscan fails to return a source code, try passing `--etherscan-apikey $API_KEY` to avoid hitting a rate-limit.

- How do I use this tool on other chains?
  If an EVM chain has an Etherscan-like platform the crytic-compile supports, this tool supports it by making the following modifications.
  Take Avalanche, for instance:

  ```shell
  slither-read-storage avax:0x0000000000000000000000000000000000000000 --layout --value --rpc-url $AVAX_RPC_URL
  ```

## Limitations

- Requires source code.
- Only works on Solidity contracts.
- Cannot find variables with unstructured storage.
- Does not support all data types (please open an issue or PR).
- Mappings cannot be completely enumerated since all keys used historically are not immediately available.
