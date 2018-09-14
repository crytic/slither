
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class Example(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = 'mydetector' # slither will launch the detector with slither.py --mydetector
    HELP = 'Help printed by slither'
    CLASSIFICATION = DetectorClassification.HIGH

    def detect(self):

        self.logger('Nothing to detect!')

        return []
