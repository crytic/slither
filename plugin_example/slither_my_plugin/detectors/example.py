from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class Example(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = "mydetector"  # slither will launch the detector with slither.py --mydetector
    HELP = "Help printed by slither"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = ""

    WIKI_TITLE = ""
    WIKI_DESCRIPTION = ""
    WIKI_EXPLOIT_SCENARIO = ""
    WIKI_RECOMMENDATION = ""

    def _detect(self):

        info = "This is an example!"

        json = self.generate_result(info)

        return [json]
