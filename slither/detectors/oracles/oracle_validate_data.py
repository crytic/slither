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

 

    def check_staleness(self, var: VarInCondition):
        for node in var.nodes:
            str_node = str(node)
            print(str_node)
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
        for node in var.nodes:
            for ir in node.irs:
                if isinstance(ir, Binary):
                    if ir.type is (BinaryType.GREATER):
                        if (ir.variable_right.value == 0):
                            return True
                    elif ir.type is (BinaryType.LESS):
                        if (ir.variable_left.value == 0):
                            return True
                    elif ir.type is (BinaryType.NOT_EQUAL):
                        if (ir.variable_left.value == 0 or ir.variable_right.value == 0):
                            return True
                        

        return False

    def naive_check(self, ordered_returned_vars):
        print([var.var.name for var in ordered_returned_vars])
        checks = {}
        for i in range(0,5):
            checks[i] = False
        for i in range(0,len(ordered_returned_vars)):
            if i == OracleVarType.ROUNDID.value:
                checks[0] = self.check_RoundId(ordered_returned_vars[i], ordered_returned_vars[-1])
            elif i == OracleVarType.ANSWER.value:
                checks[1] = self.check_price(ordered_returned_vars[i])
            elif i == OracleVarType.UPDATEDAT.value:
                checks[3] = self.check_staleness(ordered_returned_vars[i])
                print(checks[3])

        return checks

    def process_checks(self,checks):
        result = []
        for check in checks:
            if check[1] == False:
                result.append("Price is not checked well!\n")
            if check[3] == False:
                result.append("The price could be probably stale!\n")
            if check[0] == False:
                result.append("RoundID is not checked well!\n")
        return result
            
    #          require(
    #       answeredInRound >= roundID,
    #       "Chainlink Price Stale"
    #   );
    #   require(price > 0, "Chainlink Malfunction");
    #   require(updateTime != 0, "Incomplete round");

    def process_checked_vars(self):
        checks = []
        for oracle in self.oracles:
            return_vars_num = len(oracle.oracle_vars)
            if return_vars_num >=4:
                checks.append(self.naive_check(oracle.oracle_vars))
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