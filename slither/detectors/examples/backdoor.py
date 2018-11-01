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
        ret = []

        for contract in sorted(self.slither.contracts_derived, key=lambda c: c.name):
            # Check if a function has 'backdoor' in its name
            for f in sorted(contract.functions, key=lambda x: x.name):
                if 'backdoor' in f.name:
                    # Info to be printed
                    info = 'Backdoor function found in {}.{}'.format(contract.name, f.name)
                    # Print the info
                    self.log(info)
                    # Add the result in ret
                    source = f.source_mapping
                    ret.append({'vuln': 'backdoor', 'contract': contract.name, 'sourceMapping' : source})

        return ret
