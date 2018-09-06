from slither.detectors.abstractDetector import AbstractDetector
from slither.detectors.detectorClassification import DetectorClassification

class Backdoor(AbstractDetector):
    """
    Detect function named backdoor
    """

    ARGUMENT = 'backdoor' # slither will launch the detector with slither.py --mydetector
    HELP = 'Function named backdoor (detector example)'
    CLASSIFICATION = DetectorClassification.HIGH

    def detect(self):
        ret = []

        for contract in self.slither.contracts_derived:
            # Check if a function has 'backdoor' in its name
            if any('backdoor' in f.name for f in contract.functions):
                # Info to be printed
                info = 'Backdoor function found in {}'.format(contract.name)
                # Print the info
                self.log(info)
                # Add the result in ret
                ret.append({'vuln':'backdoor', 'contract':contract.name})
        return ret
