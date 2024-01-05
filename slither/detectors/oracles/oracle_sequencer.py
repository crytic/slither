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

    ARGUMENT = "sequencer"  # slither will launch the detector with slither.py --detect mydetector
    HELP = "Help printed by slither"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.INFORMATIONAL

    WIKI = "RUN"

    WIKI_TITLE = "asda"
    WIKI_DESCRIPTION = "asdsad"
    WIKI_EXPLOIT_SCENARIO = "asdsad"
    WIKI_RECOMMENDATION = "asdsad"

    def _detect(self):
        results = []
        output = []
        super()._detect()
        if len(self.oracles) > 0:
            results.append("The application uses an oracle, if you deploy on second layer as an Arbitrum, you should check if the sequencer is active.")
            res = self.generate_result(results)
            output.append(res)
        return output