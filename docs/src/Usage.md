# Usage

- [How to run Slither](#how-to-run-slither)
  - [Foundry/hardhat](#foundryhardhat)
  - [solc](#solc)
  - [Etherscan](#etherscan)
- [Detector selection](#detector-selection)
- [Printer selection](#printer-selection)
- [Path filtering](#path-filtering)
- [Suppressing findings](#suppressing-findings)
- [Triage mode](#triage-mode)
- [Configuration File](#configuration-file)

## How to run Slither

All the [`crytic-compile`](https://github.com/crytic/crytic-compile/wiki/Configuration) options are available through Slither.

### Foundry/hardhat

To run Slither on a Foundry/hardhat directory:

```sh
slither .
```

### solc

To run Slither from a Solidity file:

```sh
slither file.sol
```

### Etherscan

To run Slither from a contract hosted on Etherscan, run

```sh
slither 0x7F37f78cBD74481E593F9C737776F7113d76B315
```

We recommend installing [solc-select](https://github.com/crytic/solc-select/) so Slither can switch to the expected solc version automatically.

### Detector selection

Slither runs all its detectors by default.

To run only selected detectors, use `--detect detector1,detector2`. For example:

```sh
slither file.sol --detect arbitrary-send,pragma
```

To exclude detectors, use `--exclude detector1,detector2`. For example:

```sh
slither file.sol --exclude naming-convention,unused-state,suicidal
```

To exclude detectors with an informational or low severity, use `--exclude-informational` or `--exclude-low`.

`--list-detectors` lists [available detectors](https://github.com/crytic/slither/wiki/Detector-Documentation).

### Printer selection

By default, no printers are run.

To run selected printers, use `--print printer1,printer2`. For example:

```sh
slither file.sol --print inheritance-graph
```

`--list-printers` lists [available printers](https://github.com/crytic/slither/wiki/Printer-Documentation).

### Path filtering

`--filter-paths path1` will exclude all the results that are only related to `path1`. The path specified can be a path directory or a filename. Direct string comparison and [Python regular expression](https://docs.python.org/3/library/re.html) are used.

Examples:

```sh
slither . --filter-paths "openzepellin"
```

Filter all the results only related to openzepellin.

```bash
slither . --filter-paths "SafeMath.sol|ConvertLib.sol"
```

Filter all the results only related to the file `SafeMath.sol` or `ConvertLib.sol`.

### Suppressing findings

Slither offers several ways to suppress results:

- By adding `//slither-disable-next-line DETECTOR_NAME` before the issue
- By adding `// slither-disable-start [detector] ... // slither-disable-end [detector]` around the code to disable the detector on a large section
- By adding `@custom:security non-reentrant` before the variable declaration will indicate to Slither that the external calls from this variable are non-reentrant
- By running the triage mode (see below)

### Triage mode

`--triage-mode` runs Slither in its triage mode. For every finding, Slither will ask if the result should be shown for the next run. Results are saved in `slither.db.json`.

Examples:

```sh
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

Run `slither --list-config` to generate the supported configuration keys and their default values from the current Slither and `crytic-compile` defaults:

```json
{
    "brownie_ignore_compile": false,
    "buidler_cache_directory": "cache",
    "buidler_ignore_compile": false,
    "buidler_skip_directory_name_fix": false,
    "codex": false,
    "codex_contracts": "all",
    "codex_log": false,
    "codex_max_tokens": 300,
    "codex_model": "text-davinci-003",
    "codex_temperature": 0,
    "compile_custom_build": null,
    "compile_force_framework": null,
    "compile_libraries": null,
    "compile_remove_metadata": false,
    "dapp_ignore_compile": false,
    "detectors_to_exclude": null,
    "detectors_to_include": null,
    "detectors_to_run": "all",
    "disable_color": false,
    "embark_ignore_compile": false,
    "embark_overwrite_config": false,
    "etherlime_compile_arguments": null,
    "etherlime_ignore_compile": false,
    "etherscan_api_key": null,
    "etherscan_export_directory": "etherscan-contracts",
    "etherscan_only_bytecode": false,
    "etherscan_only_source_code": false,
    "exclude_dependencies": false,
    "exclude_high": false,
    "exclude_informational": false,
    "exclude_location": false,
    "exclude_low": false,
    "exclude_medium": false,
    "exclude_optimization": false,
    "export_dir": "crytic-export",
    "fail_on": "pedantic",
    "filter_paths": null,
    "foundry_compile_all": false,
    "foundry_ignore_compile": false,
    "foundry_out_directory": null,
    "generate_patches": false,
    "hardhat_artifacts_directory": null,
    "hardhat_cache_directory": null,
    "hardhat_ignore_compile": false,
    "ignore_compile": false,
    "include_paths": null,
    "json": null,
    "json-types": "detectors,printers",
    "legacy_ast": false,
    "no_fail": false,
    "npx_disable": false,
    "printers_to_run": null,
    "sarif": null,
    "sarif_input": "export.sarif",
    "sarif_triage": "export.sarif.sarifexplorer",
    "show_ignored_findings": false,
    "skip_assembly": false,
    "skip_clean": false,
    "solc": "solc",
    "solc_args": null,
    "solc_disable_warnings": false,
    "solc_force_legacy_json": false,
    "solc_remaps": null,
    "solc_solcs_bin": null,
    "solc_solcs_select": null,
    "solc_standard_json": false,
    "solc_working_dir": null,
    "triage_database": "slither.db.json",
    "truffle_build_directory": "build/contracts",
    "truffle_ignore_compile": false,
    "truffle_overwrite_config": false,
    "truffle_overwrite_version": null,
    "truffle_version": null,
    "waffle_config_file": null,
    "waffle_ignore_compile": false,
    "warn_unused_ignores": false,
    "zip": null,
    "zip_type": "lzma"
}
```

For details about the compilation-related flags, see the [`crytic-compile` configuration](https://github.com/crytic/crytic-compile/blob/master/crytic_compile/cryticparser/defaults.py).
