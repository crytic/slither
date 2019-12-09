# Slither, the Solidity source analyzer
<img src="./logo.png" alt="Logo" width="500"/>

[![Build Status](https://img.shields.io/github/workflow/status/crytic/slither/CI/master)](https://github.com/crytic/slither/actions)
[![Slack Status](https://empireslacking.herokuapp.com/badge.svg)](https://empireslacking.herokuapp.com)
[![PyPI version](https://badge.fury.io/py/slither-analyzer.svg)](https://badge.fury.io/py/slither-analyzer)

Slither is a Solidity static analysis framework written in Python 3. It runs a suite of vulnerability detectors, prints visual information about contract details, and provides an API to easily write custom analyses. Slither enables developers to find vulnerabilities, enhance their code comprehension, and quickly prototype custom analyses.

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


## Bugs and Optimizations Detection

Run Slither on a Truffle/Embark/Dapp/Etherlime application:
```
slither .
```

Run Slither on a single file:
```
$ slither tests/uninitialized.sol
```

For additional configuration, see the [usage](https://github.com/trailofbits/slither/wiki/Usage) documentation.

Use [solc-select](https://github.com/crytic/solc-select) if your contracts require older versions of solc.

### Detectors

Slither has more than 30 public detectors, including:
- `shadowing-state`: [State variables shadowing](https://github.com/crytic/slither/wiki/Detector-Documentation#state-variable-shadowing)
- `reentrancy-eth`: [Reentrancy vulnerabilities](https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities)
- `erc20-interface`: [Incorrect ERC20 interfaces](https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-erc20-interface)
- `incorrect-equality`: [Dangerous strict equalities](https://github.com/crytic/slither/wiki/Detector-Documentation#dangerous-strict-equalities)
- `constable-states`: [State variables that could be declared constant](https://github.com/crytic/slither/wiki/Detector-Documentation#state-variables-that-could-be-declared-constant)

See the [Detectors Documentation](https://github.com/crytic/slither/wiki/Detector-Documentation) for the complete list.
By default, all the detectors are run.

Check out [Crytic](https://crytic.io/) to get access to additional Slither's detectors and GitHub integration.

## Printers

### Quick Review Printers
- `human-summary`: [Print a human-readable summary of the contracts](https://github.com/trailofbits/slither/wiki/Printer-documentation#human-summary)
- `inheritance-graph`: [Export the inheritance graph of each contract to a dot file](https://github.com/trailofbits/slither/wiki/Printer-documentation#inheritance-graph)
- `contract-summary`: [Print a summary of the contracts](https://github.com/trailofbits/slither/wiki/Printer-documentation#contract-summary)

### In-Depth Review Printers
- `call-graph`: [Export the call-graph of the contracts to a dot file](https://github.com/trailofbits/slither/wiki/Printer-documentation#call-graph)
- `cfg`: [Export the CFG of each functions](https://github.com/trailofbits/slither/wiki/Printer-documentation#cfg)
- `function-summary`: [Print a summary of the functions](https://github.com/trailofbits/slither/wiki/Printer-documentation#function-summary)
- `vars-and-auth`: [Print the state variables written and the authorization of the functions](https://github.com/crytic/slither/wiki/Printer-documentation#variables-written-and-authorization)

To run a printer, use `--print` and a comma-separated list of printers.

See the [Printer documentation](https://github.com/crytic/slither/wiki/Printer-documentation) for the complete lists.

## Tools

- `slither-check-upgradeability`: [Review `delegatecall`-based upgradeability](https://github.com/crytic/slither/wiki/Upgradeability-Checks)
- `slither-flat`: [Flatten a codebase](https://github.com/crytic/slither/wiki/Contract-Flattening)
- `slither-erc`: [Check the ERC's conformance](https://github.com/crytic/slither/wiki/ERC-Conformance)
- `slither-format`: [Automatic patches generation](https://github.com/crytic/slither/wiki/Slither-format)

See the [Tool documentation](https://github.com/crytic/slither/wiki/Tool-Documentation) for additional tools.

[Contact us](https://www.trailofbits.com/contact/) to get help on building custom tools.

## How to install

Slither requires Python 3.6+ and [solc](https://github.com/ethereum/solidity/), the Solidity compiler.

### Using Pip

```
$ pip3 install slither-analyzer
```

### Using Git

```bash
$ git clone https://github.com/crytic/slither.git && cd slither
$ python3 setup.py install
```

We recommend using an Python virtual environment, as detailed in the [Developer Installation Instructions](https://github.com/trailofbits/slither/wiki/Developer-installation), if you prefer to install Slither via git.

### Using Docker

Use the [`eth-security-toolbox`](https://github.com/trailofbits/eth-security-toolbox/) docker image. It includes all of our security tools and every major version of Solidity in a single image. `/home/share` will be mounted to `/share`  in the container.

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


## Publication
- [Slither: A Static Analysis Framework For Smart Contracts](https://arxiv.org/abs/1908.09878), Josselin Feist, Gustavo Grieco, Alex Groce - WETSEB '19

If you are using Slither on an academic work, consider applying to the [Crytic $10k Research Prize](https://blog.trailofbits.com/2019/11/13/announcing-the-crytic-10k-research-prize/).
