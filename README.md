# Slither, the Solidity source analyzer
[![Build Status](https://travis-ci.com/trailofbits/slither.svg?token=JEF97dFy1QsDCfQ2Wusd&branch=master)](https://travis-ci.com/trailofbits/slither)

Slither is a Solidity static analysis framework. It provides an API to easily manipulate Solidity code. In addition to exposing a Solidity contracts AST, Slither provides many APIs to quickly check local and state variable usage.

With Slither you can:
- Detect vulnerabilities
- Speed up your understanding of code
- Build custom analyses to answer specific questions
- Quickly prototype a new static analysis techniques

## How to install

Use pip to install the dependencies:

```bash
$ sudo -H pip install -U -r requirements.txt
```

You may also want solc, which can be installed using homebrew:

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
$ slither.py file.sol
``` 

``` 
$ slither.py examples/uninitialized.sol
[..]
INFO:Detectors:Uninitialized state variables in examples/uninitialized.sol, Contract: Uninitialized, Vars: destination, Used in ['transfer']
[..]
``` 

If Slither is applied on a directory, it will run on every `.sol` file of the directory.

## Options

### Configuration
* `--solc SOLC`: Path to `solc` (default 'solc')
* `--disable-solc-warnings`: Do not print solc warnings
* `--solc-ast`: Use the solc AST file as input (`solc file.sol --ast-json > file.ast.json`)
* `--json FILE`: Export results as JSON
* `--solc-args SOLC_ARGS`: Add custom solc arguments. `SOLC_ARGS` can contain multiple arguments.

### Analyses
* `--high`: Run only medium/high severity checks with high confidence
* `--medium`: Run only medium/high severity checks with medium confidence
* `--low`: Run only low severity checks

### Printers
* `--print-summary`: Print a summary of the contracts
* `--print-quick-summary`: Print a quick summary of the contracts
* `--print-inheritance`: Print the inheritance graph

For more information about printers, see the [Printers documentation](docs/PRINTERS.md)

## Checks available

Check | Purpose | Severity | Confidence
--- | --- | --- | ---
`--uninitialized`| Detect uninitialized variables | High | High


## License

Slither is licensed and distributed under AGPLv3. [Contact us](mailto:opensource@trailofbits.com) if you're looking for an exception to the terms.
