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


class PriceManipulationLow(AbstractDetector):
    """
    Detect when `msg.sender` is not used as `from` in transferFrom along with the use of permit.
    """

    ARGUMENT = "price-manipulation-low"
    HELP = "transferFrom uses arbitrary from with permit"
    IMPACT = DetectorClassification.LOW
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
    # "balanceOf",
    # "totalSupply",
    "getReserves",
    # "balance",
    "getAmountsOut",
    "getAmountOut"
]
    def checkIfHavePriceManipulation(self,contract:Contract):
        result_dependent_data=[]
        result_call_data=[]
        if contract.is_interface:
            return result_call_data,result_dependent_data
        for function in contract.functions:
            return_vars=[]
            # Collection 2: Get all variables involved in function returns
            return_vars=self._get_all_return_variables(function)
            # Collection 3: Get all ERC20 operations involved in function returns
            return_calls=self._get_all_return_calls(function)
            # Collection 4: Variables assigned in the function along with associated ERC20 operations
            erc20_vars=[]
            erc20_calls=[]
            erc20_nodes=[]
            for node in function.nodes:
                # Get variables assigned in the node and all associated ERC20 operations
                node_vars,node_calls=self._get_calls_and_var_recursively_node(node)
                if len(node_calls)>0:
                    erc20_vars.append(node_vars)
                    erc20_calls.append(node_calls)
                    erc20_nodes.append(node)
            # Check if variables in Collection 2 and Collection 4 are dependent
            # All sensitive variables in the function
            all_risk_vars=[]
            if return_vars is not None:
                all_risk_vars.extend(return_vars)
            for risk_var in all_risk_vars:
                for dangerous_erc20_vars,dangerous_erc20_calls,node in zip(erc20_vars,erc20_calls,erc20_nodes):
                    for dangerous_erc20_var,dangerous_erc20_call in zip(dangerous_erc20_vars,dangerous_erc20_calls):
                        if is_dependent(risk_var, dangerous_erc20_var, function):
                            result_dependent_data.append([function,risk_var,dangerous_erc20_var,dangerous_erc20_call,node])
            # Output Collection 3
            for call in return_calls:
                result_call_data.append([function,call[0],call[1]])
        return result_dependent_data,result_call_data

    # Recursively get the child calls of a function
    @staticmethod
    def _get_calls_recursively(func: FunctionContract, maxdepth=10):
        ret=[]
        if maxdepth<=0:
            return ret
        if hasattr(func,"calls_as_expressions"):
            if len(func.calls_as_expressions) > 0:
                for call in func.calls_as_expressions:
                    if PriceManipulationLow._check_call_can_output(call):
                        if str(call.called.value) in PriceManipulationLow.ERC20_FUNCTION:
                            if not (len(call.arguments)==1 and str(call.arguments[0])=="address(this)"):
                                ret.append(call)
                        else:
                            ret.extend(PriceManipulationLow._get_calls_recursively(call.called.value,maxdepth=maxdepth-1))
                    elif isinstance(call, CallExpression) and \
                    call.called and not hasattr(call.called, 'value'):
                        # When there is an external call, only consider ERC20 balanceof and similar calls
                        if hasattr(call.called,"member_name") and call.called.member_name in PriceManipulationLow.ERC20_FUNCTION:
                            if not (len(call.arguments)==1 and str(call.arguments[0])=="address(this)"):
                                ret.append(call)
        return ret

    @staticmethod
    def _check_if_can_output_call_info(call):
        argument=call.arguments[0]
            # balanceOf(a)
        if (hasattr(argument,"value") and (isinstance(argument.value,StateVariable)) or "pair" in str(argument).lower()) or (hasattr(argument,"expression") and hasattr(argument.expression,"value") and (isinstance(argument.expression.value,StateVariable)) or "pair" in str(argument.expression.value).lower()):
            return call

    # Get all sensitive operations related to transfer and minting in a function
    @staticmethod
    def _get_all_dangerous_operation_variables(func:FunctionContract):
        ret_calls=[]
        ret_vars=[]
        for call in func.calls_as_expressions:
            if (call.called and hasattr(call.called,"member_name") and call.called.member_name in PriceManipulationTools.DANGEROUS_ERC20_FUNCTION) or \
                (call.called and hasattr(call.called,"value") and call.called.value.name in PriceManipulationTools.DANGEROUS_ERC20_FUNCTION):
                ret_calls.append(call)
        return ret_calls

    # Get all variables returned in a function
    @staticmethod
    def _get_all_return_variables(func:FunctionContract):
        ret=[]
        for node in func.nodes:
            if node.will_return and len(node.variables_read)>0:
                ret.extend(node.variables_read)
        ret.extend(func.returns)
        return ret
    
    # Get all sensitive function calls returned in a function
    @staticmethod
    def _get_all_return_calls(func:FunctionContract):
        ret_calls=[]
        for node in func.nodes:
            if node.will_return and "require" not in str(node) and hasattr(node,"calls_as_expression") and len(node.calls_as_expression)>0:
                _,calls=PriceManipulationLow._get_calls_and_var_recursively_node(node)

                for call in calls:
                    if isinstance(call,SolidityFunction):
                        ret_calls.append((call,node))
                    elif hasattr(call,"called") and \
                        ((call.called and hasattr(call.called,"member_name") and call.called.member_name in PriceManipulationLow.ERC20_FUNCTION) or \
                        (call.called and hasattr(call.called,"value") and call.called.value.name in PriceManipulationLow.ERC20_FUNCTION)):
                        ret_calls.append((call,node))
        return ret_calls
    
    # Get all assignment operations from a function
    @staticmethod
    def _get_all_assignment_for_variables(func:FunctionContract):
        variable_assignment=[]
        for node in func.nodes:
            if isinstance(node.expression,AssignmentOperation):
                variable_assignment=node.variables_written
            if hasattr(node,"calls_as_expression") and len(node.calls_as_expression) > 0:
                pass
    
    
    
    # Get all child calls related to ERC20 balance and getreserve from a node
    @staticmethod
    def _get_calls_and_var_recursively_node(node: NodeType):
        # Child calls
        ret_calls=[]
        # Variables related to balance
        ret_vars=[]
        variable_writtens=[]
        if isinstance(node.expression,AssignmentOperation):
            variable_writtens=node.variables_written # Save the written variable if exists
            # If it's for calculating token difference before and after, directly return
            for var in variable_writtens:
                if var is None:
                    continue
                if "before" in str(var.name).lower() or "after" in str(var.name).lower():
                    return [],[]            
        # If the node uses call for variable writing, output all associated calls of this node, including ERC20 and others
        if hasattr(node,"calls_as_expression") and len(node.calls_as_expression) > 0:
                for call in node.calls_as_expression:
                    if PriceManipulationLow._check_call_can_output(call):
                        if call.called.value.full_name in PriceManipulationLow.ERC20_FUNCTION:
                            # Do not consider balanceOf(address(this))
                            if not (len(call.arguments)==1 and str(call.arguments[0])=="address(this)"):
                                ret_calls.append(call)
                        else:
                            ret_calls.extend(PriceManipulationLow._get_calls_recursively(call.called.value))
                    if call.called and hasattr(call.called,"member_name") and call.called.member_name in PriceManipulationLow.ERC20_FUNCTION:
                        # Do not consider balanceOf(address(this))
                        if not (len(call.arguments)==1 and str(call.arguments[0])=="address(this)"):
                            ret_calls.append(call)
        return variable_writtens,ret_calls
    
    @staticmethod
    def _check_call_can_output(call):
        return isinstance(call, CallExpression) and \
                call.called and hasattr(call.called, 'value') and \
                isinstance(call.called.value, FunctionContract) and \
                not isinstance(call.called.value,Modifier) and \
                not isinstance(call.called.value, Event)
    
    
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
                # data[4] is the actual node that may have issues, deduplicate based on data[4]
                for data in result_dependent_data:
                    if data[4] not in exist_node and not any(isinstance(ir,EventCall) for ir in data[4].irs):
                        info += ["\t- In function ",str(data[0]),"\n",
                            "\t\t-- ",data[4]," have potential price manipulated risk from ",str(data[2])," and call ",str(data[3])," which could influence variable:",str(data[1]),"\n"
                        ]
                        exist_node.append(data[4])
                        
                # Deduplicate based on call[2]
                for call in result_call_data:
                    if call[2] not in exist_node and not any(isinstance(ir,EventCall) for ir in call[2].irs):
                        info += ["\t- In function ",str(call[0]),"\n",
                            "\t\t-- ",call[2],"have potential price manipulated risk in return call ",str(call[1])," could influence return value\n"
                        ]
                        exist_node.append(call[2])
                res=self.generate_result(info)
                results.append(res)
        return results
