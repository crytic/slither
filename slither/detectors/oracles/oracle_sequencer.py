from slither.detectors.abstract_detector import DetectorClassification
from slither.detectors.oracles.oracle import OracleDetector


class SequencerCheck(OracleDetector):

    """
    Documentation
    """

    ARGUMENT = (
        "oracle-sequencer"  # slither will launch the detector with slither.py --detect mydetector
    )
    HELP = "Oracle vulnerabilities"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.INFORMATIONAL

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#oracle-sequencer"

    WIKI_TITLE = "Oracle Sequencer"
    WIKI_DESCRIPTION = "Detection of oracle sequencer."
    WIKI_EXPLOIT_SCENARIO = "---"
    WIKI_RECOMMENDATION = "If you deploy contracts on the second layer as Arbitrum, you should perform an additional check if the sequencer is active. For more information visit https://docs.chain.link/data-feeds/l2-sequencer-feeds#available-networks"

    def _detect(self):
        results = []
        output = []
        super()._detect()
        if len(self.oracles) > 0:
            for oracle in self.oracles:
                results.append(
                    f"Oracle call to {oracle.interface} ({oracle.node.source_mapping}) is used. Additional checks for sequencer lifeness should be implemented if deployed on the second layer.\n"
                )
            res = self.generate_result(results)
            output.append(res)
        return output
