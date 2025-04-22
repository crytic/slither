# Slither, Plugin Example

This repository contains an example of plugin for Slither.
See the [detector documentation](https://github.com/trailofbits/slither/wiki/Adding-a-new-detector).
See the [detector documentation][detectorDocumentation].

## Architecture

- `setup.py`: Contain the plugin information
- `slither_my_plugin/__init__.py`: Contains `make_plugin()`. This function is responsible for returning a list of custom detectors and printers to be used by Slither.
- `slither_my_plugin/detectors/example.py`: Detector plugin skeleton.

Once these files are updated with your plugin, you can install it:
```bash
python setup.py develop
```

We recommend to use a Python virtual environment (for example: [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/)).


[detectorDocumentation]: https://github.com/trailofbits/slither/wiki/Adding-a-new-detector