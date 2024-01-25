from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract
from slither.core.expressions import expression
from slither.slithir.operations import Binary, BinaryType
from enum import Enum
from slither.detectors.oracles.oracle import OracleDetector, Oracle, VarInCondition
from slither.slithir.operations.solidity_call import SolidityCall
from slither.core.cfg.node import NodeType
from slither.core.variables.state_variable import StateVariable

from slither.core.cfg.node import Node, NodeType
from slither.slithir.operations.return_operation import Return
from slither.core.declarations import Function
from slither.core.declarations.function_contract import FunctionContract
from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import HighLevelCall, Assignment, Unpack, Operation
from slither.slithir.variables import TupleVariable
from slither.core.expressions.expression import Expression
from typing import List
from slither.slithir.variables.constant import Constant


class SequencerCheck(OracleDetector):

    """
    Documentation
    """

    ARGUMENT = "oracle-sequencer"  # slither will launch the detector with slither.py --detect mydetector
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
                results.append(f"Oracle call to {oracle.interface} ({oracle.node.source_mapping}) is used. Additional checks for sequencer lifeness should be implemented if deployed on the second layer.\n")
            res = self.generate_result(results)
            output.append(res)
        return output