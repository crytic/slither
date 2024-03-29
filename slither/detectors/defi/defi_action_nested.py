from typing import List
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.output import Output
from slither.core.declarations import Function, Contract
from slither.core.variables.state_variable import StateVariable
from slither.core.declarations import FunctionContract, SolidityVariableComposed, Modifier
from slither.core.cfg.node import NodeType, Node
from slither.core.solidity_types import ArrayType
from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.declarations.solidity_variables import (
    SolidityVariable,
    SolidityVariableComposed,
    SolidityFunction,
)
from slither.core.variables.local_variable import LocalVariable

from slither.core.expressions.assignment_operation import AssignmentOperation

import difflib
from slither.core.declarations import Contract, Function, SolidityVariableComposed

from slither.core.expressions import CallExpression,TypeConversion,Identifier

from slither.slithir.operations import (
    Assignment,
    Binary,
    BinaryType,
    HighLevelCall,
    SolidityCall,
    LibraryCall,
    Index,
)
from slither.visitors.expression.export_values import ExportValues
from slither.core.solidity_types import MappingType, ElementaryType
class DeFiActionNested(AbstractDetector):
    """
    Detect when `msg.sender` is not used as `from` in transferFrom along with the use of permit.
    """

    ARGUMENT = "defi-action-nested"
    HELP = "transferFrom uses arbitrary from with permit"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "http://"

    WIKI_TITLE = "DeFi Action Nesting"
    WIKI_DESCRIPTION = (
        "This detector identifies instances where DeFi actions are nested, specifically focusing on scenarios where `msg.sender` is not used as `from` in transferFrom while also utilizing a permit function."
    )
    WIKI_EXPLOIT_SCENARIO = """
    }"""
    ERC20_FUNCTION = [
    "transferFrom",
    "safeTransferFrom",
    "mint",
    "burn",
    "burnFrom",
    "approve",
    "balanceOf",
    "totalSupply",
    "transfer",
    "allowance",
    "safeTransfer",
    "safeApprove",
    "getReserve",
    "transfer",
    "balance"
]
    UNISWAP_FUNCTION=[
    "_addLiquidity",
    "addLiquidity",
    "addLiquidityETH",
    "removeLiquidity",
    "removeLiquidityETH",
    "removeLiquidityWithPermit",
    "removeLiquidityETHWithPermit",
    "removeLiquidityETHSupportingFeeOnTransferTokens",
    "removeLiquidityETHWithPermitSupportingFeeOnTransferTokens",
    "swapExactTokensForTokens",
    "swapTokensForExactTokens",
    "swapExactETHForTokens",
    "swapTokensForExactETH",
    "swapExactTokensForETH",
    "swapETHForExactTokens",
    "swapExactTokensForTokensSupportingFeeOnTransferTokens",
    "swapExactETHForTokensSupportingFeeOnTransferTokens",
    "swapExactTokensForETHSupportingFeeOnTransferTokens",
    "swap"  
    ]
    depositTransferMatchScore=0.1
    depositAssignementToUserScore=0.1
    withdrawTransferMatchScore=0.1
    withdrawAssignementToUserScore=0.1
    defaultDependencyScore=0.1
    lendingTransferMatchScore=0.1
    lendingAssignementToUserScore=0.1
    liquidateTransferToScore=0.05
    liquidateTransferFromScore=0.05
    def checkIfHavePriceManipulation(self,contract:Contract):
        result=[]
        if contract.is_interface:
            return result
        for function in contract.functions:
            if function.view:
                continue
            name,score=self._check_function_action_type(function)
            if_has,node,info,func=self._check_defi_action_nesting(function)
            if name!="unknown" and if_has and \
                name!=info and \
                function.name not in str(func).lower():
                result.append([function,node,info,func])
            
        return result
    
    # Check defi function nesting
    def _check_defi_action_nesting(self,func):
        if self._check_func_if_have_uniswap(func)[0]:
            return True,self._check_func_if_have_uniswap(func)[1],"UNISWAP ACTION",self._check_func_if_have_uniswap(func)[2]
        for node in func.nodes:
            for call in node.calls_as_expression:
                if call.called and hasattr(call.called,"value"):
                    if self._check_function_action_type(call.called.value)[0]!="unknown":
                        return True,node,self._check_function_action_type(call.called.value)[0],call.called.value
        return False,"unknown","unknown","unknown"
    
    # Check whether func contains uniswap related (self, call):
    def _check_func_if_have_uniswap(self,func):
        for node in func.nodes:
            for call in node.calls_as_expression:
                if call.called and hasattr(call.called,"member_name") and call.called.member_name in self.UNISWAP_FUNCTION:
                    return True,node,call.called.member_name
        return False,"",""

    # Check what function a function is and return the corresponding name
    def _check_function_action_type(self,func):
        list_action=["deposit","lending","withdraw","liquidate","unknown"]
        depositDiffscore,depositTransferScore,depositAssignmentScore,depositDependencyScore=self._check_function_if_staking_or_deposit_or_collateral(func)
        lendingDiffscore,lendingTransferScore,lendingAssignmentScore,lendingDependencyScore=self._check_function_if_lending_or_borrow(func)
        withdrawDiffscore,withdrawTransferScore,withdrawAssignmentScore,withdrawDependencyScore=self._check_function_if_withdraw_or_unstake(func)
        liquidateDiffscore,liquidateTransferScore,liquidateAssignmentScore,liquidateDependencyScore=self._check_function_if_liquidate(func)
        TransferScoreList=[depositTransferScore,lendingTransferScore,withdrawTransferScore,liquidateTransferScore]
        
        list_diffscore=[depositDiffscore,lendingDiffscore,withdrawDiffscore,liquidateDiffscore]
        list_allscore=[
            depositDiffscore+depositTransferScore+depositAssignmentScore+depositDependencyScore,
            lendingDiffscore+lendingTransferScore+lendingAssignmentScore+lendingDependencyScore,
            withdrawDiffscore+withdrawTransferScore+withdrawAssignmentScore+withdrawDependencyScore,
            liquidateDiffscore,liquidateTransferScore+liquidateAssignmentScore+liquidateDependencyScore
        ]# The lower the score, the more output. The reason is that the lower the score, the more functions are matched. At the same time, there must be a transfer behavior.
        if max(list_diffscore)>0.6 and TransferScoreList[list_diffscore.index(max(list_diffscore))]!=0:
            return list_action[list_diffscore.index(max(list_diffscore))],max(list_diffscore)
        elif max(list_allscore)>0.4 and TransferScoreList[list_allscore.index(max(list_allscore))]!=0:
            return list_action[list_allscore.index(max(list_allscore))],max(list_allscore)
        else:
            return list_action[4],max(list_allscore)

    # Checks if a call is an erc20 transfer call from the user, returns yes/no and the call itself
    def _check_call_if_transfer_from_user(self,call,func):
        if call.called and hasattr(call.called,"member_name") and call.called.member_name in ["safeTransferFrom","transferFrom"]:                    
            # The first transfer parameter is msg.sender or the external address passed in
            if (isinstance(call.arguments[0],TypeConversion) and hasattr(call.arguments[0].expression,"value") and isinstance(call.arguments[0].expression.value,SolidityVariable) and call.arguments[0].expression.value.name=="msg.sender") or \
                (isinstance(call.arguments[0],Identifier) and isinstance(call.arguments[0].value,SolidityVariableComposed) and call.arguments[0].value.name=="msg.sender") or \
                (isinstance(call.arguments[0],Identifier) and call.arguments[0].value in func.parameters):
                return True,call.arguments
    
    def _check_call_if_transfer_to_user(self, call, func):
        if call.called and hasattr(call.called, "member_name") and call.called.member_name in ["safeTransfer", "transfer"]:
            # The first transfer parameter is msg.sender or an externally passed address
            if (isinstance(call.arguments[0], TypeConversion) and hasattr(call.arguments[0].expression, 'value') and isinstance(call.arguments[0].expression.value, SolidityVariable) and call.arguments[0].expression.value.name == "msg.sender") or \
                    (isinstance(call.arguments[0], Identifier) and isinstance(call.arguments[0].value, SolidityVariableComposed) and call.arguments[0].value.name == "msg.sender") or \
                    (isinstance(call.arguments[0], Identifier) and call.arguments[0].value in func.parameters):
                return True, call.arguments

    def _check_node_if_mapping_assignment_with_sender_or_param(self, node, func):
        if isinstance(node.expression, AssignmentOperation):
            for ir in node.irs:
                if hasattr(ir, "variables") and any(isinstance(e.type, MappingType) for e in ir.variables):
                    if (hasattr(ir.expression.expression_right, "value")) and (
                            (isinstance(ir.expression.expression_right.value, SolidityVariableComposed) and ir.expression.expression_right.value.name == "msg.sender") or \
                            ir.expression.expression_right.value in func.parameters and isinstance(ir.expression.expression_right.value, LocalVariable) and ir.expression.expression_right.value.type.type == "address"):
                        if hasattr(node, "variables_read") and len(node.variables_read) > 0:
                            return True, set(node.variables_read) - set(ir.variables)

    def _check_function_if_staking_or_deposit_or_collateral(self, func: FunctionContract):
        depositDiffScore = difflib.SequenceMatcher(a="deposit", b=func.name.lower()).ratio()
        stakeDiffScore = difflib.SequenceMatcher(a="stake", b=func.name.lower()).ratio()
        diffscore = depositDiffScore if depositDiffScore > stakeDiffScore else stakeDiffScore

        transferMatchScore = 0
        assignementToUserScore = 0
        dependencyScore = 0
        call_arguments = []
        var_read = []
        if hasattr(func, "nodes"):
            for node in func.nodes:
                for call in node.calls_as_expression:
                    # Check if there is an ERC20 transfer function to a user
                    transfer_ret = self._check_call_if_transfer_from_user(call, func)
                    if transfer_ret is not None and transfer_ret[0]:
                        call_arguments.append(transfer_ret[1])
                        transferMatchScore = self.depositTransferMatchScore
                # Check for array operations, and whether the parameter is msg.sender or an address type parameter in func
                assin_ret = self._check_node_if_mapping_assignment_with_sender_or_param(node, func)
                if assin_ret is not None and assin_ret[0]:
                    var_read.append(assin_ret[1])
                    assignementToUserScore = self.depositAssignementToUserScore
                    # There is data dependency between array operations and transfers
            if self._check_two_arguments_if_dependent(call_arguments, var_read, func):
                dependencyScore = self.defaultDependencyScore

        return diffscore, transferMatchScore, assignementToUserScore, dependencyScore

    def _check_function_if_withdraw_or_unstake(self, func: FunctionContract):
        withdrawDiffScore = difflib.SequenceMatcher(a="withdraw", b=func.name.lower()).ratio()
        unstakeDiffScore = difflib.SequenceMatcher(a="unstake", b=func.name.lower()).ratio()
        diffscore = withdrawDiffScore if withdrawDiffScore > unstakeDiffScore else unstakeDiffScore

        transferMatchScore = 0
        assignementToUserScore = 0
        call_arguments = []
        var_read = []
        dependencyScore = 0
        if hasattr(func, "nodes"):
            for node in func.nodes:
                for call in node.calls_as_expression:
                    # Check if there is an ERC20 transfer function to a user
                    transfer_ret = self._check_call_if_transfer_to_user(call, func)
                    if transfer_ret is not None and transfer_ret[0]:
                        call_arguments.append(transfer_ret[1])
                        transferMatchScore = self.withdrawTransferMatchScore
                # Check for array operations, and whether the parameter is msg.sender or an address type parameter in func
                assin_ret = self._check_node_if_mapping_assignment_with_sender_or_param(node, func)
                if assin_ret is not None and assin_ret[0]:
                    var_read.append(assin_ret[1])
                    assignementToUserScore = self.withdrawAssignementToUserScore
            # There is data dependency between array operations and transfers
            if self._check_two_arguments_if_dependent(call_arguments, var_read, func):
                dependencyScore = self.defaultDependencyScore
        return diffscore, transferMatchScore, assignementToUserScore, dependencyScore

    def _check_function_if_lending_or_borrow(self, func: FunctionContract):
        lendingDiffScore = difflib.SequenceMatcher(a="lending", b=func.name.lower()).ratio()
        borrowDiffScore = difflib.SequenceMatcher(a="borrow", b=func.name.lower()).ratio()
        diffscore = lendingDiffScore if lendingDiffScore > borrowDiffScore else borrowDiffScore

        transferMatchScore = 0
        assignementToUserScore = 0
        call_arguments = []
        var_read = []
        dependencyScore = 0
        if hasattr(func, "nodes"):
            for node in func.nodes:
                for call in node.calls_as_expression:
                    # Check if there is an ERC20 transfer function to a user
                    transfer_ret = self._check_call_if_transfer_to_user(call, func)
                    if transfer_ret is not None and transfer_ret[0]:
                        call_arguments.append(transfer_ret[1])
                        transferMatchScore = self.lendingTransferMatchScore
                # Check for array operations, and whether the parameter is msg.sender or an address type parameter in func
                assin_ret = self._check_node_if_mapping_assignment_with_sender_or_param(node, func)
                if assin_ret is not None and assin_ret[0]:
                    var_read.append(assin_ret[1])
                    assignementToUserScore = self.lendingAssignementToUserScore
            # There is data dependency between array operations and transfers
            if self._check_two_arguments_if_dependent(call_arguments, var_read, func):
                dependencyScore = self.defaultDependencyScore
        return diffscore, transferMatchScore, assignementToUserScore, dependencyScore

    def _check_function_if_liquidate(self, func: FunctionContract):
        liquidateDiffScore = difflib.SequenceMatcher(a="liquidate", b=func.name.lower()).ratio()
        diffscore = liquidateDiffScore

        transferToScore = 0
        transferFromScore = 0

        transferMatchScore = 0
        assignementToUserScore = 0
        call_arguments = []
        var_read = []
        dependencyScore = 0
        if hasattr(func, "nodes"):
            for node in func.nodes:
                for call in node.calls_as_expression:
                    # Check if there is an ERC20 transfer function to a user
                    transfer_to_ret = self._check_call_if_transfer_to_user(call, func)
                    transfer_from_ret = self._check_call_if_transfer_from_user(call, func)
                    if transfer_to_ret is not None and transfer_to_ret[0]:
                        call_arguments.append(transfer_to_ret[1])
                        transferToScore = self.liquidateTransferToScore
                    if transfer_from_ret is not None and transfer_from_ret[0]:
                        call_arguments.append(transfer_from_ret[1])
                        transferFromScore = self.liquidateTransferFromScore

                # Check for array operations, and whether the parameter is msg.sender or an address type parameter in func
                assin_ret = self._check_node_if_mapping_assignment_with_sender_or_param(node, func)
                if assin_ret is not None and assin_ret[0]:
                    var_read.append(assin_ret[1])
                    assignementToUserScore = self.lendingAssignementToUserScore
            # There is data dependency between array operations and transfers
            if self._check_two_arguments_if_dependent(call_arguments, var_read, func):
                dependencyScore = self.defaultDependencyScore
        return diffscore, transferToScore + transferFromScore, assignementToUserScore, dependencyScore

    def _check_two_arguments_if_dependent(self, callArgs, assignArgs, func):
        args = [arg for callArg in callArgs for arg in callArg if isinstance(arg, Identifier)]
        for arg in args:
            if any(var for vars in assignArgs for var in vars if is_dependent(arg.value, var, func)):
                return True

    def _detect(self) -> List[Output]:
        """"""
        results: List[Output] = []
        detection_result = []
        for c in self.contracts:
            detection_result = self.checkIfHavePriceManipulation(c)
        # print("risk in",function.name,"with potential",info,"function:",func)
        for data in detection_result:

            info = [
                data[1],
                " is a potential nested defi action in its father defi action which has the risk of indirectly generating arbitrage space",
                "\n",
            ]
            res = self.generate_result(info)
            results.append(res)

        return results
