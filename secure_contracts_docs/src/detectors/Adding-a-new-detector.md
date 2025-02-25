Slither's plugin architecture lets you integrate new detectors that run from the command line.

## Detector Skeleton

The skeleton for a detector is:

```python
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class Skeleton(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = 'mydetector' # slither will launch the detector with slither.py --detect mydetector
    HELP = 'Help printed by slither'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = ''

    WIKI_TITLE = ''
    WIKI_DESCRIPTION = ''
    WIKI_EXPLOIT_SCENARIO = ''
    WIKI_RECOMMENDATION = ''

    def _detect(self):
        info = ['This is an example']
        res = self.generate_result(info)

        return [res]
```

- `ARGUMENT` lets you run the detector from the command line
- `HELP` is the information printed from the command line
- `IMPACT` indicates the impact of the issue. Allowed values are:
  - `DetectorClassification.OPTIMIZATION`: printed in green
  - `DetectorClassification.INFORMATIONAL`: printed in green
  - `DetectorClassification.LOW`: printed in green
  - `DetectorClassification.MEDIUM`: printed in yellow
  - `DetectorClassification.HIGH`: printed in red
- `CONFIDENCE` indicates your confidence in the analysis. Allowed values are:
  - `DetectorClassification.LOW`
  - `DetectorClassification.MEDIUM`
  - `DetectorClassification.HIGH`
- `WIKI` constants are used to generate automatically the documentation.

`_detect()` needs to return a list of findings. A finding is an element generated with `self.generate_result(info)`, where `info`  is a list of text or contract's object (contract, function, node, ...)

An `AbstractDetector` object has the `slither` attribute, which returns the current `Slither` object.

## Integration

You can integrate your detector into Slither by:
- Adding it in [slither/detectors/all_detectors.py](https://github.com/trailofbits/slither/blob/ae7c410938b616d993e6c27678f6e48d9a4d7dd6/slither/detectors/all_detectors.py)
- or, by creating a plugin package (see the [skeleton example](https://github.com/trailofbits/slither/tree/ae7c410938b616d993e6c27678f6e48d9a4d7dd6/plugin_example)).

### Test the detector
See [CONTRIBUTING.md#development-environment](https://github.com/crytic/slither/blob/master/CONTRIBUTING.md#development-environment)

## Example
[backdoor.py](https://github.com/crytic/slither/blob/ae7c410938b616d993e6c27678f6e48d9a4d7dd6/slither/detectors/examples/backdoor.py) will detect any function with `backdoor` in its name.
