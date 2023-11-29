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
from slither.detectors.operations.unused_return_values import UnusedReturnValues
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
        vars_order[OracleVarType.ROUNDID] = None
        vars_order[OracleVarType.ANSWER] = None
        vars_order[OracleVarType.STARTEDAT] = None
        vars_order[OracleVarType.UPDATEDAT] = None
        vars_order[OracleVarType.ANSWEREDINROUND] = None
        return vars_order

    def _is_instance(self, ir: Operation) -> bool:  # pylint: disable=no-self-use
        return (
            isinstance(ir, HighLevelCall)
            and (
                (
                    isinstance(ir.function, Function)
                    and "latestRoundData" in ir.function.name
                )
                or not isinstance(ir.function, Function)
            )
            or ir.node.type == NodeType.TRY
            and isinstance(ir, (Assignment, Unpack))
        )


    def detect_unused_return_values(
        self, f: FunctionContract
    ) -> List[Node]:  # pylint: disable=no-self-use
        """
            Return the nodes where the return value of a call is unused
        Args:
            f (Function)
        Returns:
            list(Node)
        """
        used_returned_vars = []
        values_returned = []
        nodes_origin = {}
        # pylint: disable=too-many-nested-blocks
        for n in f.nodes:
            for ir in n.irs:
                if self._is_instance(ir):
                    # if a return value is stored in a state variable, it's ok
                    if ir.lvalue and not isinstance(ir.lvalue, StateVariable):
                        values_returned.append((ir.lvalue, None))
                        nodes_origin[ir.lvalue] = ir
                        if isinstance(ir.lvalue, TupleVariable):
                            # we iterate the number of elements the tuple has
                            # and add a (variable, index) in values_returned for each of them
                            for index in range(len(ir.lvalue.type)):
                                values_returned.append((ir.lvalue, index))
                for read in ir.read:
                    remove = (read, ir.index) if isinstance(ir, Unpack) else (read, None)
                    if remove in values_returned:
                        used_returned_vars.append(remove) # This is saying which element is used based on the index
                        # this is needed to remove the tuple variable when the first time one of its element is used
                        if remove[1] is not None and (remove[0], None) in values_returned:
                            values_returned.remove((remove[0], None))
                        values_returned.remove(remove)
        output = []
        for (value, index) in used_returned_vars:
            output.append((nodes_origin[value].node, index))
        return output
     
    def find_which_vars_are_used(self, oracle: Oracle):
        vars_order = self.generate_naive_order()
        # ir = oracle.ir
      
        # values_returned = []
        # nodes_origin = {}
        # # print(ir.lvalue)
        # if ir.lvalue and not isinstance(ir.lvalue, StateVariable):
        #     values_returned.append((ir.lvalue, None))
        #     nodes_origin[ir.lvalue] = ir
        #     if isinstance(ir.lvalue, TupleVariable):
        #         for index in range(len(ir.lvalue.type)):
        #             values_returned.append((ir.lvalue, index))
        # else:
        #     print(ir.lvalue)
                    
        # for read in ir.read:
        #     remove = (read, ir.index) if isinstance(ir, Unpack) else (read, None)
        #     if remove in values_returned:
        #                 # this is needed to remove the tuple variable when the first time one of its element is used
        #         if remove[1] is not None and (remove[0], None) in values_returned:
        #             values_returned.remove((remove[0], None))
        #         values_returned.remove(remove)
        # for node in [nodes_origin[value].node for (value, _) in values_returned]:
            # print(node)
            
        
        types_of_used_vars = []
        for var in oracle.oracle_vars:
            if type(var) == VarInCondition:
                types_of_used_vars.append(var.var.type)
            else:     
                types_of_used_vars.append(var.type)
        for i in range(0,len(types_of_used_vars)):
            if types_of_used_vars[i].name == "uint80" and i == 0:
                    vars_order[OracleVarType.ROUNDID] = oracle.oracle_vars[i]
            elif types_of_used_vars[i].name == "int256":
                    vars_order[OracleVarType.ANSWER] = oracle.oracle_vars[i]
            elif types_of_used_vars[i].name == "uint80" and i == len(types_of_used_vars) - 1:
                    vars_order[OracleVarType.ANSWEREDINROUND] = oracle.oracle_vars[i]
            

        


    def naive_check(self, oracle: Oracle):
        self.find_which_vars_are_used(oracle)
        # print([var.var.name for var in ordered_returned_vars])
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
            checks.append(self.naive_check(oracle))
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
        for c in self.compilation_unit.contracts_derived:
            for f in c.functions_and_modifiers:
                unused_return = self.detect_unused_return_values(f)
                if unused_return:
                    for i in unused_return:
                        print(i)
        # self.process_checked_vars()
        # results.append(res)
        # res = self.generate_result(self.process_checked_vars())
        # results.append(res)
        return results