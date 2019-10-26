from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils import json_utils


class Backdoor(AbstractDetector):
    """
    Detect function named backdoor
    """

    ARGUMENT = 'backdoor'  # slither will launch the detector with slither.py --mydetector
    HELP = 'Function named backdoor (detector example)'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH


    WIKI = 'https://github.com/trailofbits/slither/wiki/Adding-a-new-detector'
    WIKI_TITLE = 'Backdoor example'
    WIKI_DESCRIPTION = 'Plugin example'
    WIKI_EXPLOIT_SCENARIO = '..'
    WIKI_RECOMMENDATION = '..'

    def _detect(self):
        results = []

        for contract in self.slither.contracts_derived:
            # Check if a function has 'backdoor' in its name
            for f in contract.functions:
                if 'backdoor' in f.name:
                    # Info to be printed
                    info = 'Backdoor function found in {}.{} ({})\n'
                    info = info.format(contract.name, f.name, f.source_mapping_str)
                    # Add the result in result
                    json = self.generate_json_result(info)
                    json_utils.add_function_to_json(f, json)
                    results.append(json)

        return results
