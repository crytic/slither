# Slither-mutate

`slither-mutate` is a mutation testing tool for solidity based smart contracts. 

## Usage

`slither-mutate <codebase> <test-cmd> <options>`

### CLI Interface

```
positional arguments:
  codebase              Codebase to analyze (.sol file, truffle directory, ...)
  test-cmd              Command to run the tests for your project

options:
  -h, --help            show this help message and exit
  --list-mutators       List available detectors
  --test-dir TEST_DIR   Tests directory
  --ignore-dirs IGNORE_DIRS
                        Directories to ignore
  --timeout TIMEOUT     Set timeout for test command (by default 30 seconds)
  --output-dir OUTPUT_DIR
                        Name of output Directory (by default 'mutation_campaign')
  --verbose             output all mutants generated
  --mutators-to-run MUTATORS_TO_RUN
                        mutant generators to run
  --contract-names CONTRACT_NAMES
                        list of contract names you want to mutate
  --quick               to stop full mutation if revert mutator passes
```