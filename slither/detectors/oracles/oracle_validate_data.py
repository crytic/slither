from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract
from slither.core.expressions import expression
from slither.slithir.operations import Binary, BinaryType
from enum import Enum
from slither.detectors.oracles.oracle import OracleDetector, Oracle, VarInCondition
from slither.detectors.operations.unused_return_values import UnusedReturnValues
from slither.core.cfg.node import NodeType
from slither.core.variables.state_variable import StateVariable

from slither.core.cfg.node import Node, NodeType
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
from typing import List



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
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "RUN"

    WIKI_TITLE = "asda"
    WIKI_DESCRIPTION = "asdsad"
    WIKI_EXPLOIT_SCENARIO = "asdsad"
    WIKI_RECOMMENDATION = "asdsad"

 

    def check_staleness(self, var: VarInCondition):
        if var is None:
            return False
        for node in var.nodes:
            str_node = str(node)
            # print(str_node)
            if "block.timestamp" in str_node: #TODO maybe try something like block.timestamp - updatedAt < b
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
    

    def check_RoundId(self, var: VarInCondition, var2: VarInCondition): # https://solodit.xyz/issues/chainlink-oracle-return-values-are-not-handled-property-halborn-savvy-defi-pdf
        if var is None or var2 is None:
            return False
        for node in var.nodes:
            for ir in node.irs:
                if isinstance(ir, Binary):
                    if ir.type in (BinaryType.GREATER, BinaryType.GREATER_EQUAL):
                        if ir.variable_right == var.var and ir.variable_left == var2.var:
                            return True
                    elif ir.type in (BinaryType.LESS, BinaryType.LESS_EQUAL):
                        if (ir.variable_right == var2.var and ir.variable_left == var.var):
                            return True
                       
        return False
    
    def check_price(self, var: VarInCondition): #TODO I need to divie require or IF
        if var is None:
            return False
        look_for_revert = False
        for node in var.nodes: #TODO testing
            if look_for_revert:
                if node.type == NodeType.THROW:
                    return True
                else:
                    look_for_revert = False
            for ir in node.irs:
                if isinstance(ir, Binary):
                    if ir.type is (BinaryType.GREATER):
                        if (ir.variable_right.value == 0):
                            return True
                    elif ir.type is (BinaryType.LESS):
                        if (ir.variable_left.value == 0):
                            return True
                    elif ir.type is (BinaryType.NOT_EQUAL):
                        if (ir.variable_right.value == 0):
                            return True
                    else:
                        look_for_revert = True
                        

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


    def naive_check(self, oracle: Oracle):
        vars_order = self.find_which_vars_are_used(oracle)
        problems = []
        for (index, var) in vars_order.items():
            if not self.is_needed_to_check_conditions(oracle, var):
                continue
            if index == OracleVarType.ROUNDID.value:
                if not self.check_RoundId(var, vars_order[OracleVarType.ANSWEREDINROUND.value]):
                    problems.append("The RoundID is not checked\n") #TODO add more info
            elif index == OracleVarType.ANSWER.value:
                if not self.check_price(var):
                    problems.append("The price is not checked\n") #TODO add more info
            elif index == OracleVarType.UPDATEDAT.value:
                if not self.check_staleness(var):
                    problems.append("The staleness is not checked\n") #TODO add more info
        return problems
        # checks = {}
        # for i in range(0,5):
        #     checks[i] = False
        # for var in oracle.vars_not_in_condition:

        # for i in range(0,len(ordered_returned_vars)):
        #     if i == OracleVarType.ROUNDID.value:
        #         checks[0] = self.check_RoundId(ordered_returned_vars[i], ordered_returned_vars[-1])
        #     elif i == OracleVarType.ANSWER.value:
        #         checks[1] = self.check_price(ordered_returned_vars[i])
        #     elif i == OracleVarType.UPDATEDAT.value:
        #         checks[3] = self.check_staleness(ordered_returned_vars[i])
        #         print(checks[3])

        # return checks
            
    #          require(
    #       answeredInRound >= roundID,
    #       "Chainlink Price Stale"
    #   );
    #   require(price > 0, "Chainlink Malfunction");
    #   require(updateTime != 0, "Incomplete round");

        # return self.process_checks(checks)
    
    def process_not_checked_vars(self):
        result = []
        for oracle in self.oracles:
            if len(oracle.vars_not_in_condition) > 0:
                result.append("In contract `{}` a function `{}` uses oracle where the values of vars {} are not checked. This can potentially lead to a problem! \n".format(
                        oracle.contract.name,
                        oracle.function.name,
                        [var.name for var in oracle.vars_not_in_condition],
                    ))
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