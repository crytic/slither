# Slither, the Solidity source analyzer
[![Build Status](https://travis-ci.com/trailofbits/slither.svg?token=JEF97dFy1QsDCfQ2Wusd&branch=master)](https://travis-ci.com/trailofbits/slither)
[![Slack Status](https://empireslacking.herokuapp.com/badge.svg)](https://empireslacking.herokuapp.com)

Slither is a Solidity static analysis framework written in Python 3. It runs a suite of vulnerability detectors, prints visual information about contract details, and provides an API to easily write custom analyses. Slither enables developers to find vulnerabilities, enhance their code comphrehension, and quickly prototype custom analyses.

## Features

* Detects vulnerable Solidity code with low false positives
* Identifies where the error condition occurs in the source code
* Easy integration into continuous integration pipelines
* Built-in 'printers' quickly report crucial contract information
* Detector API to write custom analyses in Python
* Ability to analyze contracts written with Solidity >= 0.4
* Intermediate representation ([SlithIR](https://github.com/trailofbits/slither/wiki/SlithIR)) enables simple, high-precision analyses

## Usage

``` 
$ slither tests/uninitialized.sol
[..]
INFO:Detectors:Uninitialized state variables in tests/uninitialized.sol, Contract: Uninitialized, Vars: destination, Used in ['transfer']
[..]
``` 

If Slither is run on a directory, it will run on every `.sol` file of the directory. All vulnerability checks are run by default.

###  Configuration

* `--solc SOLC`: Path to `solc` (default 'solc')
* `--solc-args SOLC_ARGS`: Add custom solc arguments. `SOLC_ARGS` can contain multiple arguments
* `--disable-solc-warnings`: Do not print solc warnings
* `--solc-ast`: Use the solc AST file as input (`solc file.sol --ast-json > file.ast.json`)
* `--json FILE`: Export results as JSON
* `--exclude-name`: Excludes the detector `name` from analysis

### Printers

* `--printer-summary`: Print a summary of the contracts
* `--printer-quick-summary`: Print a quick summary of the contracts
* `--printer-inheritance`: Print the inheritance relations
* `--printer-inheritance-graph`: Print the inheritance graph in a file
* `--printer-vars-and-auth`: Print the variables written and the check on `msg.sender` of each function

## Checks available

By default, all the checks are run. Use --detect-_name-of-check_ to run one check at a time.

Num | Check | What it Detects | Impact | Confidence
--- | --- | --- | --- | ---
1 | `suicidal` | Suicidal functions | High | High
2 | `uninitialized-state` | Uninitialized state variables | High | High
3 | `uninitialized-storage` | Uninitialized storage variables | High | High
4 | `arbitrary-send` | Functions that send ether to an arbitrary destination | High | Medium
5 | `reentrancy` | Reentrancy vulnerabilities | High | Medium
6 | `locked-ether` | Contracts that lock ether | Medium | High
7 | `tx-origin` | Dangerous usage of `tx.origin` | Medium | Medium
8 | `assembly` | Assembly usage | Informational | High
9 | `const-candidates-state` | State variables that could be declared constant | Informational | High
10 | `low-level-calls` | Low level calls | Informational | High
11 | `naming-convention` | Conformance to Solidity naming conventions | Informational | High
12 | `pragma` | If different pragma directives are used | Informational | High
13 | `solc-version` | If an old version of Solidity used (<0.4.23) | Informational | High
14 | `unused-state` | Unused state variables | Informational | High

[Contact us](https://www.trailofbits.com/contact/) to get access to additional detectors.

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
