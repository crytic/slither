# Slither, the Solidity source analyzer
[![Build Status](https://travis-ci.com/trailofbits/slither.svg?token=JEF97dFy1QsDCfQ2Wusd&branch=master)](https://travis-ci.com/trailofbits/slither)
[![Slack Status](https://empireslacking.herokuapp.com/badge.svg)](https://empireslacking.herokuapp.com)
[![PyPI version](https://badge.fury.io/py/slither-analyzer.svg)](https://badge.fury.io/py/slither-analyzer)

Slither is a Solidity static analysis framework written in Python 3. It runs a suite of vulnerability detectors, prints visual information about contract details, and provides an API to easily write custom analyses. Slither enables developers to find vulnerabilities, enhance their code comphrehension, and quickly prototype custom analyses.

## Features

* Detects vulnerable Solidity code with low false positives
* Identifies where the error condition occurs in the source code
* Easy integration into continuous integration and Truffle builds
* Built-in 'printers' quickly report crucial contract information
* Detector API to write custom analyses in Python
* Ability to analyze contracts written with Solidity >= 0.4
* Intermediate representation ([SlithIR](https://github.com/trailofbits/slither/wiki/SlithIR)) enables simple, high-precision analyses

## Usage

Run Slither on a Truffle application:
```
truffle compile
slither .
```

Run Slither on a single file:
``` 
$ slither tests/uninitialized.sol # argument can be file, folder or glob, be sure to quote the argument when using a glob
[..]
INFO:Detectors:Uninitialized state variables in tests/uninitialized.sol, Contract: Uninitialized, Vars: destination, Used in ['transfer']
[..]
``` 

If Slither is run on a directory, it will run on every `.sol` file in the directory.

###  Configuration

* `--solc SOLC`: Path to `solc` (default 'solc')
* `--solc-args SOLC_ARGS`: Add custom solc arguments. `SOLC_ARGS` can contain multiple arguments
* `--disable-solc-warnings`: Do not print solc warnings
* `--solc-ast`: Use the solc AST file as input (`solc file.sol --ast-json > file.ast.json`)
* `--json FILE`: Export results as JSON

## Detectors

By default, all the detectors are run.

Num | Detector | What it Detects | Impact | Confidence
--- | --- | --- | --- | ---
1 | `suicidal` | [Functions allowing anyone to destruct the contract](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#suicidal) | High | High
2 | `uninitialized-local` | [Uninitialized local variables](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#uninitialized-local-variables) | High | High
3 | `uninitialized-state` | [Uninitialized state variables](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#uninitialized-state-variables) | High | High
4 | `uninitialized-storage` | [Uninitialized storage variables](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#uninitialized-storage-variables) | High | High
5 | `arbitrary-send` | [Functions that send ether to arbitrary destinations](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#functions-that-send-ether-to-arbitrary-destinations) | High | Medium
6 | `controlled-delegatecall` | [Controlled delegatecall function id](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#controlled-delegatecall) | High | Medium
7 | `reentrancy` | [Reentrancy vulnerabilities](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#reentrancy-vulnerabilities) | High | Medium
8 | `locked-ether` | [Contracts that lock ether](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#contracts-that-lock-ether) | Medium | High
9 | `tx-origin` | [Dangerous usage of `tx.origin`](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#dangerous-usage-of-txorigin) | Medium | Medium
10 | `assembly` | [Assembly usage](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#assembly-usage) | Informational | High
11 | `constable-states` | [State variables that could be declared constant](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#state-variables-that-could-be-declared-constant) | Informational | High
12 | `external-function` | [Public function that could be declared as external](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#public-function-that-could-be-declared-as-external) | Informational | High
13 | `low-level-calls` | [Low level calls](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#low-level-calls) | Informational | High
14 | `naming-convention` | [Conformance to Solidity naming conventions](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#conformance-to-solidity-naming-conventions) | Informational | High
15 | `pragma` | [If different pragma directives are used](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#state-variables-that-could-be-declared-constant) | Informational | High
16 | `solc-version` | [Old versions of Solidity (< 0.4.23)](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#old-versions-of-solidity) | Informational | High
17 | `unused-state` | [Unused state variables](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#unused-state-variables) | Informational | High

[Contact us](https://www.trailofbits.com/contact/) to get access to additional detectors.

### Printers

To run a printer, use `--print` and a comma-separated list of printers.

Num | Printer | Description
--- | --- | ---
1 | `call-graph` | Export the call-graph of the contracts to a dot file
2 | `contract-summary` | Print a summary of the contracts
3 | `function-summary` | Print a summary of the functions
4 | `human-summary` | Print a human readable summary of the contracts
5 | `inheritance` | Print the inheritance relations between contracts
6 | `inheritance-graph` | Export the inheritance graph of each contract to a dot file
7 | `slithir` | Print the slithIR representation of the functions
8 | `vars-and-auth` | Print the state variables written and the authorization of the functions

## How to install

Slither requires Python 3.6+ and [solc](https://github.com/ethereum/solidity/), the Solidity compiler.

### Using Pip

```
$ pip install slither-analyzer
```

### Using Git

```bash
$ git clone https://github.com/trailofbits/slither.git && cd slither
$ python setup.py install 
```

## Getting Help

Feel free to stop by our [Slack channel](https://empireslacking.herokuapp.com) (#ethereum) for help using or extending Slither.

* The [Printer documentation](https://github.com/trailofbits/slither/wiki/Printer-documentation) describes the information Slither is capable of visualizing for each contract.

* The [Detector documentation](https://github.com/trailofbits/slither/wiki/Adding-a-new-detector) describes how to write a new vulnerability analyses.

* The [API documentation](https://github.com/trailofbits/slither/wiki/API-examples) describes the methods and objects available for custom analyses.

* The [SlithIR documentation](https://github.com/trailofbits/slither/wiki/SlithIR) describes the SlithIR intermediate representation.

## License

Slither is licensed and distributed under the AGPLv3 license. [Contact us](mailto:opensource@trailofbits.com) if you're looking for an exception to the terms.
