## Usage

- [How to run Slither](#how-to-run-slither)
  - [Foundry/Hardhat](#foundryhardhat)
  - [solc](#solc)
  - [Etherscan](#etherscan)
  - [AST input](#ast-file)
- [Options](#options)
  - [Detector selection](#detector-selection)
  - [Printer selection](#printer-selection)
  - [Path Filtering](#path-filtering)
  - [Triage mode](#triage-mode)
  - [Configuration file](#configuration-file)
- [IDE integrations](#ide-integration)

## How to run Slither

All the [`crytic-compile`](https://github.com/crytic/crytic-compile/wiki/Configuration) options are available through Slither.

### Foundry/hardhat

To run Slither on a Foundry/hardhat directory:

```
slither .
```

### solc

To run Slither from a Solidity file:

```
slither file.sol
```

### Etherscan

To run Slither from a contract hosted on Etherscan, run

```
slither 0x7F37f78cBD74481E593F9C737776F7113d76B315
```

We recommend installing [solc-select](https://github.com/crytic/solc-select/) so Slither can switch to the expected solc version automatically.

### Detector selection

Slither runs all its detectors by default.

To run only selected detectors, use `--detect detector1,detector2`. For example:

```
slither file.sol --detect arbitrary-send,pragma
```

To exclude detectors, use `--exclude detector1,detector2`. For example:

```
slither file.sol --exclude naming-convention,unused-state,suicidal
```

To exclude detectors with an informational or low severity, use `--exclude-informational` or `--exclude-low`.

`--list-detectors` lists [available detectors](https://github.com/crytic/slither/wiki/Detector-Documentation).

### Printer selection

By default, no printers are run.

To run selected printers, use `--print printer1,printer2`. For example:

```
slither file.sol --print inheritance-graph
```

`--list-printers` lists [available printers](https://github.com/crytic/slither/wiki/Printer-Documentation).

### Path filtering

`--filter-paths path1` will exclude all the results that are only related to `path1`. The path specified can be a path directory or a filename. Direct string comparison and [Python regular expression](https://docs.python.org/3/library/re.html) are used.

Examples:

```
slither . --filter-paths "openzepellin"
```

Filter all the results only related to openzepellin.

```
slither . --filter-paths "Migrations.sol|ConvertLib.sol"
```

Filter all the results only related to the file `SafeMath.sol` or `ConvertLib.sol`.

### Triage mode

Slither offers two ways to remove results:

- By adding `//slither-disable-next-line DETECTOR_NAME` before the issue
- By adding `// slither-disable-start [detector] ... // slither-disable-end [detector]` around the code to disable the detector on a large section
- By adding `@custom:security non-reentrant` before the variable declaration will indicate to Slither that the external calls from this variable are non-reentrant
- By running the triage mode (see below)

### Triage mode

`--triage-mode` runs Slither in its triage mode. For every finding, Slither will ask if the result should be shown for the next run. Results are saved in `slither.db.json`.

Examples:

```
slither . --triage-mode
[...]
0: C.destination (test.sol#3) is never initialized. It is used in:
	- f (test.sol#5-7)
Reference: https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#uninitialized-state-variables
Results to hide during next runs: "0,1,..." or "All" (enter to not hide results):  0
[...]
```

The second run of Slither will hide the above result.

To show the hidden results again, delete `slither.db.json`.

### Configuration File

Some options can be set through a json configuration file. By default, `slither.config.json` is used if present (it can be changed through `--config-file file.config.json`).

Options passed via the CLI have priority over options set in the configuration file.

The following flags are supported:

```
{
    "detectors_to_run": "all",
    "printers_to_run": None,
    "detectors_to_exclude": None,
    "detectors_to_include": None,
    "exclude_dependencies": False,
    "exclude_informational": False,
    "exclude_optimization": False,
    "exclude_low": False,
    "exclude_medium": False,
    "exclude_high": False,
    "fail_on": FailOnLevel.PEDANTIC,
    "json": None,
    "sarif": None,
    "disable_color": False,
    "filter_paths": None,
    "include_paths": None,
    "generate_patches": False,
    "skip_assembly": False,
    "legacy_ast": False,
    "zip": None,
    "zip_type": "lzma",
    "show_ignored_findings": False,
    "sarif_input": "export.sarif",
    "sarif_triage": "export.sarif.sarifexplorer",
    "triage_database": "slither.db.json",
    # codex
    "codex": False,
    "codex_contracts": "all",
    "codex_model": "text-davinci-003",
    "codex_temperature": 0,
    "codex_max_tokens": 300,
    "codex_log": False,
}
```

For flags related to the compilation, see the [`crytic-compile` configuration](https://github.com/crytic/crytic-compile/blob/master/crytic_compile/cryticparser/defaults.py)
