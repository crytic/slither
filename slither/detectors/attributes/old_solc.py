"""
    Check if an old version of solc is used
    Solidity >= 0.4.23 should be used
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class OldSolc(AbstractDetector):
    """
    Check if an old version of solc is used
    """

    ARGUMENT = 'solc-version'
    HELP = 'Old versions of Solidity (< 0.4.23)'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#old-versions-of-solidity'

    @staticmethod
    def _convert_pragma(version):
        return version.replace('solidity', '').replace('^', '')

    def detect(self):
        results = []
        pragma = self.slither.pragma_directives
        old_pragma = sorted([p for p in pragma if self._convert_pragma(p.version) not in ['0.4.23', '0.4.24']], key=lambda x:str(x))

        if old_pragma:
            info = "Old version (<0.4.23) of Solidity used in {}:\n".format(self.filename)
            for p in old_pragma:
                info += "\t- {} declares {}\n".format(p.source_mapping_str, str(p))
            self.log(info)

            json = self.generate_json_result(info)
            # follow the same format than add_nodes_to_json
            json['expressions'] = [{'expression': p.version,
                                    'source_mapping': p.source_mapping} for p in old_pragma]
            results.append(json)

        return results
