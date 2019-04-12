from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
import re

class RightToLeftOverride(AbstractDetector):
    """
    Detect the usage of a Right-To-Left-Override (U+202E) character
    """

    ARGUMENT = 'rtlo'  
    HELP = 'Right-To-Left-Override control character is used'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#right-to-left-override'
    WIKI_TITLE = 'Right-To-Left-Override character'
    WIKI_DESCRIPTION = 'An attacker can manipulate the logic of the contract by using a right-to-left-override character (U+202E)'
    WIKI_EXPLOIT_SCENARIO = ' '
    WIKI_RECOMMENDATION = 'Special control characters should not be allowed'

    def _detect(self):
        results = []

        pattern = re.compile(".*\u202e.*");
        for filename, source in self.slither.source_code.items():
            info = "{} contains a unicode right-to-left-override character:\n".format(filename)
            found = False
            for match in pattern.finditer(source):
                match_line = match.group(0)
                info += "\t- {}\n".format(match_line)
                found = True

            if found:
                json = self.generate_json_result(info)
                results.append(json)

        return results
