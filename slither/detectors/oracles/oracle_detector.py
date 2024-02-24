from typing import List
from slither.analyses.data_dependency.data_dependency import get_dependencies
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract
from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import AbstractDetector
from slither.slithir.operations import HighLevelCall, InternalCall, Operation, Unpack
from slither.slithir.variables import TupleVariable
from slither.detectors.oracles.supported_oracles.oracle import Oracle, VarInCondition
from slither.detectors.oracles.supported_oracles.chainlink_oracle import ChainlinkOracle
from slither.detectors.oracles.supported_oracles.help_functions import is_internal_call
from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.expressions.tuple_expression import TupleExpression


class OracleDetector(AbstractDetector):
    def __init__(self, compilation_unit, slither, logger):
        super().__init__(compilation_unit, slither, logger)
        self.oracles = []
        self.nodes_with_var = []

    # If the node is high level call, return the interface and the function name
    @staticmethod
    def obtain_interface_and_api(node) -> (str, str):
        for ir in node.irs:
            if isinstance(ir, HighLevelCall):
                return ir.destination, ir.function.name
        return None, None

    @staticmethod
    def generate_oracle(ir: Operation) -> Oracle:
        if ChainlinkOracle().is_instance_of(ir):
            return ChainlinkOracle()
        return None

    @staticmethod
    def get_returned_variables_from_oracle(node) -> list:
        written_vars = []
        ordered_vars = []
        for var in node.variables_written:
            written_vars.append(var)
        for exp in node.variables_written_as_expression:
            if isinstance(exp, TupleExpression):
                for v in exp.expressions:
                    for var in written_vars:
                        if str(v) == str(var.name):
                            ordered_vars.append(var)
        if len(ordered_vars) == 0:
            ordered_vars = written_vars
        return ordered_vars

    @staticmethod
    def check_var_condition_match(var, node) -> bool:
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

    @staticmethod
    def map_param_to_var(var, function: FunctionContract):
        for param in function.parameters:
            origin_vars = get_dependencies(param, function)
            for var2 in origin_vars:
                if var2 == var:
                    return param
        return None

    @staticmethod
    def match_index_to_node(indexes, node):
        idxs = []
        for idx in indexes:
            if idx[0] == node:
                idxs.append(idx[1])
        return idxs

    def find_oracles(self, contracts: Contract) -> List[Oracle]:
        """
        Detects off-chain oracle contract and VAR
        """
        oracles = []
        for contract in contracts:
            for function in contract.functions:
                if function.is_constructor:
                    continue
                (
                    returned_oracles,
                    oracle_returned_var_indexes,
                ) = self.oracle_call(function)
                if returned_oracles:
                    for oracle in returned_oracles:
                        (interface, oracle_api) = self.obtain_interface_and_api(oracle.node)
                        idxs = self.match_index_to_node(oracle_returned_var_indexes, oracle.node)
                        oracle.set_data(contract, function, idxs, interface, oracle_api)
                        oracles.append(oracle)
        return oracles

    # This function was inspired by detector unused return values
    def oracle_call(self, function: FunctionContract):
        used_returned_vars = []
        values_returned = []
        nodes_origin = {}
        oracles = []
        for node in function.nodes:  # pylint: disable=too-many-nested-blocks
            for ir in node.irs:
                oracle = self.generate_oracle(ir)
                if oracle:
                    oracle.set_node(node)
                    oracles.append(oracle)
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
        return oracles, returned_vars_used_indexes

    def map_condition_to_var(self, var, function: FunctionContract):
        nodes = []
        for node in function.nodes:
            if node.is_conditional() and self.check_var_condition_match(var, node):
                nodes.append(node)
        return nodes

    # Check if the vars occurs in require/assert statement or in conditional node
    def vars_in_conditions(self, oracle: Oracle):
        # vars_in_condition = []
        vars_not_in_condition = []
        oracle_vars = []
        nodes = []
        for var in oracle.oracle_vars:
            self.nodes_with_var = []
            if oracle.function.is_reading_in_conditional_node(
                var
            ) or oracle.function.is_reading_in_require_or_assert(var):
                self.nodes_with_var = self.map_condition_to_var(var, oracle.function)
                for node in self.nodes_with_var:
                    for ir in node.irs:
                        if isinstance(ir, InternalCall):
                            self.investigate_internal_call(ir.function, var)

                if len(self.nodes_with_var) > 0:
                    # vars_in_condition.append(VarInCondition(var, self.nodes_with_var))
                    oracle_vars.append(VarInCondition(var, self.nodes_with_var))
            else:
                if self.investigate_internal_call(oracle.function, var):
                    # vars_in_condition.append(VarInCondition(var, self.nodes_with_var))
                    oracle_vars.append(VarInCondition(var, self.nodes_with_var))
                elif nodes := self.investigate_on_return(oracle, var):
                    oracle_vars.append(VarInCondition(var, nodes))
                    oracle.out_of_function_checks.append((var, nodes))
                else:
                    vars_not_in_condition.append(var)
                    oracle_vars.append(var)

        # oracle.vars_in_condition = vars_in_condition
        oracle.vars_not_in_condition = vars_not_in_condition
        oracle.oracle_vars = oracle_vars
        return True

    def checks_performed_out_of_original_function(self, oracle, returned_var):
        nodes_of_call = []
        functions_of_call = []
        original_function = oracle.function
        original_node = oracle.node
        for contract in self.contracts:
            for function in contract.functions:
                if function == oracle.function:
                    continue
                nodes, functions = self.find_if_original_function_called(oracle, function)
                if nodes and functions:
                    nodes_of_call.extend(nodes)
                    functions_of_call.extend(functions)
        if not nodes_of_call or not functions_of_call:
            return []

        i = 0
        nodes = []
        for node in nodes_of_call:
            oracle.set_function(functions_of_call[i])
            oracle.set_node(node)
            new_vars = self.get_returned_variables_from_oracle(node)
            for var in new_vars:
                if is_dependent(var, returned_var, node):
                    oracle.oracle_vars = [var]
                    break
            self.vars_in_conditions(oracle)
            if type(oracle.oracle_vars[0]) == VarInCondition:
                nodes.extend(oracle.oracle_vars[0].nodes_with_var)
            i += 1

        # Return back original node and function after recursion to let developer know on which line the oracle is used
        oracle.set_function(original_function)
        oracle.set_node(original_node)
        return nodes

    @staticmethod
    def find_if_original_function_called(oracle, function):
        nodes_of_call = []
        functions_of_call = []
        for node in function.nodes:
            for ir in node.irs:
                if isinstance(ir, (InternalCall, HighLevelCall)):
                    if ir.function == oracle.function:
                        nodes_of_call.append(node)
                        functions_of_call.append(function)
        return nodes_of_call, functions_of_call

    def investigate_on_return(self, oracle, var) -> bool:
        for value in oracle.function.return_values:
            if is_dependent(value, var, oracle.node):
                return self.checks_performed_out_of_original_function(oracle, value)
        return False

    # This function interates through all internal calls in function and checks if the var is used in condition any of them
    def investigate_internal_call(self, function: FunctionContract, var) -> bool:
        if function is None:
            return False

        original_var_as_param = self.map_param_to_var(var, function)
        if original_var_as_param is None:
            original_var_as_param = var

        if function.is_reading_in_conditional_node(
            original_var_as_param
        ) or function.is_reading_in_require_or_assert(original_var_as_param):
            conditions = []
            for node in function.nodes:
                if (
                    node.is_conditional()
                    and self.check_var_condition_match(original_var_as_param, node)
                    and not is_internal_call(node)
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

    def _detect(self):
        self.oracles = self.find_oracles(self.contracts)
        for oracle in self.oracles:
            oracle.oracle_vars = self.get_returned_variables_from_oracle(oracle.node)
            self.vars_in_conditions(oracle)
