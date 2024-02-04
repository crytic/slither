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


class OracleDetector(AbstractDetector):
    def find_oracles(self, contracts: Contract) -> list[Oracle]:
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
                        interface = None
                        oracle_api = None
                        for ir in oracle.node.irs:
                            if isinstance(ir, HighLevelCall):
                                interface = ir.destination
                                oracle_api = ir.function.name
                        idxs = []
                        for idx in oracle_returned_var_indexes:
                            if idx[0] == oracle.node:
                                idxs.append(idx[1])
                        oracle.set_data(contract, function, idxs, interface, oracle_api)
                        oracles.append(oracle)
        return oracles

    def generate_oracle(self, ir: Operation) -> Oracle:
        if ChainlinkOracle().is_instance_of(ir):
            return ChainlinkOracle()
        return None

    # This function was inspired by detector unused return values
    def oracle_call(self, function: FunctionContract):
        used_returned_vars = []
        values_returned = []
        nodes_origin = {}
        oracles = []
        for node in function.nodes:
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

    # Check if the vars occurs in require/assert statement or in conditional node
    def vars_in_conditions(self, oracle: Oracle) -> bool:
        vars_in_condition = []
        vars_not_in_condition = []
        oracle_vars = []

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
                    vars_in_condition.append(VarInCondition(var, self.nodes_with_var))
                    oracle_vars.append(VarInCondition(var, self.nodes_with_var))
            else:
                if self.investigate_internal_call(oracle.function, var):
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
        return None

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
