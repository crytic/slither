from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract
from slither.core.expressions import expression
from slither.slithir.operations import Binary, BinaryType
from enum import Enum
from slither.detectors.oracles.oracle import OracleDetector, Oracle, VarInCondition
from slither.detectors.operations.unused_return_values import UnusedReturnValues


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

 


    def check_conditions_enough(self, oracle: Oracle) -> bool:
        checks_not_enough = []
        for var in oracle.vars_in_condition:
            for node in oracle.function.nodes:
                if node.is_conditional() and self.check_var_condition_match(var, node):
                    # print(node.slithir_generation)
                    self.check_condition(node)
                    # for ir in node.irs:
                    #     if isinstance(ir, Binary):
                    #         print(ir.type)
                    #         print(ir.variable_left)
                    #         print(ir.variable_right)
                    # print("-----------")

        return checks_not_enough


        return False
    def check_staleness(self, var: VarInCondition):
        for node in var.nodes:
            str_node = str(node)
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
    
    def check_price(self, var: VarInCondition):
        for node in var.nodes:
            for ir in node.irs:
                if isinstance(ir, Binary):
                    if ir.type in (BinaryType.GREATER, BinaryType.NOT_EQUAL):
                        if (ir.variable_right.value == 0):
                            return True
                        

        return False

    def naive_check(self, ordered_returned_vars):
        checks = {}
        for i in range(0,5):
            checks[i] = False
        for i in range(0,len(ordered_returned_vars)):
            if i == OracleVarType.ROUNDID.value:
                pass
            elif i == OracleVarType.ANSWER.value:
                checks[1] = self.check_price(ordered_returned_vars[i])
            elif i == OracleVarType.STARTEDAT.value:
                pass
            elif i == OracleVarType.UPDATEDAT.value:
                checks[3] = self.check_staleness(ordered_returned_vars[i])
            else:
                pass
        return checks

    def process_checks(self,checks):
        result = []
        if checks[1] == False:
            result.append("Price is not checked well!\n")
        if checks[3] == False:
            result.append("The price could be probably stale\n")
        return result
            
    #          require(
    #       answeredInRound >= roundID,
    #       "Chainlink Price Stale"
    #   );
    #   require(price > 0, "Chainlink Malfunction");
    #   require(updateTime != 0, "Incomplete round");

    def process_checked_vars(self):
        for oracle in self.oracles:
            return_vars_num = len(oracle.oracle_vars)
            if return_vars_num >=4:
                checks = self.naive_check(oracle.oracle_vars)
        return self.process_checks(checks)
    def process_not_checked_vars(self):
        result = []
        for oracle in self.oracles:
            if len(oracle.vars_not_in_condition) > 0:
                result.append("In contract `{}` a function `{}` uses oracle `{}` where the values of vars {} are not checked. This can potentially lead to a problem! \n".format(
                        oracle.contract.name,
                        oracle.function.name,
                        oracle.interface_var,
                        [var.name for var in oracle.vars_not_in_condition],
                    ))
        return result


    def _detect(self):
        results = []
        super()._detect()
        not_checked_vars = self.process_not_checked_vars()
        self.process_checked_vars()
        res = self.generate_result(not_checked_vars)
        results.append(res)
        res = self.generate_result(self.process_checked_vars())
        results.append(res)
        return results