# Slither, Plugin Example

This repo contains an example of plugin for Slither.

See the [detector documentation](https://github.com/trailofbits/slither/wiki/Adding-a-new-detector).

## Architecture

- `setup.py`: Contain the plugin information
- `slither_my_plugin/__init__.py`: Contain `make_plugin()`. The function must return the list of new detectors and printers 
- `slither_my_plugin/detectors/example.py`: Detector plugin skeleton.

Once these files are updated with your plugin, you can install it:
```
python setup.py develop
```

We recommend to use a Python virtual environment (for example: [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/)).

