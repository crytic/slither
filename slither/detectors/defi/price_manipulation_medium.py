from typing import List
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.output import Output
from slither.core.declarations import Contract
from slither.core.variables.state_variable import StateVariable
from slither.core.declarations import FunctionContract, Modifier
from slither.core.cfg.node import NodeType, Node
from slither.core.declarations.event import Event
from slither.core.expressions import CallExpression, Identifier
from slither.analyses.data_dependency.data_dependency import is_dependent

from slither.core.declarations.solidity_variables import (
    SolidityFunction,
)
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable

from slither.core.expressions import CallExpression
from slither.core.expressions.assignment_operation import AssignmentOperation

from slither.slithir.operations import (
    EventCall,
)
from slither.detectors.defi.price_manipulation_tools import PriceManipulationTools


class PriceManipulationMedium(AbstractDetector):
    """
    Detect when `msg.sender` is not used as `from` in transferFrom along with the use of permit.
    """

    ARGUMENT = "price-manipulation-medium"
    HELP = "transferFrom uses arbitrary from with permit"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = " https://metatrust.feishu.cn/wiki/wikcnley0RNMaoaSzdjcCpYxYoD"

    WIKI_TITLE = "The risk of price manipulation in DeFi projects"
    WIKI_DESCRIPTION = (
        "Price manipulation is a common attack in DeFi projects. "
    )
    WIKI_EXPLOIT_SCENARIO = """"""

    WIKI_RECOMMENDATION = """"""
    # Functions that may return abnormal values due to price manipulation
    ERC20_FUNCTION = [
    "balanceOf(address)",
    "balanceOf",
    # "totalSupply",
    # "getReserves",
    "balance",
    # "getAmountsOut",
    # "getAmountOut"
]
    def checkIfHavePriceManipulation(self,contract:Contract):
        result_dependent_data=[]
        result_call_data=[]
        if contract.is_interface:
            return result_call_data,result_dependent_data
        for function in contract.functions:
            return_vars=[]
            # Set 1: Get all sensitive functions related to fund transfer and their associated variables DANGEROUS_ERC20_FUNCTION
            dangerous_calls=self._get_all_dangerous_operation_variables(function)
            # Set 4: All assigned variables and their associated underlying ERC20 operations in the function
            erc20_vars=[]
            erc20_calls=[]
            erc20_nodes=[]
            for node in function.nodes:
                # Get variables and all associated underlying ERC20 operations from the node
                node_vars,node_calls=self._get_calls_and_var_recursively_node(node)
                if len(node_vars)>0:
                    erc20_vars.append(node_vars)
                    erc20_calls.append(node_calls)
                    erc20_nodes.append(node)
            # Check if there are dependencies between variables in Set 1 and Set 4
            all_risk_vars = [arg.value for call in dangerous_calls for arg in call.arguments if isinstance(arg,Identifier) and (isinstance(arg.value,LocalVariable) or isinstance(arg.value,StateVariable))]
            for risk_var in all_risk_vars:
                for dangerous_erc20_vars,dangerous_erc20_calls,node in zip(erc20_vars,erc20_calls,erc20_nodes):
                    for dangerous_erc20_var,dangerous_erc20_call in zip(dangerous_erc20_vars,dangerous_erc20_calls):
                        if is_dependent(risk_var, dangerous_erc20_var, function):
                            result_dependent_data.append([function,risk_var,dangerous_erc20_var,dangerous_erc20_call,node])
                            # print("risk variable in",function.name,":",risk_var.canonical_name,"rely on",dangerous_erc20_var.canonical_name,"with call:",dangerous_erc20_call)
        return result_dependent_data,result_call_data

    # Get all sensitive operations related to transfer and mint in the function
    @staticmethod
    def _get_all_dangerous_operation_variables(func:FunctionContract):
        ret_calls=[]
        ret_vars=[]
        for call in func.calls_as_expressions:
            if (call.called and hasattr(call.called,"member_name") and call.called.member_name in PriceManipulationTools.DANGEROUS_ERC20_FUNCTION) or \
                (call.called and hasattr(call.called,"value") and call.called.value.name in PriceManipulationTools.DANGEROUS_ERC20_FUNCTION):
                ret_calls.append(call)
        return ret_calls

    # Get all return variables in the function
    @staticmethod
    def _get_all_return_variables(func:FunctionContract):
        ret=[]
        for node in func.nodes:
            if node.will_return and len(node.variables_read)>0:
                ret.extend(node.variables_read)
        ret.extend(func.returns)
        return ret
    
    # Get all sensitive function calls in the return statements
    @staticmethod
    def _get_all_return_calls(func:FunctionContract):
        ret_calls=[]
        for node in func.nodes:
            if node.will_return and "require" not in str(node) and hasattr(node,"calls_as_expression") and len(node.calls_as_expression)>0:
                _,calls=PriceManipulationMedium._get_calls_and_var_recursively_node(node)

                for call in calls:
                    if isinstance(call,SolidityFunction):
                        ret_calls.append((call,node))
                    elif hasattr(call,"called") and \
                        ((call.called and hasattr(call.called,"member_name") and call.called.member_name in PriceManipulationMedium.ERC20_FUNCTION) or \
                        (call.called and hasattr(call.called,"value") and call.called.value.name in PriceManipulationMedium.ERC20_FUNCTION)):
                        ret_calls.append((call,node))
        return ret_calls
    
    # Get all assignment operations from the function
    @staticmethod
    def _get_all_assignment_for_variables(func:FunctionContract):
        variable_assignment=[]
        for node in func.nodes:
            if isinstance(node.expression,AssignmentOperation):
                variable_assignment=node.variables_written
            if hasattr(node,"calls_as_expression") and len(node.calls_as_expression) > 0:
                pass
    
    
    
    # Get all underlying erc20 balance and getreserve sub-calls from the node
    @staticmethod
    def _get_calls_and_var_recursively_node(node: NodeType):
        # Sub-calls
        ret_calls=[]
        # Variables related to balance
        ret_vars=[]
        variable_writtens=[]
        if isinstance(node.expression,AssignmentOperation):
            variable_writtens=node.variables_written # If there's variable written, save it
            # If it's used for calculating token difference between before and after, return without considering
            for var in variable_writtens:
                if var is None:
                    continue
                if "before" in str(var.name).lower() or "after" in str(var.name).lower():
                    return [],[]            
        # If the node uses call for variable writing, output all associated calls of this node, including erc20 and others
        if hasattr(node,"calls_as_expression") and len(node.calls_as_expression) > 0:
                for call in node.calls_as_expression:
                    if PriceManipulationMedium._check_call_can_output(call):
                        if call.called.value.full_name in PriceManipulationMedium.ERC20_FUNCTION:
                            # Do not consider balanceOf(address(this))
                            if len(call.arguments)==1 and not str(call.arguments[0]) in ["address(this)"]:
                                ret_calls.append(PriceManipulationMedium._check_if_can_output_call_info(call))
                        else:
                            ret_calls.extend(PriceManipulationMedium._get_calls_recursively(call.called.value))
                    if call.called and hasattr(call.called,"member_name") and call.called.member_name in PriceManipulationMedium.ERC20_FUNCTION:
                        # Do not consider balanceOf(address(this))
                        if len(call.arguments)==1 and not str(call.arguments[0]) in ["address(this)"]:
                            ret_calls.append(PriceManipulationMedium._check_if_can_output_call_info(call))
        # Includes all address.balance
        # Excludes address(this)
        if len(node.internal_calls) > 0 and "address(this)" not in str(node):
            for call in node.internal_calls:
                if call.name=="balance(address)":
                    ret_calls.append(call)
        return variable_writtens,ret_calls
    
    # Recursive function to get sub-calls of the function
    @staticmethod
    def _get_calls_recursively(func: FunctionContract, maxdepth=10):
        ret=[]
        if maxdepth<=0:
            return ret
        if hasattr(func,"calls_as_expressions"):
            if len(func.calls_as_expressions) > 0:
                for call in func.calls_as_expressions:
                    if PriceManipulationMedium._check_call_can_output(call):
                        if str(call.called.value) in PriceManipulationMedium.ERC20_FUNCTION:
                            if len(call.arguments)==1 and not str(call.arguments[0]) in ["address(this)","msg.sender"]:
                                ret.append(PriceManipulationMedium._check_if_can_output_call_info(call))
                        else:
                            ret.extend(PriceManipulationMedium._get_calls_recursively(call.called.value,maxdepth=maxdepth-1))
                    elif isinstance(call, CallExpression) and \
                    call.called and not hasattr(call.called, 'value'):
                        # When there's external call, only consider ERC20's external call, ignore others
                        # This could be extended to include other calls to ensure no issues with external project returns or check potential issues
                        if hasattr(call.called,"member_name") and call.called.member_name in PriceManipulationMedium.ERC20_FUNCTION:
                            if len(call.arguments)==1 and not str(call.arguments[0]) in ["address(this)","msg.sender"]:
                                ret.append(PriceManipulationMedium._check_if_can_output_call_info(call))
        return ret


    @staticmethod
    def _check_call_can_output(call):
        return isinstance(call, CallExpression) and \
                call.called and hasattr(call.called, 'value') and \
                isinstance(call.called.value, FunctionContract) and \
                not isinstance(call.called.value,Modifier) and \
                not isinstance(call.called.value, Event)
    
    @staticmethod
    def _check_if_can_output_call_info(call):
        argument=call.arguments[0]
            # balanceOf(a)
        if (hasattr(argument,"value") and (isinstance(argument.value,StateVariable)) or \
            "pair" in str(argument).lower()) or \
            (hasattr(argument,"expression") and hasattr(argument.expression,"value") and \
            ((isinstance(argument.expression.value,StateVariable)) or "pair" in str(argument.expression.value).lower())):
            return call

    def _check_contract_if_uniswap_fork(self,contract:Contract):
        if set(PriceManipulationTools.UNISWAP_PAIR_FUNCTION).issubset(set(contract.functions_declared)) or set(PriceManipulationTools.UNISWAP_ROUTER_FUNCTION).issubset(set(contract.functions_declared)):
            return True
        return False

    def _detect(self) -> List[Output]:
        """"""
        results: List[Output] = []
        result_dependent_data=[]
        result_call_data=[]
        info=[]
        for c in self.contracts:
            if c.name in PriceManipulationTools.SAFECONTRACTS:
                continue
            if c.is_interface:
                continue
            if self._check_contract_if_uniswap_fork(c):
                continue
            if any(router_name in c.name for router_name in ["Router","router"]):
                continue
            result_dependent_data,result_call_data=self.checkIfHavePriceManipulation(c)
            exist_node=[]
            if len(result_dependent_data)>0 or len(result_call_data)>0:
                info = ["Potential price manipulation risk:\n"]
                # print("risk variable in",function.name,":",risk_var.canonical_name,"rely on",dangerous_erc20_var.canonical_name,"with call:",dangerous_erc20_call)
                # data[4] is the actual problematic node, remove duplicates based on data[4]
                for data in result_dependent_data:
                    if data[4] not in exist_node and not any(isinstance(ir,EventCall) for ir in data[4].irs):
                        info += ["\t- In function ",str(data[0]),"\n",
                            "\t\t-- ",data[4]," have potential price manipulated risk from ",str(data[2])," and call ",str(data[3])," which could influence variable:",str(data[1]),"\n"
                        ]
                        exist_node.append(data[4])
                        
                # print("return call in",function.name,":",str(call[0]),"in return is dangerous")
                # Remove duplicates based on call[2]
                for call in result_call_data:
                    if call[2] not in exist_node and not any(isinstance(ir,EventCall) for ir in call[2].irs):
                        info += ["\t- In function ",str(call[0]),"\n",
                            "\t\t-- ",call[2],"have potential price manipulated risk in return call ",str(call[1])," could influence return value\n"
                        ]
                        exist_node.append(call[2])
                res=self.generate_result(info)
                results.append(res)
        return results
