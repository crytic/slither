from enum import Enum
from slither.detectors.oracles.supported_oracles.oracle import Oracle, VarInCondition
from slither.slithir.operations import (
    Binary,
    BinaryType,
)

from slither.slithir.variables.constant import Constant
from slither.detectors.oracles.supported_oracles.help_functions import check_revert, return_boolean


CHAINLINK_ORACLE_CALLS = [
    "latestRoundData",
    "getRoundData",
]


class ChainlinkVars(Enum):
    ROUNDID = 0
    ANSWER = 1
    STARTEDAT = 2
    UPDATEDAT = 3
    ANSWEREDINROUND = 4


class ChainlinkOracle(Oracle):
    def __init__(self):
        super().__init__(CHAINLINK_ORACLE_CALLS)

    # This function checks if the RoundId value is validated in connection with answeredInRound value
    # But this last variable was deprecated. We left this function for possible future use.
    @staticmethod
    def check_RoundId(var: VarInCondition, var2: VarInCondition) -> bool:
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
            return check_revert(node) or return_boolean(node)

        return False

    @staticmethod
    def generate_naive_order():
        vars_order = {}
        vars_order[ChainlinkVars.ROUNDID.value] = None
        vars_order[ChainlinkVars.ANSWER.value] = None
        vars_order[ChainlinkVars.STARTEDAT.value] = None
        vars_order[ChainlinkVars.UPDATEDAT.value] = None
        vars_order[ChainlinkVars.ANSWEREDINROUND.value] = None
        return vars_order

    def find_which_vars_are_used(self):
        vars_order = self.generate_naive_order()
        for i in range(len(self.oracle_vars)):  # pylint: disable=consider-using-enumerate
            vars_order[self.returned_vars_indexes[i]] = self.oracle_vars[i]
        return vars_order

    def is_needed_to_check_conditions(self, var):
        if isinstance(var, VarInCondition):
            var = var.var
        if var in self.vars_not_in_condition:
            return False
        return True

    @staticmethod
    def price_check_for_liveness(ir: Binary) -> bool:
        if ir.type is (BinaryType.EQUAL):
            if isinstance(ir.variable_right, Constant):
                if ir.variable_right.value == 1:
                    return True
        return False

    def is_sequencer_check(self, answer, startedAt):
        if answer is None or startedAt is None:
            return False
        answer_checked = False
        startedAt_checked = False

        for node in answer.nodes_with_var:
            for ir in node.irs:
                if isinstance(ir, Binary):
                    if self.price_check_for_liveness(ir):
                        answer_checked = True
        startedAt_checked = self.check_staleness(startedAt)

        return answer_checked and startedAt_checked

    def naive_data_validation(self):
        vars_order = self.find_which_vars_are_used()
        problems = []
        for (index, var) in vars_order.items():
            if not self.is_needed_to_check_conditions(var):
                continue
            # if index == ChainlinkVars.ROUNDID.value: # Commented due to deprecation of AnsweredInRound
            #     if not self.check_RoundId(var, vars_order[ChainlinkVars.ANSWEREDINROUND.value]):
            #         problems.append("RoundID value is not checked correctly. It was returned by the oracle call in the function {} of contract {}.\n".format( oracle.function, oracle.node.source_mapping))
            if index == ChainlinkVars.ANSWER.value:
                if not self.check_price(var):
                    problems.append(
                        f"The price value is validated incorrectly. This value is returned by Chainlink oracle call {self.contract}.{self.interface}.{self.oracle_api} ({self.node.source_mapping}).\n"
                    )
            elif index == ChainlinkVars.UPDATEDAT.value:
                if not self.check_staleness(var):
                    problems.append(
                        f"The price can be stale due to incorrect validation of updatedAt value. This value is returned by Chainlink oracle call {self.contract}.{self.interface}.{self.oracle_api} ({self.node.source_mapping}).\n"
                    )

            elif (
                index == ChainlinkVars.STARTEDAT.value
                and vars_order[ChainlinkVars.STARTEDAT.value] is not None
            ):
                # If the startedAt is not None. We are checking if the oracle is a sequencer to ignore incorrect results.
                if self.is_sequencer_check(vars_order[ChainlinkVars.ANSWER.value], var):
                    problems = []
                    break
        for tup in self.out_of_function_checks:
            problems.append(
                f"The variation of {tup[0]} is checked on the lines {[str(node.source_mapping) for node in tup[1][::5]]}. Not in the original function where the Oracle call is performed.\n"
            )
        return problems
