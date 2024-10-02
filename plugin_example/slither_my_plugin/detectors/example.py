from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class Example(AbstractDetector):  # pylint: disable=too-few-public-methods
    """
    Documentation
    """

    ARGUMENT = "mydetector"  # slither will launch the detector with slither.py --mydetector
    HELP = "Help printed by slither"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://www.example.com/#example-detector"

    WIKI_TITLE = "example detector"
    WIKI_DESCRIPTION = "This is an example detector that always generates a finding"
    WIKI_EXPLOIT_SCENARIO = "Scenario goes here"
    WIKI_RECOMMENDATION = "Customize the detector"

    def _detect(self):

        info = "This is an example!"

        json = self.generate_result(info)

        return [json]
