# Slither-mutate

`slither-mutate` is a mutation testing tool for solidity based smart contracts.

## Quick Start

In a foundry project with **passing** tests that are run with `forge test`, you can mutate all solidity files in the `src` folder by running the following:

`slither-mutate src --test-cmd='forge test'`

You can provide flags to `forge` as part of the `--test-cmd` parameter or target a single file path instead of the whole `src` directory, for example:

`slither-mutate src/core/MyContract.sol --test-cmd='forge test --match-contract="MyContract"'`

### CLI Interface

```shell
$ slither-mutate --help
usage: slither-mutate <codebase> --test-cmd <test command> <options>

Experimental smart contract mutator. Based on https://arxiv.org/abs/2006.11597

positional arguments:
  codebase              Codebase to analyze (.sol file, project directory, ...)

options:
  -h, --help            show this help message and exit
  --list-mutators       List available detectors
  --test-cmd TEST_CMD   Command to run the tests for your project
  --test-dir TEST_DIR   Tests directory
  --ignore-dirs IGNORE_DIRS
                        Directories to ignore
  --timeout TIMEOUT     Set timeout for test command (by default 30 seconds)
  --output-dir OUTPUT_DIR
                        Name of output directory (by default 'mutation_campaign')
  -v, --verbose         log mutants that are caught as well as those that are uncaught
  -vv, --very-verbose   log mutants that are caught, uncaught, and fail to compile. And more!
  --mutators-to-run MUTATORS_TO_RUN
                        mutant generators to run
  --contract-names CONTRACT_NAMES
                        list of contract names you want to mutate
  --comprehensive       continue testing minor mutations if severe mutants are uncaught
```
