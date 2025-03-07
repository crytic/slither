# Slither

The objective of this tutorial is to demonstrate how to use Slither to automatically find bugs in smart contracts.

- [Installation](#installation)
- [Command-line usage](#command-line)
- [Introduction to static analysis](./static_analysis.md): A concise introduction to static analysis
- [API](../api/api.md): Python API description

Once you feel confident with the material in this README, proceed to the exercises:

- [Exercise 1](./exercise1.md): Function override protection
- [Exercise 2](./exercise2.md): Check for access controls
- [Exercise 3](./exercise3.md): Find variable used in conditional statements

Watch Slither's [code walkthrough](https://www.youtube.com/watch?v=EUl3UlYSluU), or [API walkthrough](https://www.youtube.com/watch?v=Ijf0pellvgw) to learn about its code structure.

## Installation

Slither requires Python >= 3.8. You can install it through pip or by using Docker.

Installing Slither through pip:

```bash
pip3 install --user slither-analyzer
```

### Docker

Installing Slither through Docker:

```bash
docker pull trailofbits/eth-security-toolbox
docker run -it -v "$PWD":/home/trufflecon trailofbits/eth-security-toolbox
```

_The last command runs the eth-security-toolbox in a Docker container that has access to your current directory. You can modify the files from your host, and run the tools on the files from the Docker container._

Inside the Docker container, run:

```bash
solc-select 0.5.11
cd /home/trufflecon/
```

## Command-line

**Command-line vs. user-defined scripts.** Slither comes with a set of predefined detectors that can identify many common bugs. Running Slither from the command-line will execute all the detectors without requiring detailed knowledge of static analysis:

```bash
slither project_paths
```

Besides detectors, Slither also offers code review capabilities through its [printers](https://github.com/crytic/slither#printers) and [tools](https://github.com/crytic/slither#tools).
