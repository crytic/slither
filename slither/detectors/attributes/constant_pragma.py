"""
    Check that the same pragma is used in all the files
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class ConstantPragma(AbstractDetector):
    """
    Check that the same pragma is used in all the files
    """

    ARGUMENT = 'pragma'
    HELP = 'If different pragma directives are used'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#different-pragma-directives-are-used'

    def detect(self):
        results = []
        pragma = self.slither.pragma_directives
        versions = [p.version for p in pragma]
        versions = list(set(versions))

        if len(versions) > 1:
            info = "Different versions of Solidity is used in {}:\n".format(self.filename)
            info += "\t- Version used: {}\n".format([str(v) for v in versions])
            for p in pragma:
                info += "\t- {} declares {}\n".format(p.source_mapping_str, str(p))
            self.log(info)

            json = self.generate_json_result()
            # follow the same format than add_nodes_to_json
            json['expressions'] = [{'expression': p.version,
                                    'source_mapping': p.source_mapping} for p in pragma]
            results.append(json)

        return results
