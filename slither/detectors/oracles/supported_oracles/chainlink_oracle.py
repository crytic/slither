from enum import Enum
from slither.detectors.oracles.supported_oracles.oracle import Oracle, VarInCondition
from slither.slithir.operations import (
    Binary,
    BinaryType,
)
from slither.slithir.variables.constant import Constant


CHAINLINK_ORACLE_CALLS = [
    "latestRoundData",
    "getRoundData",
]
INTERFACES = ["AggregatorV3Interface", "FeedRegistryInterface"]


class ChainlinkVars(Enum):
    ROUNDID = 0
    ANSWER = 1
    STARTEDAT = 2
    UPDATEDAT = 3
    ANSWEREDINROUND = 4


class ChainlinkOracle(Oracle):
    def __init__(self):
        super().__init__(CHAINLINK_ORACLE_CALLS, INTERFACES)

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

        if hasattr(answer, "nodes_with_var"):
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
        # Iterating through all oracle variables which were returned by the oracle call
        for index, var in vars_order.items():
            if not self.is_needed_to_check_conditions(var):
                continue
            # Second variable is the price value
            if index == ChainlinkVars.ANSWER.value:
                if not self.check_price(var):
                    problems.append(
                        f"The price value is validated incorrectly. This value is returned by Chainlink oracle call {self.contract}.{self.interface}.{self.oracle_api} ({self.node.source_mapping}).\n"
                    )
            # Third variable is the updatedAt value, indicating when the price was updated
            elif index == ChainlinkVars.UPDATEDAT.value:
                if not self.check_staleness(var):
                    problems.append(
                        f"The price can be stale due to incorrect validation of updatedAt value. This value is returned by Chainlink oracle call {self.contract}.{self.interface}.{self.oracle_api} ({self.node.source_mapping}).\n"
                    )

            # Fourth variable is the startedAt value, indicating when the round was started.
            # Used in connection with sequencer
            elif (
                index == ChainlinkVars.STARTEDAT.value
                and vars_order[ChainlinkVars.STARTEDAT.value] is not None
            ):
                # If the startedAt is not None. We are checking if the oracle is a sequencer to ignore incorrect results.
                if self.is_sequencer_check(vars_order[ChainlinkVars.ANSWER.value], var):
                    problems = []
                    break
        # Iterate through checks performed out of the function where the oracle call is performed
        for tup in self.out_of_function_checks:
            problems.append(
                f"The variation of {tup[0]} is checked on the lines {[str(node.source_mapping) for node in tup[1][::5]]}. Not in the original function where the Oracle call is performed.\n"
            )
        return problems
