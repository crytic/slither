# Slither, the Solidity source analyzer
[![Build Status](https://travis-ci.com/trailofbits/slither.svg?token=JEF97dFy1QsDCfQ2Wusd&branch=master)](https://travis-ci.com/trailofbits/slither)

Slither is a Solidity static analysis framework written in Python 3. It provides an API to easily manipulate Solidity code. In addition to exposing a Solidity contracts AST, Slither provides many APIs to quickly check local and state variable usage.

With Slither you can:
- Detect vulnerabilities
- Speed up your understanding of code
- Build custom analyses to answer specific questions
- Quickly prototype a new static analysis techniques

## How to install

Slither uses Python 3.6.


```bash
$ python setup.py install
```

You may also want solc, the Solidity compiler, which can be installed using homebrew:

```bash
$ brew update
$ brew upgrade
$ brew tap ethereum/ethereum
$ brew install solidity
$ brew linkapps solidity
```

or with aptitude:

```bash
$ sudo add-apt-repository ppa:ethereum/ethereum
$ sudo apt-get update
$ sudo apt-get install solc
```

## How to use

``` 
$ slither file.sol
``` 

``` 
$ slither examples/bugs/uninitialized.sol
[..]
INFO:Detectors:Uninitialized state variables in examples/bugs/uninitialized.sol, Contract: Uninitialized, Vars: destination, Used in ['transfer']
[..]
``` 

If Slither is applied on a directory, it will run on every `.sol` file of the directory.

## Checks available

By default, all the checks are run.

Check | Purpose | Impact | Confidence | Prioritization
--- | --- | --- | --- | ---
`--detect-uninitialized`| Detect uninitialized variables | High | High | High
`--detect-pragma`| Detect if different pragma directives are used | Informational | High | Informational
`--detect-reentrancy`| Detect if different pragma directives are used | High | Medium | Medium
`--detect-solc-version`| Detect if an old version of Solidity is used (<0.4.23) | Informational | High | Informational

A high prioritization check is likely to be a true positive with a severe impact.

### Exclude analyses
* `--exclude-informational`: Exclude informational prioritization analyses
* `--exclude-low`: Exclude low prioritization analyses
* `--exclude-medium`: Exclude medium prioritization impact analyses
* `--exclude-high`: Exclude high impact prioritization analyses
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

For more information about printers, see the [Printers documentation](docs/PRINTERS.md)


## License

Slither is licensed and distributed under the AGPLv3 license. [Contact us](mailto:opensource@trailofbits.com) if you're looking for an exception to the terms.
