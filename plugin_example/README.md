# Slither, Plugin Example

This repository contains an example of plugin for Slither.

See the [detector documentation](https://github.com/trailofbits/slither/wiki/Adding-a-new-detector).

## Architecture

- `pyproject.toml`: Contains the plugin information and dependencies
- `slither_my_plugin/__init__.py`: Contains `make_plugin()`. The function must return the list of new detectors and printers
- `slither_my_plugin/detectors/example.py`: Detector plugin skeleton.

## Installation

Once these files are updated with your plugin, install it:

```bash
uv sync
uv run slither --help  # Verify plugin is loaded
```
