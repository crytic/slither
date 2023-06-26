# Slither-interface

Generates code for a Solidity interface from contract

## Usage

Run `slither-interface <ContractName> <source file or deployment address>`.

## CLI Interface
```shell
positional arguments:
  contract_source       The name of the contract (case sensitive) followed by the deployed contract address if verified on etherscan or project directory/filename for local contracts.

optional arguments:
  -h, --help            show this help message and exit
  --unroll-structs      Whether to use structures' underlying types instead of the user-defined type
  --exclude-events      Excludes event signatures in the interface
  --exclude-errors      Excludes custom error signatures in the interface
  --exclude-enums       Excludes enum definitions in the interface
  --exclude-structs     Exclude struct definitions in the interface
```