from enum import Enum
from slither.detectors.oracles.supported_oracles.oracle import Oracle, VarInCondition
from slither.slithir.operations import (
    Binary,
    BinaryType,
)

from slither.slithir.variables.constant import Constant


CHAINLINK_ORACLE_CALLS = ["latestRoundData","getRoundData",] 
class ChainlinkVars(Enum):
    ROUNDID = 0
    ANSWER = 1
    STARTEDAT = 2
    UPDATEDAT = 3
    ANSWEREDINROUND = 4


class ChainlinkOracle(Oracle):
    def __init__(self):
        super().__init__(CHAINLINK_ORACLE_CALLS)
        self.oracle_type = "Chainlink"


    # This function checks if the updatedAt value is validated.
    def check_staleness(self, var: VarInCondition) -> bool:
        if var is None:
            return False
        for node in var.nodes_with_var:
            str_node = str(node)
            # This is temporarily check which will be improved in the future. Mostly we are looking for block.timestamp and trust the developer that he is using it correctly
            if "block.timestamp" in str_node:
                return True
        return False

    # This function checks if the RoundId value is validated in connection with answeredInRound value
    # But this last variable was deprecated. We left this function for possible future use.
    def check_RoundId(self, var: VarInCondition, var2: VarInCondition) -> bool:
        if var is None or var2 is None:
            return False
        for node in var.nodes_with_var:
            for ir in node.irs:
                if isinstance(ir, Binary):
                    if ir.type in (BinaryType.GREATER, BinaryType.GREATER_EQUAL):
                        if ir.variable_right == var.var and ir.variable_left == var2.var:
                            return True
                    elif ir.type in (BinaryType.LESS, BinaryType.LESS_EQUAL):
                        if ir.variable_right == var2.var and ir.variable_left == var.var:
                            return True
            if self.check_revert(node):
                return True
            elif self.return_boolean(node):
                return True

        return False


    # This functions validates checks of price value
    def check_price(self, var: VarInCondition, oracle: Oracle) -> bool:
        if var is None:
            return False
        for node in var.nodes_with_var:
            for ir in node.irs:
                if isinstance(ir, Binary):
                    if isinstance(ir.variable_right, Constant):
                        if ir.type is (BinaryType.GREATER):
                            if ir.variable_right.value == 0:
                                return True
                        elif ir.type is (BinaryType.NOT_EQUAL):
                            if ir.variable_right.value == 0:
                                return True
                    if isinstance(ir.variable_left, Constant):
                        if ir.type is (BinaryType.LESS):
                            if ir.variable_left.value == 0:
                                return True
                    # If the conditions does not match we are looking for revert or return node
                    if self.check_revert(node):
                        return True
                    elif self.return_boolean(node):
                        return True

        return False

    def generate_naive_order(self):
        vars_order = {}
        vars_order[ChainlinkVars.ROUNDID.value] = None
        vars_order[ChainlinkVars.ANSWER.value] = None
        vars_order[ChainlinkVars.STARTEDAT.value] = None
        vars_order[ChainlinkVars.UPDATEDAT.value] = None
        vars_order[ChainlinkVars.ANSWEREDINROUND.value] = None
        return vars_order

    def find_which_vars_are_used(self, oracle: Oracle):
        vars_order = self.generate_naive_order()
        for i in range(len(oracle.oracle_vars)):
            vars_order[oracle.returned_vars_indexes[i]] = oracle.oracle_vars[i]
        return vars_order

    def is_needed_to_check_conditions(self, oracle, var):
        if isinstance(var, VarInCondition):
            var = var.var
        if var in oracle.vars_not_in_condition:
            return False
        return True

    def is_sequencer_check(self, answer, startedAt):
        if answer is None or startedAt is None:
            return False
        answer_checked = False
        startedAt_checked = False

        for node in answer.nodes:
            for ir in node.irs:
                if isinstance(ir, Binary):
                    if ir.type is (BinaryType.EQUAL):
                        if isinstance(ir.variable_right, Constant):
                            if ir.variable_right.value == 1:
                                answer_checked = True
        startedAt_checked = self.check_staleness(startedAt)
        print(answer_checked, startedAt_checked)

        return answer_checked and startedAt_checked

    def naive_data_validation(self):
        oracle = self
        vars_order = self.find_which_vars_are_used(oracle)
        problems = []
        for (index, var) in vars_order.items():
            if not self.is_needed_to_check_conditions(oracle, var):
                continue
            # if index == ChainlinkVars.ROUNDID.value: # Commented due to deprecation of AnsweredInRound
            #     if not self.check_RoundId(var, vars_order[ChainlinkVars.ANSWEREDINROUND.value]):
            #         problems.append("RoundID value is not checked correctly. It was returned by the oracle call in the function {} of contract {}.\n".format( oracle.function, oracle.node.source_mapping))
            if index == ChainlinkVars.ANSWER.value:
                if not self.check_price(var, oracle):
                    problems.append(
                        f"The price value is validated incorrectly. This value is returned by Chainlink oracle call {oracle.contract}.{oracle.interface}.{oracle.oracle_api} ({oracle.node.source_mapping}).\n"
                    )
            elif index == ChainlinkVars.UPDATEDAT.value:
                if not self.check_staleness(var):
                    problems.append(
                        f"The price can be stale due to incorrect validation of updatedAt value. This value is returned by Chainlink oracle call {oracle.contract}.{oracle.interface}.{oracle.oracle_api} ({oracle.node.source_mapping}).\n"
                    )
            elif (
                index == ChainlinkVars.STARTEDAT.value
                and vars_order[ChainlinkVars.STARTEDAT.value] is not None
            ):
                # If the startedAt is not None. We are checking if the oracle is a sequencer to ignore incorrect results.
                if self.is_sequencer_check(vars_order[ChainlinkVars.ANSWER.value], var):
                    problems = []
                    break
        return problems