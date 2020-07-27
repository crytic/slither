# Slither, the Solidity source analyzer
<img src="./logo.png" alt="Logo" width="500"/>

[![Build Status](https://img.shields.io/github/workflow/status/crytic/slither/CI/master)](https://github.com/crytic/slither/actions?query=workflow%3ACI)
[![Slack Status](https://empireslacking.herokuapp.com/badge.svg)](https://empireslacking.herokuapp.com)
[![PyPI version](https://badge.fury.io/py/slither-analyzer.svg)](https://badge.fury.io/py/slither-analyzer)

Slither is a Solidity static analysis framework written in Python 3. It runs a suite of vulnerability detectors, prints visual information about contract details, and provides an API to easily write custom analyses. Slither enables developers to find vulnerabilities, enhance their code comprehension, and quickly prototype custom analyses.

- [Features](#features)
- [Bugs and Optimizations Detection](#bugs-and-optimizations-detection)
- [Printers](#printers)
- [Tools](#tools)
- [How to Install](#how-to-install)
- [Getting Help](#getting-help)
- [Publications](#publications)

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
```bash
slither .
```

Run Slither on a single file:
```bash
slither tests/uninitialized.sol
```

For additional configuration, see the [usage](https://github.com/trailofbits/slither/wiki/Usage) documentation.

Use [solc-select](https://github.com/crytic/solc-select) if your contracts require older versions of solc.

### Detectors


Num | Detector | What it Detects | Impact | Confidence
--- | --- | --- | --- | ---
1 | `name-reused` | [Contract's name reused](https://github.com/crytic/slither/wiki/Detector-Documentation#name-reused) | High | High
2 | `rtlo` | [Right-To-Left-Override control character is used](https://github.com/crytic/slither/wiki/Detector-Documentation#right-to-left-override-character) | High | High
3 | `shadowing-state` | [State variables shadowing](https://github.com/crytic/slither/wiki/Detector-Documentation#state-variable-shadowing) | High | High
4 | `suicidal` | [Functions allowing anyone to destruct the contract](https://github.com/crytic/slither/wiki/Detector-Documentation#suicidal) | High | High
5 | `uninitialized-state` | [Uninitialized state variables](https://github.com/crytic/slither/wiki/Detector-Documentation#uninitialized-state-variables) | High | High
6 | `uninitialized-storage` | [Uninitialized storage variables](https://github.com/crytic/slither/wiki/Detector-Documentation#uninitialized-storage-variables) | High | High
7 | `arbitrary-send` | [Functions that send ether to arbitrary destinations](https://github.com/crytic/slither/wiki/Detector-Documentation#functions-that-send-ether-to-arbitrary-destinations) | High | Medium
8 | `controlled-delegatecall` | [Controlled delegatecall destination](https://github.com/crytic/slither/wiki/Detector-Documentation#controlled-delegatecall) | High | Medium
9 | `reentrancy-eth` | [Reentrancy vulnerabilities (theft of ethers)](https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities) | High | Medium
10 | `erc20-interface` | [Incorrect ERC20 interfaces](https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-erc20-interface) | Medium | High
11 | `erc721-interface` | [Incorrect ERC721 interfaces](https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-erc721-interface) | Medium | High
12 | `incorrect-equality` | [Dangerous strict equalities](https://github.com/crytic/slither/wiki/Detector-Documentation#dangerous-strict-equalities) | Medium | High
13 | `locked-ether` | [Contracts that lock ether](https://github.com/crytic/slither/wiki/Detector-Documentation#contracts-that-lock-ether) | Medium | High
14 | `shadowing-abstract` | [State variables shadowing from abstract contracts](https://github.com/crytic/slither/wiki/Detector-Documentation#state-variable-shadowing-from-abstract-contracts) | Medium | High
15 | `tautology` | [Tautology or contradiction](https://github.com/crytic/slither/wiki/Detector-Documentation#tautology-or-contradiction) | Medium | High
16 | `boolean-cst` | [Misuse of Boolean constant](https://github.com/crytic/slither/wiki/Detector-Documentation#misuse-of-a-boolean-constant) | Medium | Medium
17 | `constant-function-asm` | [Constant functions using assembly code](https://github.com/crytic/slither/wiki/Detector-Documentation#constant-functions-using-assembly-code) | Medium | Medium
18 | `constant-function-state` | [Constant functions changing the state](https://github.com/crytic/slither/wiki/Detector-Documentation#constant-functions-changing-the-state) | Medium | Medium
19 | `divide-before-multiply` | [Imprecise arithmetic operations order](https://github.com/crytic/slither/wiki/Detector-Documentation#divide-before-multiply) | Medium | Medium
20 | `reentrancy-no-eth` | [Reentrancy vulnerabilities (no theft of ethers)](https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities-1) | Medium | Medium
21 | `tx-origin` | [Dangerous usage of `tx.origin`](https://github.com/crytic/slither/wiki/Detector-Documentation#dangerous-usage-of-txorigin) | Medium | Medium
22 | `unchecked-lowlevel` | [Unchecked low-level calls](https://github.com/crytic/slither/wiki/Detector-Documentation#unchecked-low-level-calls) | Medium | Medium
23 | `unchecked-send` | [Unchecked send](https://github.com/crytic/slither/wiki/Detector-Documentation#unchecked-send) | Medium | Medium
24 | `uninitialized-local` | [Uninitialized local variables](https://github.com/crytic/slither/wiki/Detector-Documentation#uninitialized-local-variables) | Medium | Medium
25 | `unused-return` | [Unused return values](https://github.com/crytic/slither/wiki/Detector-Documentation#unused-return) | Medium | Medium
26 | `shadowing-builtin` | [Built-in symbol shadowing](https://github.com/crytic/slither/wiki/Detector-Documentation#builtin-symbol-shadowing) | Low | High
27 | `shadowing-local` | [Local variables shadowing](https://github.com/crytic/slither/wiki/Detector-Documentation#local-variable-shadowing) | Low | High
28 | `void-cst` | [Constructor called not implemented](https://github.com/crytic/slither/wiki/Detector-Documentation#void-constructor) | Low | High
29 | `calls-loop` | [Multiple calls in a loop](https://github.com/crytic/slither/wiki/Detector-Documentation/#calls-inside-a-loop) | Low | Medium
30 | `reentrancy-benign` | [Benign reentrancy vulnerabilities](https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities-2) | Low | Medium
31 | `reentrancy-events` | [Reentrancy vulnerabilities leading to out-of-order Events](https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities-3) | Low | Medium
32 | `timestamp` | [Dangerous usage of `block.timestamp`](https://github.com/crytic/slither/wiki/Detector-Documentation#block-timestamp) | Low | Medium
33 | `assembly` | [Assembly usage](https://github.com/crytic/slither/wiki/Detector-Documentation#assembly-usage) | Informational | High
34 | `boolean-equal` | [Comparison to boolean constant](https://github.com/crytic/slither/wiki/Detector-Documentation#boolean-equality) | Informational | High
35 | `deprecated-standards` | [Deprecated Solidity Standards](https://github.com/crytic/slither/wiki/Detector-Documentation#deprecated-standards) | Informational | High
36 | `erc20-indexed` | [Un-indexed ERC20 event parameters](https://github.com/crytic/slither/wiki/Detector-Documentation#unindexed-erc20-event-parameters) | Informational | High
37 | `low-level-calls` | [Low level calls](https://github.com/crytic/slither/wiki/Detector-Documentation#low-level-calls) | Informational | High
38 | `naming-convention` | [Conformance to Solidity naming conventions](https://github.com/crytic/slither/wiki/Detector-Documentation#conformance-to-solidity-naming-conventions) | Informational | High
39 | `pragma` | [If different pragma directives are used](https://github.com/crytic/slither/wiki/Detector-Documentation#different-pragma-directives-are-used) | Informational | High
40 | `solc-version` | [Incorrect Solidity version](https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-versions-of-solidity) | Informational | High
41 | `unused-state` | [Unused state variables](https://github.com/crytic/slither/wiki/Detector-Documentation#unused-state-variables) | Informational | High
42 | `reentrancy-unlimited-gas` | [Reentrancy vulnerabilities through send and transfer](https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities-4) | Informational | Medium
43 | `too-many-digits` | [Conformance to numeric notation best practices](https://github.com/crytic/slither/wiki/Detector-Documentation#too-many-digits) | Informational | Medium
44 | `constable-states` | [State variables that could be declared constant](https://github.com/crytic/slither/wiki/Detector-Documentation#state-variables-that-could-be-declared-constant) | Optimization | High
45 | `external-function` | [Public function that could be declared as external](https://github.com/crytic/slither/wiki/Detector-Documentation#public-function-that-could-be-declared-as-external) | Optimization | High


See the [Detectors Documentation](https://github.com/crytic/slither/wiki/Detector-Documentation) for more information.
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
- `slither-prop`: [Automatic unit tests and properties generation](https://github.com/crytic/slither/wiki/Properties-generation)
- `slither-flat`: [Flatten a codebase](https://github.com/crytic/slither/wiki/Contract-Flattening)
- `slither-erc`: [Check the ERC's conformance](https://github.com/crytic/slither/wiki/ERC-Conformance)
- `slither-format`: [Automatic patches generation](https://github.com/crytic/slither/wiki/Slither-format)

See the [Tool documentation](https://github.com/crytic/slither/wiki/Tool-Documentation) for additional tools.

[Contact us](https://www.trailofbits.com/contact/) to get help on building custom tools.

## How to install

Slither requires Python 3.6+ and [solc](https://github.com/ethereum/solidity/), the Solidity compiler.

### Using Pip

```bash
pip3 install slither-analyzer
```

### Using Git

```bash
git clone https://github.com/crytic/slither.git && cd slither
python3 setup.py install
```

We recommend using an Python virtual environment, as detailed in the [Developer Installation Instructions](https://github.com/trailofbits/slither/wiki/Developer-installation), if you prefer to install Slither via git.

### Using Docker

Use the [`eth-security-toolbox`](https://github.com/trailofbits/eth-security-toolbox/) docker image. It includes all of our security tools and every major version of Solidity in a single image. `/home/share` will be mounted to `/share`  in the container.

```bash
docker pull trailofbits/eth-security-toolbox
```

To share a directory in the container:

```bash
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


## Publications

### Trail of Bits publication
- [Slither: A Static Analysis Framework For Smart Contracts](https://arxiv.org/abs/1908.09878), Josselin Feist, Gustavo Grieco, Alex Groce - WETSEB '19

### External publications
- [ReJection: A AST-Based Reentrancy Vulnerability Detection Method](https://www.researchgate.net/publication/339354823_ReJection_A_AST-Based_Reentrancy_Vulnerability_Detection_Method), Rui Ma, Zefeng Jian, Guangyuan Chen, Ke Ma, Yujia Chen - CTCIS 19
- [MPro: Combining Static and Symbolic Analysis forScalable Testing of Smart Contract](https://arxiv.org/pdf/1911.00570.pdf), William Zhang, Sebastian Banescu, Leodardo Pasos, Steven Stewart, Vijay Ganesh - ISSRE 2019
- [ETHPLOIT: From Fuzzing to Efficient Exploit Generation against Smart Contracts](https://wcventure.github.io/FuzzingPaper/Paper/SANER20_ETHPLOIT.pdf), Qingzhao Zhang, Yizhuo Wang, Juanru Li, Siqi Ma - SANER 20
- [Verification of Ethereum Smart Contracts: A Model Checking Approach](http://www.ijmlc.org/vol10/977-AM0059.pdf), Tam Bang, Hoang H Nguyen, Dung Nguyen, Toan Trieu, Tho Quan - IJMLC 20

If you are using Slither on an academic work, consider applying to the [Crytic $10k Research Prize](https://blog.trailofbits.com/2019/11/13/announcing-the-crytic-10k-research-prize/).
