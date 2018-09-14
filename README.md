# Slither, the Solidity source analyzer
[![Build Status](https://travis-ci.com/trailofbits/slither.svg?token=JEF97dFy1QsDCfQ2Wusd&branch=master)](https://travis-ci.com/trailofbits/slither)

Slither is a Solidity static analysis framework written in Python 3. It provides an API to easily manipulate Solidity code, and integrates vulnerabilities detectors.

# Features
With Slither you can:
- **Detect vulnerabilities**
- **Speed up your understanding** of code
- **Build custom analyses** to answer specific questions
- **Quickly prototype** a new static analysis techniques

Slither can analyze contracts written with Solidity > 0.4.

Some of Slither detectors are open-source, [contact us](https://www.trailofbits.com/contact/) to get access to additional detectors.

# How to install

Slither uses Python 3.6.

## Using Pip

```
$ pip install slither-analyzer
```

## Using Gihtub

```bash
$ git clone https://github.com/trailofbits/slither.git & cd slither
$ python setup.py install 
```

Slither requires [solc](https://github.com/ethereum/solidity/), the Solidity compiler.

# How to use

``` 
$ slither file.sol
``` 

For example:

``` 
$ slither tests/uninitialized.sol
[..]
INFO:Detectors:Uninitialized state variables in tests/uninitialized.sol, Contract: Uninitialized, Vars: destination, Used in ['transfer']
[..]
``` 

If Slither is applied on a directory, it will run on every `.sol` file of the directory.

## Checks available

By default, all the checks are run.

Check | Purpose | Impact | Confidence
--- | --- | --- | ---
`--detect-uninitialized-state`| Detect uninitialized state variables | High | High
`--detect-uninitialized-storage`| Detect uninitialized storage variables | High | High
`--detect-pragma`| Detect if different pragma directives are used | Informational | High
`--detect-reentrancy`| Detect if different pragma directives are used | High | Medium
`--detect-solc-version`| Detect if an old version of Solidity is used (<0.4.23) | Informational | High

## Exclude analyses
* `--exclude-informational`: Exclude informational impact analyses
* `--exclude-low`: Exclude low impact analyses
* `--exclude-medium`: Exclude medium impact analyses
* `--exclude-high`: Exclude high impact analyses
* `--exclude-name` will exclude the detector `name`

##  Configuration
* `--solc SOLC`: Path to `solc` (default 'solc')
* `--solc-args SOLC_ARGS`: Add custom solc arguments. `SOLC_ARGS` can contain multiple arguments.
* `--disable-solc-warnings`: Do not print solc warnings
* `--solc-ast`: Use the solc AST file as input (`solc file.sol --ast-json > file.ast.json`)
* `--json FILE`: Export results as JSON

## Printers
* `--printer-summary`: Print a summary of the contracts
* `--printer-quick-summary`: Print a quick summary of the contracts
* `--printer-inheritance`: Print the inheritance graph
* `--printer-vars-and-auth`: Print the variables written and the check on `msg.sender` of each function.

For more information about printers, see the [Printers documentation](https://github.com/trailofbits/slither/wiki/Printer-documentation)

## How to create analyses

See the [API documentation](https://github.com/trailofbits/slither/wiki/API-examples), and the [detector documentation](https://github.com/trailofbits/slither/wiki/Adding-a-new-detector).


# License

Slither is licensed and distributed under the AGPLv3 license. [Contact us](mailto:opensource@trailofbits.com) if you're looking for an exception to the terms.
