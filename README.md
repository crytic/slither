# Slither, the Solidity source analyzer
[![Build Status](https://travis-ci.com/trailofbits/slither.svg?token=JEF97dFy1QsDCfQ2Wusd&branch=master)](https://travis-ci.com/trailofbits/slither)
[![Slack Status](https://empireslacking.herokuapp.com/badge.svg)](https://empireslacking.herokuapp.com)

Slither is a Solidity static analysis framework written in Python 3. It runs a suite of vulnerability detectors, prints visual information about contract details, and provides an API to easily write custom analyses. Slither enables developers to find vulnerabilities, enhance their code comphrehension, and quickly prototype custom analyses.

## Features

* Detects vulnerable Solidity code with low false positives
  * Detection of most major smart contract vulnerabilities
  * Detection of poor coding practices
* Identifies where the error condition occurs in the source code
* Easy integration into continuous integration pipelines
* Four built-in 'printers' quickly report crucial contract information
* Detector API to write custom analyses in Python
* Ability to analyze contracts written with Solidity > 0.4

Support for advanced value- and taint-tracking is [coming soon](https://github.com/trailofbits/slither/issues/6)!

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
* `--printer-inheritance`: Print the inheritance graph
* `--printer-vars-and-auth`: Print the variables written and the check on `msg.sender` of each function

## Checks available

By default, all the checks are run.

Check | Purpose | Impact | Confidence
--- | --- | --- | ---
`--detect-reentrancy`| Detect reentrancy vulnerabilities | High | Medium
`--detect-suicidal`| Detect suicidal functions | High | High
`--detect-uninitialized-state`| Detect uninitialized state variables | High | High
`--detect-uninitialized-storage`| Detect uninitialized storage variables | High | High
`--detect-locked-ether`| Detect contracts with a payable function that do not send ether | Medium | High
`--detect-tx-origin`| Detect dangerous usage of `tx.origin` | Medium | Medium
`--detect-pragma`| Detect if different pragma directives are used | Informational | High
`--detect-solc-version`| Detect if an old version of Solidity used (<0.4.23) | Informational | High
`--detect-unused-state`| Detect unused state variables | Informational | High



[Contact us](https://www.trailofbits.com/contact/) to get access to additional detectors.

## How to install

Slither requires Python 3.6+ and [solc](https://github.com/ethereum/solidity/), the Solidity compiler.
<!--- 
## Using Pip

```
$ pip install slither-analyzer
```

or
-->

```bash
$ git clone https://github.com/trailofbits/slither.git & cd slither
$ python setup.py install 
```

## Getting Help

Feel free to stop by our [Slack channel](https://empirehacking.slack.com/messages/C7KKY517H/) for help using or extending Slither.

* The [Printer documentation](https://github.com/trailofbits/slither/wiki/Printer-documentation) describes the information Slither is capable of visualizing for each contract.

* The [Detector documentation](https://github.com/trailofbits/slither/wiki/Adding-a-new-detector) describes how to write a new vulnerability analyses.

* The [API documentation](https://github.com/trailofbits/slither/wiki/API-examples) describes the methods and objects available for custom analyses.

## License

Slither is licensed and distributed under the AGPLv3 license. [Contact us](mailto:opensource@trailofbits.com) if you're looking for an exception to the terms.
