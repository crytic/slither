`slither-flat` produces a flattened version of the codebase.

## Features
- Code flattening
- Support multiple [strategies](#strategies)
- Support circular dependency
- Support all the compilation platforms (Truffle, embark, buidler, etherlime, ...).

## Usage
`slither-flat target`

- `--contract ContractName`: flatten only one contract (standalone file)
### Strategies
`slither-flat` contains three strategies that can be specified with the `--strategy` flag:
- `MostDerived`: Export all the most derived contracts (every file is standalone)
- `OneFile`: Export all the contracts in one standalone file
- `LocalImport`: Export every contract in one separate file, and include import ".." in their preludes

Default: `MostDerived`

### Patching
`slither-flat` can transform the codebase to help some usage (eg. [Echidna](https://github.com/crytic/echidna))
- `--convert-external`: convert `external` function to `public`. This is meant to facilitate [Echidna](https://github.com/crytic/echidna) usage.
- `--contract name`:  To flatten only a target contract
- `--remove-assert`: Remove call to assert().

### Export option
- `--dir DirName`: output directory
- `--json file.json`: export the results to a json file (`--json -` output to the standard output
- `--zip file.zip`: export to a zip file 
- `--zip-type type`: Zip compression type (default lzma))


