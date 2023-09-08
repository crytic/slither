# Slither, the Solidity source analyzer

<img src="https://raw.githubusercontent.com/crytic/slither/master/logo.png" alt="Logo" width="500"/>

[![Build Status](https://img.shields.io/github/actions/workflow/status/crytic/slither/ci.yml?branch=master)](https://github.com/crytic/slither/actions?query=workflow%3ACI)
[![Slack Status](https://empireslacking.herokuapp.com/badge.svg)](https://empireslacking.herokuapp.com)
[![PyPI version](https://badge.fury.io/py/slither-analyzer.svg)](https://badge.fury.io/py/slither-analyzer)

Slither is a Solidity static analysis framework written in Python3. It runs a suite of vulnerability detectors, prints visual information about contract details, and provides an API to easily write custom analyses. Slither enables developers to find vulnerabilities, enhance their code comprehension, and quickly prototype custom analyses.

- [Features](#features)
- [Usage](#usage)
- [How to Install](#how-to-install)
- [Detectors](#detectors)
- [Printers](#printers)
- [Tools](#tools)
- [API Documentation](#api-documentation)
- [Getting Help](#getting-help)
- [FAQ](#faq)
- [Publications](#publications)

## Features

- Detects vulnerable Solidity code with low false positives (see the list of [trophies](./trophies.md))
- Identifies where the error condition occurs in the source code
- Easily integrates into continuous integration and Hardhat/Foundry builds
- Built-in 'printers' quickly report crucial contract information
- Detector API to write custom analyses in Python
- Ability to analyze contracts written with Solidity >= 0.4
- Intermediate representation ([SlithIR](https://github.com/trailofbits/slither/wiki/SlithIR)) enables simple, high-precision analyses
- Correctly parses 99.9% of all public Solidity code
- Average execution time of less than 1 second per contract
- Integrates with Github's code scanning in [CI](https://github.com/marketplace/actions/slither-action)

## Usage

Run Slither on a Hardhat/Foundry/Dapp/Brownie application:

```bash
slither .
```

This is the preferred option if your project has dependencies as Slither relies on the underlying compilation framework to compile source code.

However, you can run Slither on a single file that does not import dependencies:

```bash
slither tests/uninitialized.sol
```

## How to install

Slither requires Python 3.8+.
If you're **not** going to use one of the [supported compilation frameworks](https://github.com/crytic/crytic-compile), you need [solc](https://github.com/ethereum/solidity/), the Solidity compiler; we recommend using [solc-select](https://github.com/crytic/solc-select) to conveniently switch between solc versions.

### Using Pip

```bash
pip3 install slither-analyzer
```

### Using Git

```bash
git clone https://github.com/crytic/slither.git && cd slither
python3 setup.py install
```

We recommend using a Python virtual environment, as detailed in the [Developer Installation Instructions](https://github.com/trailofbits/slither/wiki/Developer-installation), if you prefer to install Slither via git.

### Using Docker

Use the [`eth-security-toolbox`](https://github.com/trailofbits/eth-security-toolbox/) docker image. It includes all of our security tools and every major version of Solidity in a single image. `/home/share` will be mounted to `/share` in the container.

```bash
docker pull trailofbits/eth-security-toolbox
```

To share a directory in the container:

```bash
docker run -it -v /home/share:/share trailofbits/eth-security-toolbox
```

### Integration

- For GitHub action integration, use [slither-action](https://github.com/marketplace/actions/slither-action).
- To generate a Markdown report, use `slither [target] --checklist`.
- To generate a Markdown with GitHub source code highlighting, use `slither [target] --checklist --markdown-root https://github.com/ORG/REPO/blob/COMMIT/` (replace `ORG`, `REPO`, `COMMIT`)

## Detectors

Num | Detector | What it Detects | Impact | Confidence
--- | --- | --- | --- | ---
1 | `abiencoderv2-array` | [Storage abiencoderv2 array](https://github.com/crytic/slither/wiki/Detector-Documentation#storage-abiencoderv2-array) | High | High
2 | `arbitrary-send-erc20` | [transferFrom uses arbitrary `from`](https://github.com/crytic/slither/wiki/Detector-Documentation#arbitrary-from-in-transferfrom) | High | High
3 | `array-by-reference` | [Modifying storage array by value](https://github.com/crytic/slither/wiki/Detector-Documentation#modifying-storage-array-by-value) | High | High
4 | `encode-packed-collision` | [ABI encodePacked Collision](https://github.com/crytic/slither/wiki/Detector-Documentation#abi-encodePacked-collision) | High | High
5 | `incorrect-shift` | [The order of parameters in a shift instruction is incorrect.](https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-shift-in-assembly) | High | High
6 | `multiple-constructors` | [Multiple constructor schemes](https://github.com/crytic/slither/wiki/Detector-Documentation#multiple-constructor-schemes) | High | High
7 | `name-reused` | [Contract's name reused](https://github.com/crytic/slither/wiki/Detector-Documentation#name-reused) | High | High
8 | `protected-vars` | [Detected unprotected variables](https://github.com/crytic/slither/wiki/Detector-Documentation#protected-variables) | High | High
9 | `public-mappings-nested` | [Public mappings with nested variables](https://github.com/crytic/slither/wiki/Detector-Documentation#public-mappings-with-nested-variables) | High | High
10 | `rtlo` | [Right-To-Left-Override control character is used](https://github.com/crytic/slither/wiki/Detector-Documentation#right-to-left-override-character) | High | High
11 | `shadowing-state` | [State variables shadowing](https://github.com/crytic/slither/wiki/Detector-Documentation#state-variable-shadowing) | High | High
12 | `suicidal` | [Functions allowing anyone to destruct the contract](https://github.com/crytic/slither/wiki/Detector-Documentation#suicidal) | High | High
13 | `uninitialized-state` | [Uninitialized state variables](https://github.com/crytic/slither/wiki/Detector-Documentation#uninitialized-state-variables) | High | High
14 | `uninitialized-storage` | [Uninitialized storage variables](https://github.com/crytic/slither/wiki/Detector-Documentation#uninitialized-storage-variables) | High | High
15 | `unprotected-upgrade` | [Unprotected upgradeable contract](https://github.com/crytic/slither/wiki/Detector-Documentation#unprotected-upgradeable-contract) | High | High
16 | `codex` | [Use Codex to find vulnerabilities.](https://github.com/crytic/slither/wiki/Detector-Documentation#codex) | High | Low
17 | `arbitrary-send-erc20-permit` | [transferFrom uses arbitrary from with permit](https://github.com/crytic/slither/wiki/Detector-Documentation#arbitrary-from-in-transferfrom-used-with-permit) | High | Medium
18 | `arbitrary-send-eth` | [Functions that send Ether to arbitrary destinations](https://github.com/crytic/slither/wiki/Detector-Documentation#functions-that-send-ether-to-arbitrary-destinations) | High | Medium
19 | `controlled-array-length` | [Tainted array length assignment](https://github.com/crytic/slither/wiki/Detector-Documentation#array-length-assignment) | High | Medium
20 | `controlled-delegatecall` | [Controlled delegatecall destination](https://github.com/crytic/slither/wiki/Detector-Documentation#controlled-delegatecall) | High | Medium
21 | `delegatecall-loop` | [Payable functions using `delegatecall` inside a loop](https://github.com/crytic/slither/wiki/Detector-Documentation/#payable-functions-using-delegatecall-inside-a-loop) | High | Medium
22 | `msg-value-loop` | [msg.value inside a loop](https://github.com/crytic/slither/wiki/Detector-Documentation/#msgvalue-inside-a-loop) | High | Medium
23 | `reentrancy-eth` | [Reentrancy vulnerabilities (theft of ethers)](https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities) | High | Medium
24 | `storage-array` | [Signed storage integer array compiler bug](https://github.com/crytic/slither/wiki/Detector-Documentation#storage-signed-integer-array) | High | Medium
25 | `unchecked-transfer` | [Unchecked tokens transfer](https://github.com/crytic/slither/wiki/Detector-Documentation#unchecked-transfer) | High | Medium
26 | `weak-prng` | [Weak PRNG](https://github.com/crytic/slither/wiki/Detector-Documentation#weak-PRNG) | High | Medium
27 | `domain-separator-collision` | [Detects ERC20 tokens that have a function whose signature collides with EIP-2612's DOMAIN_SEPARATOR()](https://github.com/crytic/slither/wiki/Detector-Documentation#domain-separator-collision) | Medium | High
28 | `enum-conversion` | [Detect dangerous enum conversion](https://github.com/crytic/slither/wiki/Detector-Documentation#dangerous-enum-conversion) | Medium | High
29 | `erc20-interface` | [Incorrect ERC20 interfaces](https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-erc20-interface) | Medium | High
30 | `erc721-interface` | [Incorrect ERC721 interfaces](https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-erc721-interface) | Medium | High
31 | `incorrect-equality` | [Dangerous strict equalities](https://github.com/crytic/slither/wiki/Detector-Documentation#dangerous-strict-equalities) | Medium | High
32 | `locked-ether` | [Contracts that lock ether](https://github.com/crytic/slither/wiki/Detector-Documentation#contracts-that-lock-ether) | Medium | High
33 | `mapping-deletion` | [Deletion on mapping containing a structure](https://github.com/crytic/slither/wiki/Detector-Documentation#deletion-on-mapping-containing-a-structure) | Medium | High
34 | `shadowing-abstract` | [State variables shadowing from abstract contracts](https://github.com/crytic/slither/wiki/Detector-Documentation#state-variable-shadowing-from-abstract-contracts) | Medium | High
35 | `tautology` | [Tautology or contradiction](https://github.com/crytic/slither/wiki/Detector-Documentation#tautology-or-contradiction) | Medium | High
36 | `write-after-write` | [Unused write](https://github.com/crytic/slither/wiki/Detector-Documentation#write-after-write) | Medium | High
37 | `boolean-cst` | [Misuse of Boolean constant](https://github.com/crytic/slither/wiki/Detector-Documentation#misuse-of-a-boolean-constant) | Medium | Medium
38 | `constant-function-asm` | [Constant functions using assembly code](https://github.com/crytic/slither/wiki/Detector-Documentation#constant-functions-using-assembly-code) | Medium | Medium
39 | `constant-function-state` | [Constant functions changing the state](https://github.com/crytic/slither/wiki/Detector-Documentation#constant-functions-changing-the-state) | Medium | Medium
40 | `divide-before-multiply` | [Imprecise arithmetic operations order](https://github.com/crytic/slither/wiki/Detector-Documentation#divide-before-multiply) | Medium | Medium
41 | `reentrancy-no-eth` | [Reentrancy vulnerabilities (no theft of ethers)](https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities-1) | Medium | Medium
42 | `reused-constructor` | [Reused base constructor](https://github.com/crytic/slither/wiki/Detector-Documentation#reused-base-constructors) | Medium | Medium
43 | `tx-origin` | [Dangerous usage of `tx.origin`](https://github.com/crytic/slither/wiki/Detector-Documentation#dangerous-usage-of-txorigin) | Medium | Medium
44 | `unchecked-lowlevel` | [Unchecked low-level calls](https://github.com/crytic/slither/wiki/Detector-Documentation#unchecked-low-level-calls) | Medium | Medium
45 | `unchecked-send` | [Unchecked send](https://github.com/crytic/slither/wiki/Detector-Documentation#unchecked-send) | Medium | Medium
46 | `uninitialized-local` | [Uninitialized local variables](https://github.com/crytic/slither/wiki/Detector-Documentation#uninitialized-local-variables) | Medium | Medium
47 | `unused-return` | [Unused return values](https://github.com/crytic/slither/wiki/Detector-Documentation#unused-return) | Medium | Medium
48 | `incorrect-modifier` | [Modifiers that can return the default value](https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-modifier) | Low | High
49 | `shadowing-builtin` | [Built-in symbol shadowing](https://github.com/crytic/slither/wiki/Detector-Documentation#builtin-symbol-shadowing) | Low | High
50 | `shadowing-local` | [Local variables shadowing](https://github.com/crytic/slither/wiki/Detector-Documentation#local-variable-shadowing) | Low | High
51 | `uninitialized-fptr-cst` | [Uninitialized function pointer calls in constructors](https://github.com/crytic/slither/wiki/Detector-Documentation#uninitialized-function-pointers-in-constructors) | Low | High
52 | `variable-scope` | [Local variables used prior their declaration](https://github.com/crytic/slither/wiki/Detector-Documentation#pre-declaration-usage-of-local-variables) | Low | High
53 | `void-cst` | [Constructor called not implemented](https://github.com/crytic/slither/wiki/Detector-Documentation#void-constructor) | Low | High
54 | `calls-loop` | [Multiple calls in a loop](https://github.com/crytic/slither/wiki/Detector-Documentation/#calls-inside-a-loop) | Low | Medium
55 | `events-access` | [Missing Events Access Control](https://github.com/crytic/slither/wiki/Detector-Documentation#missing-events-access-control) | Low | Medium
56 | `events-maths` | [Missing Events Arithmetic](https://github.com/crytic/slither/wiki/Detector-Documentation#missing-events-arithmetic) | Low | Medium
57 | `incorrect-unary` | [Dangerous unary expressions](https://github.com/crytic/slither/wiki/Detector-Documentation#dangerous-unary-expressions) | Low | Medium
58 | `missing-zero-check` | [Missing Zero Address Validation](https://github.com/crytic/slither/wiki/Detector-Documentation#missing-zero-address-validation) | Low | Medium
59 | `reentrancy-benign` | [Benign reentrancy vulnerabilities](https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities-2) | Low | Medium
60 | `reentrancy-events` | [Reentrancy vulnerabilities leading to out-of-order Events](https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities-3) | Low | Medium
61 | `timestamp` | [Dangerous usage of `block.timestamp`](https://github.com/crytic/slither/wiki/Detector-Documentation#block-timestamp) | Low | Medium
62 | `assembly` | [Assembly usage](https://github.com/crytic/slither/wiki/Detector-Documentation#assembly-usage) | Informational | High
63 | `assert-state-change` | [Assert state change](https://github.com/crytic/slither/wiki/Detector-Documentation#assert-state-change) | Informational | High
64 | `boolean-equal` | [Comparison to boolean constant](https://github.com/crytic/slither/wiki/Detector-Documentation#boolean-equality) | Informational | High
65 | `cyclomatic-complexity` | [Detects functions with high (> 11) cyclomatic complexity](https://github.com/crytic/slither/wiki/Detector-Documentation#cyclomatic-complexity) | Informational | High
66 | `deprecated-standards` | [Deprecated Solidity Standards](https://github.com/crytic/slither/wiki/Detector-Documentation#deprecated-standards) | Informational | High
67 | `erc20-indexed` | [Un-indexed ERC20 event parameters](https://github.com/crytic/slither/wiki/Detector-Documentation#unindexed-erc20-event-parameters) | Informational | High
68 | `function-init-state` | [Function initializing state variables](https://github.com/crytic/slither/wiki/Detector-Documentation#function-initializing-state) | Informational | High
69 | `incorrect-using-for` | [Detects using-for statement usage when no function from a given library matches a given type](https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-using-for-usage) | Informational | High
70 | `low-level-calls` | [Low level calls](https://github.com/crytic/slither/wiki/Detector-Documentation#low-level-calls) | Informational | High
71 | `missing-inheritance` | [Missing inheritance](https://github.com/crytic/slither/wiki/Detector-Documentation#missing-inheritance) | Informational | High
72 | `naming-convention` | [Conformity to Solidity naming conventions](https://github.com/crytic/slither/wiki/Detector-Documentation#conformance-to-solidity-naming-conventions) | Informational | High
73 | `pragma` | [If different pragma directives are used](https://github.com/crytic/slither/wiki/Detector-Documentation#different-pragma-directives-are-used) | Informational | High
74 | `redundant-statements` | [Redundant statements](https://github.com/crytic/slither/wiki/Detector-Documentation#redundant-statements) | Informational | High
75 | `solc-version` | [Incorrect Solidity version](https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-versions-of-solidity) | Informational | High
76 | `unimplemented-functions` | [Unimplemented functions](https://github.com/crytic/slither/wiki/Detector-Documentation#unimplemented-functions) | Informational | High
77 | `unused-state` | [Unused state variables](https://github.com/crytic/slither/wiki/Detector-Documentation#unused-state-variable) | Informational | High
78 | `costly-loop` | [Costly operations in a loop](https://github.com/crytic/slither/wiki/Detector-Documentation#costly-operations-inside-a-loop) | Informational | Medium
79 | `dead-code` | [Functions that are not used](https://github.com/crytic/slither/wiki/Detector-Documentation#dead-code) | Informational | Medium
80 | `reentrancy-unlimited-gas` | [Reentrancy vulnerabilities through send and transfer](https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities-4) | Informational | Medium
81 | `similar-names` | [Variable names are too similar](https://github.com/crytic/slither/wiki/Detector-Documentation#variable-names-too-similar) | Informational | Medium
82 | `too-many-digits` | [Conformance to numeric notation best practices](https://github.com/crytic/slither/wiki/Detector-Documentation#too-many-digits) | Informational | Medium
83 | `cache-array-length` | [Detects `for` loops that use `length` member of some storage array in their loop condition and don't modify it.](https://github.com/crytic/slither/wiki/Detector-Documentation#cache-array-length) | Optimization | High
84 | `constable-states` | [State variables that could be declared constant](https://github.com/crytic/slither/wiki/Detector-Documentation#state-variables-that-could-be-declared-constant) | Optimization | High
85 | `external-function` | [Public function that could be declared external](https://github.com/crytic/slither/wiki/Detector-Documentation#public-function-that-could-be-declared-external) | Optimization | High
86 | `immutable-states` | [State variables that could be declared immutable](https://github.com/crytic/slither/wiki/Detector-Documentation#state-variables-that-could-be-declared-immutable) | Optimization | High
87 | `var-read-using-this` | [Contract reads its own variable using `this`](https://github.com/crytic/slither/wiki/Detector-Documentation#public-variable-read-in-external-context) | Optimization | High

For more information, see

- The [Detector Documentation](https://github.com/crytic/slither/wiki/Detector-Documentation) for details on each detector
- The [Detection Selection](https://github.com/crytic/slither/wiki/Usage#detector-selection) to run only selected detectors. By default, all the detectors are run.
- The [Triage Mode](https://github.com/crytic/slither/wiki/Usage#triage-mode) to filter individual results

## Printers
### Quick Review Printers
- `human-summary`: [Print a human-readable summary of the contracts](https://github.com/trailofbits/slither/wiki/Printer-documentation#human-summary)
- `inheritance-graph`: [Export the inheritance graph of each contract to a dot file](https://github.com/trailofbits/slither/wiki/Printer-documentation#inheritance-graph)
- `contract-summary`: [Print a summary of the contracts](https://github.com/trailofbits/slither/wiki/Printer-documentation#contract-summary)
- `loc`: [Count the total number lines of code (LOC), source lines of code (SLOC), and comment lines of code (CLOC) found in source files (SRC), dependencies (DEP), and test files (TEST).](https://github.com/trailofbits/slither/wiki/Printer-documentation#loc)

### In-Depth Review Printers
- `call-graph`: [Export the call-graph of the contracts to a dot file](https://github.com/trailofbits/slither/wiki/Printer-documentation#call-graph)
- `cfg`: [Export the CFG of each functions](https://github.com/trailofbits/slither/wiki/Printer-documentation#cfg)
- `function-summary`: [Print a summary of the functions](https://github.com/trailofbits/slither/wiki/Printer-documentation#function-summary)
- `vars-and-auth`: [Print the state variables written and the authorization of the functions](https://github.com/crytic/slither/wiki/Printer-documentation#variables-written-and-authorization)
- `not-pausable`: [Print functions that do not use `whenNotPaused` modifier](https://github.com/trailofbits/slither/wiki/Printer-documentation#when-not-paused).

To run a printer, use `--print` and a comma-separated list of printers.

See the [Printer documentation](https://github.com/crytic/slither/wiki/Printer-documentation) for the complete lists.

## Tools

- `slither-check-upgradeability`: [Review `delegatecall`-based upgradeability](https://github.com/crytic/slither/wiki/Upgradeability-Checks)
- `slither-prop`: [Automatic unit test and property generation](https://github.com/crytic/slither/wiki/Property-generation)
- `slither-flat`: [Flatten a codebase](https://github.com/crytic/slither/wiki/Contract-Flattening)
- `slither-check-erc`: [Check the ERC's conformance](https://github.com/crytic/slither/wiki/ERC-Conformance)
- `slither-format`: [Automatic patch generation](https://github.com/crytic/slither/wiki/Slither-format)
- `slither-read-storage`: [Read storage values from contracts](./slither/tools/read_storage/README.md)
- `slither-interface`: [Generate an interface for a contract](./slither/tools/interface/README.md)

See the [Tool documentation](https://github.com/crytic/slither/wiki/Tool-Documentation) for additional tools.

[Contact us](https://www.trailofbits.com/contact/) to get help on building custom tools.

## API Documentation

Documentation on Slither's internals is available [here](https://crytic.github.io/slither/slither.html).

## Getting Help

Feel free to stop by our [Slack channel](https://empireslacking.herokuapp.com) (#ethereum) for help using or extending Slither.

- The [Printer documentation](https://github.com/trailofbits/slither/wiki/Printer-documentation) describes the information Slither is capable of visualizing for each contract.

- The [Detector documentation](https://github.com/trailofbits/slither/wiki/Adding-a-new-detector) describes how to write a new vulnerability analyses.

- The [API documentation](https://github.com/crytic/slither/wiki/Python-API) describes the methods and objects available for custom analyses.

- The [SlithIR documentation](https://github.com/trailofbits/slither/wiki/SlithIR) describes the SlithIR intermediate representation.

## FAQ

How do I exclude mocks or tests?

- View our documentation on [path filtering](https://github.com/crytic/slither/wiki/Usage#path-filtering).

How do I fix "unknown file" or compilation issues?

- Because slither requires the solc AST, it must have all dependencies available.
If a contract has dependencies, `slither contract.sol` will fail.
Instead, use `slither .` in the parent directory of `contracts/` (you should see `contracts/` when you run `ls`).
If you have a `node_modules/` folder, it must be in the same directory as `contracts/`. To verify that this issue is related to slither,
run the compilation command for the framework you are using e.g `npx hardhat compile`. That must work successfully;
otherwise, slither's compilation engine, crytic-compile, cannot generate the AST.

## License

Slither is licensed and distributed under the AGPLv3 license. [Contact us](mailto:opensource@trailofbits.com) if you're looking for an exception to the terms.

## Publications

### Trail of Bits publication

- [Slither: A Static Analysis Framework For Smart Contracts](https://arxiv.org/abs/1908.09878), Josselin Feist, Gustavo Grieco, Alex Groce - WETSEB '19

### External publications

Title | Usage | Authors | Venue | Code
--- | --- | --- | --- | ---
[ReJection: A AST-Based Reentrancy Vulnerability Detection Method](https://www.researchgate.net/publication/339354823_ReJection_A_AST-Based_Reentrancy_Vulnerability_Detection_Method) | AST-based analysis built on top of Slither | Rui Ma, Zefeng Jian, Guangyuan Chen, Ke Ma, Yujia Chen | CTCIS 19
[MPro: Combining Static and Symbolic Analysis forScalable Testing of Smart Contract](https://arxiv.org/pdf/1911.00570.pdf) | Leverage data dependency through Slither | William Zhang, Sebastian Banescu, Leodardo Pasos, Steven Stewart, Vijay Ganesh | ISSRE 2019 | [MPro](https://github.com/QuanZhang-William/M-Pro)
[ETHPLOIT: From Fuzzing to Efficient Exploit Generation against Smart Contracts](https://wcventure.github.io/FuzzingPaper/Paper/SANER20_ETHPLOIT.pdf) | Leverage data dependency through Slither | Qingzhao Zhang, Yizhuo Wang, Juanru Li, Siqi Ma | SANER 20
[Verification of Ethereum Smart Contracts: A Model Checking Approach](http://www.ijmlc.org/vol10/977-AM0059.pdf) | Symbolic execution built on top of Slither’s CFG | Tam Bang, Hoang H Nguyen, Dung Nguyen, Toan Trieu, Tho Quan | IJMLC 20
[Smart Contract Repair](https://arxiv.org/pdf/1912.05823.pdf) | Rely on Slither’s vulnerabilities detectors | Xiao Liang Yu, Omar Al-Bataineh, David Lo, Abhik Roychoudhury | TOSEM 20 | [SCRepair](https://github.com/xiaoly8/SCRepair/)
[Demystifying Loops in Smart Contracts](https://www.microsoft.com/en-us/research/uploads/prod/2020/08/loops_solidity__camera_ready-5f3fec3f15c69.pdf) | Leverage data dependency through Slither | Ben Mariano, Yanju Chen, Yu Feng, Shuvendu Lahiri, Isil Dillig | ASE 20
[Trace-Based Dynamic Gas Estimation of Loops in Smart Contracts](https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=9268144) | Use Slither’s CFG to detect loops | Chunmiao Li, Shijie Nie, Yang Cao, Yijun Yu, Zhenjiang Hu | IEEE Open J. Comput. Soc. 1 (2020)
[SAILFISH: Vetting Smart Contract State-Inconsistency Bugs in Seconds](https://arxiv.org/pdf/2104.08638.pdf) | Rely on SlithIR to build a *storage dependency graph* | Priyanka Bose, Dipanjan Das, Yanju Chen, Yu Feng, Christopher Kruegel, and Giovanni Vigna | S&P 22 | [Sailfish](https://github.com/ucsb-seclab/sailfish)
[SolType: Refinement Types for Arithmetic Overflow in Solidity](https://arxiv.org/abs/2110.00677) | Use Slither as frontend to build refinement type system | Bryan Tan, Benjamin Mariano, Shuvendu K. Lahiri, Isil Dillig, Yu Feng | POPL 22
[Do Not Rug on Me: Leveraging Machine Learning Techniques for Automated Scam Detection](https://www.mdpi.com/2227-7390/10/6/949) | Use Slither to extract tokens' features (mintable, pausable, ..) | Mazorra, Bruno, Victor Adan, and Vanesa Daza | Mathematics 10.6 (2022)
[MANDO: Multi-Level Heterogeneous Graph Embeddings for Fine-Grained Detection of Smart Contract Vulnerabilities](https://arxiv.org/abs/2208.13252) | Use Slither to extract the CFG and call graph | Hoang Nguyen, Nhat-Minh Nguyen, Chunyao Xie, Zahra Ahmadi, Daniel Kudendo, Thanh-Nam Doan and Lingxiao Jiang| IEEE 9th International Conference on Data Science and Advanced Analytics (DSAA, 2022) | [ge-sc](https://github.com/MANDO-Project/ge-sc)
[Automated Auditing of Price Gouging TOD Vulnerabilities in Smart Contracts](https://www.cs.toronto.edu/~fanl/papers/price-icbc22.pdf) | Use Slither to extract the CFG and data dependencies| Sidi Mohamed Beillahi, Eric Keilty, Keerthi Nelaturu, Andreas Veneris, and Fan Long | 2022 IEEE International Conference on Blockchain and Cryptocurrency (ICBC) | [Smart-Contract-Repair](https://github.com/Veneris-Group/TOD-Location-Rectification)

If you are using Slither on an academic work, consider applying to the [Crytic $10k Research Prize](https://blog.trailofbits.com/2019/11/13/announcing-the-crytic-10k-research-prize/).
