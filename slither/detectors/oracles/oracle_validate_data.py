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


class OracleVarType(Enum):
    ROUNDID = 0
    ANSWER = 1
    STARTEDAT = 2
    UPDATEDAT = 3
    ANSWEREDINROUND = 4


class OracleDataCheck(OracleDetector):
    """
    Documentation
    """

    ARGUMENT = "oracle"  # slither will launch the detector with slither.py --detect mydetector
    HELP = "Help printed by slither"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "RUN"

    WIKI_TITLE = "asda"
    WIKI_DESCRIPTION = "asdsad"
    WIKI_EXPLOIT_SCENARIO = "asdsad"
    WIKI_RECOMMENDATION = "asdsad"

    def check_staleness(self, var: VarInCondition) -> bool:
        if var is None:
            return False
        for node in var.nodes_with_var:
            str_node = str(node)
            # print(str_node)
            if (
                "block.timestamp" in str_node
            ):  # TODO maybe try something like block.timestamp - updatedAt < b
                return True

            # for ir in node.irs:
            #     if isinstance(ir, Binary):
            #         if ir.type in (BinaryType.LESS, BinaryType.LESS_EQUAL):
            #             if node.contains_require_or_assert():
            #                 pass
            #             elif node.contains_conditional():
            #                 pass
            #         elif ir.type in (BinaryType.GREATER, BinaryType.GREATER_EQUAL):
            #             pass
        return False

    def check_RoundId(
        self, var: VarInCondition, var2: VarInCondition
    ) -> bool:  # https://solodit.xyz/issues/chainlink-oracle-return-values-are-not-handled-property-halborn-savvy-defi-pdf
        if var is None or var2 is None:
            return False
        for node in var.nodes_with_var:
            for ir in node.irs:
                if isinstance(ir, Binary):
                    if ir.type in (BinaryType.GREATER, BinaryType.GREATER_EQUAL):
                        if ir.variable_right == var.var and ir.variable_left == var2.var:
                            return True
                    elif ir.type in (BinaryType.LESS, BinaryType.LESS_EQUAL):
                        if ir.variable_right == var2.var and ir.variable_left == var.var:
                            return True
            if self.check_revert(node):
                return True

        return False

    def check_revert(self, node: Node) -> bool:
        for n in node.sons:
            if n.type == NodeType.EXPRESSION:
                for ir in n.irs:
                    if isinstance(ir, SolidityCall):
                        if "revert" in ir.function.name:
                            return True
        return False

    def return_boolean(self, node: Node) -> bool:
        for n in node.sons:
            if n.type == NodeType.RETURN:
                for ir in n.irs:
                    if isinstance(ir, Return):
                        return True

    def check_price(
        self, var: VarInCondition, oracle: Oracle
    ) -> bool:  # TODO I need to divie require or IF
        if var is None:
            return False
        for node in var.nodes_with_var:  # TODO testing
            for ir in node.irs:
                if isinstance(ir, Binary):
                    if isinstance(ir.variable_right, Constant):
                        if ir.type is (BinaryType.GREATER):
                            if ir.variable_right.value == 0:
                                return True
                        elif ir.type is (BinaryType.NOT_EQUAL):
                            if ir.variable_right.value == 0:
                                return True
                    if isinstance(ir.variable_left, Constant):
                        if ir.type is (BinaryType.LESS):
                            if ir.variable_left.value == 0:
                                return True
                    if self.check_revert(node):
                        return True
                    elif self.return_boolean(node):
                        return True

                       
        return False

    def generate_naive_order(self):
        vars_order = {}
        vars_order[OracleVarType.ROUNDID.value] = None
        vars_order[OracleVarType.ANSWER.value] = None
        vars_order[OracleVarType.STARTEDAT.value] = None
        vars_order[OracleVarType.UPDATEDAT.value] = None
        vars_order[OracleVarType.ANSWEREDINROUND.value] = None
        return vars_order

    def find_which_vars_are_used(self, oracle: Oracle):
        vars_order = self.generate_naive_order()
        for i in range(len(oracle.oracle_vars)):
            vars_order[oracle.returned_vars_indexes[i]] = oracle.oracle_vars[i]
        return vars_order

    def is_needed_to_check_conditions(self, oracle, var):
        if isinstance(var, VarInCondition):
            var = var.var
        if var in oracle.vars_not_in_condition:
            return False
        return True

    def is_sequencer_check(self, answer, startedAt):
        if answer is None or startedAt is None:
            return False
        answer_checked = False
        startedAt_checked = False

        for node in answer.nodes:
            for ir in node.irs:
                if isinstance(ir, Binary):
                    if ir.type is (BinaryType.EQUAL):
                        if isinstance(ir.variable_right, Constant):
                            if ir.variable_right.value == 1:
                                answer_checked = True
        startedAt_checked = self.check_staleness(startedAt)
        print(answer_checked, startedAt_checked)

        return answer_checked and startedAt_checked

    def naive_check(self, oracle: Oracle):
        vars_order = self.find_which_vars_are_used(oracle)
        problems = []
        for (index, var) in vars_order.items():
            if not self.is_needed_to_check_conditions(oracle, var):
                continue
            # if index == OracleVarType.ROUNDID.value: #TODO this is maybe not so mandatory
            #     if not self.check_RoundId(var, vars_order[OracleVarType.ANSWEREDINROUND.value]):
            #         problems.append("RoundID value is not checked correctly. It was returned by the oracle call in the function {} of contract {}.\n".format( oracle.function, oracle.node.source_mapping))
            if index == OracleVarType.ANSWER.value:
                if not self.check_price(var, oracle):
                    problems.append(
                        "Price value is not checked correctly. It was returned by the oracle call in the function {} of contract {}.\n".format(
                            oracle.function, oracle.node.source_mapping
                        )
                    )
            elif index == OracleVarType.UPDATEDAT.value:
                if not self.check_staleness(var):
                    problems.append(
                        "UpdatedAt value is not checked correctly. It was returned by the oracle call in the function {} of contract {}.\n".format(
                            oracle.function, oracle.node.source_mapping
                        )
                    )
            elif (
                index == OracleVarType.STARTEDAT.value
                and vars_order[OracleVarType.STARTEDAT.value] is not None
            ):
                if self.is_sequencer_check(vars_order[OracleVarType.ANSWER.value], var):
                    problems = []  # TODO send some hook to another detector
                    break
        return problems

    def process_not_checked_vars(self):
        result = []
        for oracle in self.oracles:
            if len(oracle.vars_not_in_condition) > 0:
                result.append(
                    "In contract `{}` a function `{}` uses oracle where the values of vars {} are not checked. This can potentially lead to a problem! \n".format(
                        oracle.contract.name,
                        oracle.function.name,
                        [var.name for var in oracle.vars_not_in_condition],
                    )
                )
        return result

    def _detect(self):
        results = []
        super()._detect()
        not_checked_vars = self.process_not_checked_vars()
        res = self.generate_result(not_checked_vars)
        results.append(res)
        for oracle in self.oracles:
            checked_vars = self.naive_check(oracle)
            if len(checked_vars) > 0:
                res = self.generate_result(checked_vars)
                results.append(res)
        # res = self.generate_result(self.process_checked_vars())
        # results.append(res)
        return results
