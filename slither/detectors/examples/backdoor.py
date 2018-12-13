from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class Backdoor(AbstractDetector):
    """
    Detect function named backdoor
    """

    ARGUMENT = 'backdoor'  # slither will launch the detector with slither.py --mydetector
    HELP = 'Function named backdoor (detector example)'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    def detect(self):
        results = []

        for contract in self.slither.contracts_derived:
            # Check if a function has 'backdoor' in its name
            for f in contract.functions:
                if 'backdoor' in f.name:
                    # Info to be printed
                    info = 'Backdoor function found in {}.{} ({})\n'
                    info = info.format(contract.name, f.name, f.source_mapping_str)
                    # Print the info
                    self.log(info)
                    # Add the result in result
                    json = self.generate_json_result(info)
                    self.add_function_to_json(f, json)
                    results.append(json)


        return results
