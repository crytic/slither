# -*- coding:utf-8 -*-
from slither.core.declarations import FunctionContract, SolidityVariableComposed, Modifier
from slither.core.expressions import CallExpression


class ModifierUtil:

    @staticmethod
    def is_reentrancy_lock(modifier: Modifier) -> bool:
        """
        Whether it is a reentrancy lock
        1. There are read and write operations on state variables
        2. There are state variable condition statements (require, if)
        3. There is a placeholder: "_"
        """
        if len(modifier.state_variables_read) <= 0 or len(modifier.state_variables_written) <= 0:
            return False

        if not any(node.type.name == 'PLACEHOLDER' for node in modifier.nodes):
            return False

        return len(modifier.all_conditional_state_variables_read(include_loop=True)) > 0

    @staticmethod
    def _get_function_variables_read_recursively(func: FunctionContract, max_depth=10):
        variables_read = func.variables_read
        if max_depth <= 0:
            return variables_read
        if len(func.calls_as_expressions) > 0:
            for call in func.calls_as_expressions:
                if isinstance(call, CallExpression) and \
                        call.called and hasattr(call.called, 'value') and \
                        isinstance(call.called.value, FunctionContract):
                    variables_read.extend(ModifierUtil._get_function_variables_read_recursively(call.called.value, max_depth=max_depth - 1))
        return variables_read

    @staticmethod
    def _has_msg_sender_check_new(func: FunctionContract):
        for modifier in func.modifiers:
            for var in ModifierUtil._get_function_variables_read_recursively(modifier):
                if isinstance(var, SolidityVariableComposed) and var.name == 'msg.sender':
                    return True
        for var in ModifierUtil._get_function_variables_read_recursively(func):
            if isinstance(var, SolidityVariableComposed) and var.name == 'msg.sender':
                return True
        return False

    @staticmethod
    def _has_msg_sender_check(func: FunctionContract):

        for var in ModifierUtil._get_function_variables_read_recursively(func):
            if isinstance(var, SolidityVariableComposed) and var.name == 'msg.sender':
                return True
        return False

    @staticmethod
    def is_access_control(modifier: Modifier) -> bool:
        """
        Whether there is access control (onlyXXX)
        1. There is a placeholder: "_"
        2. There are read and write operations on state variables
        3. There is a call statement containing msg.sender (require, if)
        """

        # No placeholder exists
        if not any(node.type.name == 'PLACEHOLDER' for node in modifier.nodes):
            return False
        # There are read and write operations on state variables
        if len(modifier.all_conditional_state_variables_read(include_loop=True)) < 0:
            return False
        if not ModifierUtil._has_msg_sender_check(modifier):
            return False
        return True

    @staticmethod
    def check_all_modifiers_if_access_controll(func: FunctionContract):
        for mod in func.modifiers:
            if ModifierUtil.is_access_control(mod):
                return True
        return False
