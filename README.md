# Slither, the Solidity source analyzer
[![Build Status](https://travis-ci.com/trailofbits/slither.svg?token=JEF97dFy1QsDCfQ2Wusd&branch=master)](https://travis-ci.com/trailofbits/slither)
[![Slack Status](https://empireslacking.herokuapp.com/badge.svg)](https://empireslacking.herokuapp.com)
[![PyPI version](https://badge.fury.io/py/slither-analyzer.svg)](https://badge.fury.io/py/slither-analyzer)

Slither is a Solidity static analysis framework written in Python 3. It runs a suite of vulnerability detectors, prints visual information about contract details, and provides an API to easily write custom analyses. Slither enables developers to find vulnerabilities, enhance their code comphrehension, and quickly prototype custom analyses.

## Features

* Detects vulnerable Solidity code with low false positives
* Identifies where the error condition occurs in the source code
* Easily integrates into continuous integration and Truffle builds
* Built-in 'printers' quickly report crucial contract information
* Detector API to write custom analyses in Python
* Ability to analyze contracts written with Solidity >= 0.4
* Intermediate representation ([SlithIR](https://github.com/trailofbits/slither/wiki/SlithIR)) enables simple, high-precision analyses
* Correctly parses 99.9% of all public Solidity code
* Average execution time of less than 1 second per contract

## Usage

Run Slither on a Truffle application:
```
slither .
```

Run Slither on a single file:
``` 
$ slither tests/uninitialized.sol 
[..]
INFO:Detectors:
Uninitialized.destination (tests/uninitialized.sol#5) is never initialized. It is used in:
	- transfer (tests/uninitialized.sol#7-9)
Reference: https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#uninitialized-state-variables
[..]
``` 

Slither can be run on:
- A `.sol` file
- A Truffle directory
- A directory containing `*.sol` files (all the `*.sol` files will be analyzed)
- A glob (be sure to quote the argument when using a glob) 

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
1 | `shadowing-state` | [State variables shadowing](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#state-variable-shadowing) | High | High
2 | `suicidal` | [Functions allowing anyone to destruct the contract](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#suicidal) | High | High
3 | `uninitialized-state` | [Uninitialized state variables](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#uninitialized-state-variables) | High | High
4 | `uninitialized-storage` | [Uninitialized storage variables](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#uninitialized-storage-variables) | High | High
5 | `arbitrary-send` | [Functions that send ether to arbitrary destinations](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#functions-that-send-ether-to-arbitrary-destinations) | High | Medium
6 | `controlled-delegatecall` | [Controlled delegatecall destination](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#controlled-delegatecall) | High | Medium
7 | `reentrancy-eth` | [Reentrancy vulnerabilities (theft of ethers)](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#reentrancy-vulnerabilities) | High | Medium
8 | `incorrect-equality` | [Dangerous strict equalities](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#dangerous-strict-equalities) | Medium | High
9 | `locked-ether` | [Contracts that lock ether](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#contracts-that-lock-ether) | Medium | High
10 | `shadowing-abstract` | [State variables shadowing from abstract contracts](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#state-variable-shadowing-from-abstract-contracts) | Medium | High
11 | `constant-function` | [Constant functions changing the state](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#constant-functions-changing-the-state) | Medium | Medium
12 | `reentrancy-no-eth` | [Reentrancy vulnerabilities (no theft of ethers)](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#reentrancy-vulnerabilities-1) | Medium | Medium
13 | `tx-origin` | [Dangerous usage of `tx.origin`](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#dangerous-usage-of-txorigin) | Medium | Medium
14 | `uninitialized-local` | [Uninitialized local variables](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#uninitialized-local-variables) | Medium | Medium
15 | `unused-return` | [Unused return values](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#unused-return) | Medium | Medium
16 | `shadowing-builtin` | [Built-in symbol shadowing](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#builtin-symbol-shadowing) | Low | High
17 | `shadowing-local` | [Local variables shadowing](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#local-variable-shadowing) | Low | High
18 | `calls-loop` | [Multiple calls in a loop](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description/_edit#calls-inside-a-loop) | Low | Medium
19 | `reentrancy-benign` | [Benign reentrancy vulnerabilities](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#reentrancy-vulnerabilities-2) | Low | Medium
20 | `timestamp` | [Dangerous usage of `block.timestamp`](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#block-timestamp) | Low | Medium
21 | `assembly` | [Assembly usage](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#assembly-usage) | Informational | High
22 | `constable-states` | [State variables that could be declared constant](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#state-variables-that-could-be-declared-constant) | Informational | High
23 | `external-function` | [Public function that could be declared as external](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#public-function-that-could-be-declared-as-external) | Informational | High
24 | `low-level-calls` | [Low level calls](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#low-level-calls) | Informational | High
25 | `naming-convention` | [Conformance to Solidity naming conventions](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#conformance-to-solidity-naming-conventions) | Informational | High
26 | `pragma` | [If different pragma directives are used](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#different-pragma-directives-are-used) | Informational | High
27 | `solc-version` | [Incorrect Solidity version (< 0.4.24 or complex pragma)](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#incorrect-version-of-solidity) | Informational | High
28 | `unused-state` | [Unused state variables](https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#unused-state-variables) | Informational | High

[Contact us](https://www.trailofbits.com/contact/) to get access to additional detectors.

### Printers

To run a printer, use `--print` and a comma-separated list of printers.

Num | Printer | Description
--- | --- | ---
1 | `call-graph` | Export the call-graph of the contracts to a dot file
2 | `cfg` | Export the CFG of each functions
3 | `contract-summary` | Print a summary of the contracts
4 | `function-id` | Print the keccack256 signature of the functions
5 | `function-summary` | Print a summary of the functions
6 | `human-summary` | Print a human-readable summary of the contracts
7 | `inheritance` | Print the inheritance relations between contracts
8 | `inheritance-graph` | Export the inheritance graph of each contract to a dot file
9 | `slithir` | Print the slithIR representation of the functions
10 | `slithir-ssa` | Print the slithIR representation of the functions
11 | `variables-order` | Print the storage order of the state variables
12 | `vars-and-auth` | Print the state variables written and the authorization of the functions

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

We recommend using an Python virtual environment, as detailed in the [Developer Installation Instructions](https://github.com/trailofbits/slither/wiki/Developer-installation), if you prefer to install Slither via git.

### Using Docker

Use the [`eth-security-toolbox`](https://github.com/trailofbits/eth-security-toolbox/) docker image. It includes all of our security tools and every major version of Solidity in a single image. `/home/share` will be mounted to `/share`  in the container. Use [`solc-select`](https://github.com/trailofbits/eth-security-toolbox/#usage) to switch the Solidity version.

```
docker pull trailofbits/eth-security-toolbox
```

To share a directory in the container:

```
docker run -it -v /home/share:/share trailofbits/eth-security-toolbox
```

## Getting Help

Feel free to stop by our [Slack channel](https://empireslacking.herokuapp.com) (#ethereum) for help using or extending Slither.

* The [Printer documentation](https://github.com/trailofbits/slither/wiki/Printer-documentation) describes the information Slither is capable of visualizing for each contract.

* The [Detector documentation](https://github.com/trailofbits/slither/wiki/Adding-a-new-detector) describes how to write a new vulnerability analyses.

* The [API documentation](https://github.com/trailofbits/slither/wiki/API-examples) describes the methods and objects available for custom analyses.

* The [SlithIR documentation](https://github.com/trailofbits/slither/wiki/SlithIR) describes the SlithIR intermediate representation.

## License

Slither is licensed and distributed under the AGPLv3 license. [Contact us](mailto:opensource@trailofbits.com) if you're looking for an exception to the terms.
