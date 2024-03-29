from falcon.core.declarations.function_contract import FunctionContract
from falcon.core.cfg.node import NodeType
from falcon.core.declarations.solidity_variables import SolidityVariableComposed
from falcon.core.expressions.call_expression import CallExpression
from falcon.ir.operations import HighLevelCall, LibraryCall, Binary, BinaryType, Unary, UnaryType, Assignment
from falcon.ir.operations.codesize import CodeSize
from falcon.ir.variables.constant import Constant
from falcon.utils.modifier_utils import ModifierUtil

def function_can_only_initialized_once(fn: FunctionContract):
    if fn.name in ['initialize', 'init']:
        return True
    flag_vars = []
    for node in fn.nodes:
        for ir in node.irs:
            if isinstance(ir, Binary):
                if BinaryType.return_bool(ir.type) and ir.type == BinaryType.NOT_EQUAL:
                    if isinstance(ir.variable_right, Constant) and ir.variable_left == True:
                        flag_vars.append(ir.variable_left)
            elif isinstance(ir, Unary):
                if UnaryType.get_type(str(ir.type).strip(), isprefix=True) == UnaryType.BANG:
                    flag_vars.append(ir.rvalue)
                    # if fn.contract.name == "OKOffChainExchange" and fn.name=="init":
            #             print(ir, ir.lvalue.name, ir.rvalue, type(ir.rvalue), list(map(lambda a: a.name, flag_vars)))
            if len(flag_vars) > 0:
                if isinstance(ir, Assignment):
                    if ir.lvalue.name in list(map(lambda a: a.name, flag_vars)) and isinstance(ir.rvalue,
                                                                                               Constant) and ir.rvalue.value == True:
                        return True
    return False

def function_has_caller_check(fn: FunctionContract):
    hasContractCheck = False
    if ModifierUtil._has_msg_sender_check_new(fn):
        return True
    if fn.is_constructor or fn.is_protected() or fn.pure or fn.view or (not (fn.visibility in ["public", "external"])):
        return True
    for node in fn.all_nodes():
        isContractChecks = [True for ir in node.irs if (
                isinstance(ir, HighLevelCall) or isinstance(ir, LibraryCall)) and ir.function_name == "isContract"]
        if any(isContractChecks) is True:
            hasContractCheck = True
            break
        codeSizingChecks = [True for ir in node.irs if isinstance(ir, CodeSize)]
        if any(codeSizingChecks) is True:
            hasContractCheck = True
            break

        txOriginChecks = [True for ir in node.irs if isinstance(ir, Binary) and ir.type == BinaryType.EQUAL and (
                (str(ir.variable_left) == "tx.origin" and str(ir.variable_right) == "msg.sender") or (
                str(ir.variable_right) == "tx.origin" and str(ir.variable_left) == "msg.sender"))]

        if any(txOriginChecks) is True:
            hasContractCheck = True
            break

        if node.type == NodeType.ASSEMBLY:
            inline_asm = node.inline_asm
            if inline_asm:
                if "extcodesize" in inline_asm:
                    hasContractCheck = True
                    break

    return hasContractCheck
