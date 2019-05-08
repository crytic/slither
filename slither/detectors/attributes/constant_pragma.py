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

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#different-pragma-directives-are-used'


    WIKI_TITLE = 'Different pragma directives are used'
    WIKI_DESCRIPTION = 'Detect if different Solidity versions are used.'
    WIKI_RECOMMENDATION = 'Use one Solidity version.'

    def _detect(self):
        results = []
        pragma = self.slither.pragma_directives
        versions = [p.version for p in pragma]
        versions = sorted(list(set(versions)))

        if len(versions) > 1:
            info = "Different versions of Solidity is used in {}:\n".format(self.filename)
            info += "\t- Version used: {}\n".format([str(v) for v in versions])
            for p in pragma:
                info += "\t- {} declares {}\n".format(p.source_mapping_str, str(p))

            json = self.generate_json_result(info)

            # Add each pragma to our elements
            for p in pragma:
                self.add_pragma_to_json(p, json)
            results.append(json)

        return results
