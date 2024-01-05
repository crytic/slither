from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.declarations.contract import Contract
from slither.core.cfg.node import NodeType
from slither.core.declarations.function_contract import FunctionContract
from slither.core.expressions import expression
from slither.slithir.operations import Binary, BinaryType
from slither.slithir.operations import HighLevelCall
from enum import Enum
from slither.core.cfg.node import Node, NodeType
from slither.core.declarations import Function
from slither.core.declarations.function_contract import FunctionContract
from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import HighLevelCall, Assignment, Unpack, Operation, InternalCall
from slither.slithir.variables import TupleVariable
from slither.slithir.variables.reference import ReferenceVariable
from typing import List
from slither.analyses.data_dependency.data_dependency import is_tainted, get_dependencies

# For debugging
# import debugpy

# # 5678 is the default attach port in the VS Code debug configurations. Unless a host and port are specified, host defaults to 127.0.0.1
# debugpy.listen(5678)
# print("Waiting for debugger attach")
# debugpy.wait_for_client()
# debugpy.breakpoint()
# print('break on this line')


class Oracle:
    def __init__(self, _contract, _function, _node, _line_of_call, _returned_used_vars, _interface):
        self.contract = _contract
        self.function = _function
        self.node = _node
        self.line_of_call = _line_of_call  # can be get by node.source_mapping.lines[0]
        self.oracle_vars = []
        self.vars_in_condition = []
        self.vars_not_in_condition = []
        self.returned_vars_indexes = _returned_used_vars
        self.interface = _interface
        # self.possible_variables_names = [
        #     "price",
        #     "timestamp",
        #     "updatedAt",
        #     "answer",
        #     "roundID",
        #     "startedAt",
        # ]


class VarInCondition:
    def __init__(self, _var, _nodes):
        self.var = _var
        self.nodes_with_var = _nodes


class OracleDetector(AbstractDetector):

    # https://github.com/crytic/slither/wiki/Python-API
    # def detect_stale_price(Function):
    ORACLE_CALLS = [
        "latestRoundData",
        "getRoundData",
    ]  # Calls i found which are generally used to get data from oracles, based on docs. Mostly it is lastestRoundData

    def chainlink_oracles(self, contracts: Contract) -> list[Oracle]:
        """
        Detects off-chain oracle contract and VAR
        """
        oracles = []
        for contract in contracts:
            for function in contract.functions:
                if function.is_constructor:
                    continue
                (
                    oracle_calls_in_function,
                    oracle_returned_var_indexes,
                ) = self.check_chainlink_call(function)
                if oracle_calls_in_function:
                    for node in oracle_calls_in_function:
                        interface = None
                        for ir in node.irs:
                            if isinstance(ir, HighLevelCall):
                                interface = ir.destination
                        idxs = []
                        # if referecne_variable_assigned and isinstance(interface, ReferenceVariable):
                        #     break
                        # if isinstance(interface, ReferenceVariable):
                        #     referecne_variable_assigned = True
                        for idx in oracle_returned_var_indexes:
                            if idx[0] == node:
                                idxs.append(idx[1])
                        # print(node, interface, contract)
                        oracle = Oracle(
                            contract, function, node, node.source_mapping.lines[0], idxs, interface
                        )
                        oracles.append(oracle)
        return oracles

    def compare_chainlink_call(self, function) -> bool:
        for call in self.ORACLE_CALLS:
            if call in str(function):
                return True
        return False

    def _is_instance(self, ir: Operation) -> bool:  # pylint: disable=no-self-use
        return isinstance(ir, HighLevelCall) and (
            isinstance(ir.function, Function) and self.compare_chainlink_call(ir.function.name)
        )

    def check_chainlink_call(self, function: FunctionContract):
        used_returned_vars = []
        values_returned = []
        nodes_origin = {}
        oracle_calls = []
        for node in function.nodes:
            for ir in node.irs:
                if self._is_instance(ir):
                    oracle_calls.append(node)
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
                        used_returned_vars.append(
                            remove
                        )  # This is saying which element is used based on the index
                        # this is needed to remove the tuple variable when the first time one of its element is used
                        if remove[1] is not None and (remove[0], None) in values_returned:
                            values_returned.remove((remove[0], None))
                        values_returned.remove(remove)
        returned_vars_used_indexes = []
        for (value, index) in used_returned_vars:
            returned_vars_used_indexes.append((nodes_origin[value].node, index))
        return oracle_calls, returned_vars_used_indexes

    def get_returned_variables_from_oracle(self, node) -> list:
        written_vars = []
        ordered_vars = []
        for var in node.variables_written:
            written_vars.append(var)
        for exp in node.variables_written_as_expression:
            for v in exp.expressions:
                for var in written_vars:
                    if str(v) == str(var.name):
                        ordered_vars.append(var)
        return ordered_vars

    def check_var_condition_match(self, var, node) -> bool:
        for (
            var2
        ) in (
            node.variables_read
        ):  # This iterates through all variables which are read in node, what means that they are used in condition
            if var is None or var2 is None:
                return False
            if var.name == var2.name:
                return True
        return False

    def map_condition_to_var(self, var, function: FunctionContract):
        nodes = []
        for node in function.nodes:
            if node.is_conditional() and self.check_var_condition_match(var, node):
                nodes.append(node)
        return nodes

    def var_in_function(self, var, function: FunctionContract):

        return False

    def vars_in_conditions(self, oracle: Oracle) -> bool:
        """
        Detects if vars from oracles are in some condition
        """
        vars_in_condition = []
        vars_not_in_condition = []
        oracle_vars = []

        for var in oracle.oracle_vars:
            self.nodes_with_var = []
            if oracle.function.is_reading_in_conditional_node(
                var
            ) or oracle.function.is_reading_in_require_or_assert(
                var
            ):  # These two functions check if within the function some var is in require/assert of in if statement

                self.nodes_with_var = self.map_condition_to_var(var, oracle.function)
                for node in self.nodes_with_var:
                    for ir in node.irs:
                        if isinstance(ir, InternalCall):
                            self.investigate_internal_call(ir.function, var)

                if len(self.nodes_with_var) > 0:
                    vars_in_condition.append(VarInCondition(var, self.nodes_with_var))
                    oracle_vars.append(VarInCondition(var, self.nodes_with_var))
            else:
                if self.investigate_internal_call(
                    oracle.function, var
                ):  # TODO i need to chnge this to check for taint analysis somehow
                    vars_in_condition.append(VarInCondition(var, self.nodes_with_var))
                    oracle_vars.append(VarInCondition(var, self.nodes_with_var))
                else:
                    vars_not_in_condition.append(var)
                    oracle_vars.append(var)

        oracle.vars_in_condition = vars_in_condition
        oracle.vars_not_in_condition = vars_not_in_condition
        oracle.oracle_vars = oracle_vars

    def map_param_to_var(self, var, function: FunctionContract):
        for param in function.parameters:
            origin_vars = get_dependencies(param, function)
            for var2 in origin_vars:
                if var2 == var:
                    return param

    def is_internal_call(self, node):
        for ir in node.irs:
            if isinstance(ir, InternalCall):
                return True
        return False

    def investigate_internal_call(self, function: FunctionContract, var) -> bool:
        if function is None:
            return False

        original_var_as_param = self.map_param_to_var(var, function)
        if original_var_as_param is None:
            return False

        if function.is_reading_in_conditional_node(
            original_var_as_param
        ) or function.is_reading_in_require_or_assert(original_var_as_param):
            conditions = []
            for node in function.nodes:
                if (
                    node.is_conditional()
                    and self.check_var_condition_match(original_var_as_param, node)
                    and not self.is_internal_call(node)
                ):
                    conditions.append(node)
            if len(conditions) > 0:
                for cond in conditions:
                    self.nodes_with_var.append(cond)
                return True

        for node in function.nodes:
            for ir in node.irs:
                if isinstance(ir, InternalCall):
                    if self.investigate_internal_call(ir.function, original_var_as_param):
                        return True
        return False

        # for functionCalled in function.internal_calls:
        #     if isinstance(functionCalled, FunctionContract):
        #         print("functionCalled", functionCalled)
        #         self.nodes_with_var = self.map_condition_to_var(var, functionCalled)
        #         if len(self.nodes_with_var) > 0:
        #             return True
        #         # for local_var in functionCalled.variables_read:
        #         #     if local_var.name == var.name:

        #         #         if functionCalled.is_reading_in_conditional_node(
        #         #             local_var
        #         #         ) or functionCalled.is_reading_in_require_or_assert(
        #         #             local_var
        #         #         ):  # These two functions check if within the function some var is in require/assert of in if statement
        #         #             return True
        #         if self.investigate_internal_call(functionCalled, var):
        #             return True

    def _detect(self):
        info = []
        self.oracles = self.chainlink_oracles(self.contracts)
        for oracle in self.oracles:
            oracle.oracle_vars = self.get_returned_variables_from_oracle(oracle.node)
            self.vars_in_conditions(oracle)
        # for oracle in oracles:
        #     oracle_vars = self.get_returned_variables_from_oracle(
        #         oracle.function, oracle.line_of_call
        #     )
        #     if not self.check_vars(oracle, oracle_vars):
        #         rep = "In contract {} a function {} uses oracle {} where the values of vars {} are not checked \n".format(
        #             oracle.contract.name,
        #             oracle.function.name,
        #             oracle.interface_var,
        #             [var.name for var in oracle.vars_not_in_condition],
        #         )
        #         info.append(rep)
        #     if len(oracle.vars_in_condition) > 0:
        #         for var in self.check_conditions_enough(oracle):
        #             info.append("Problem with {}", var.name)
        # res = self.generate_result(info)

        return []
