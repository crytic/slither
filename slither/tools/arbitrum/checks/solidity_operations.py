from slither.core.declarations import SolidityVariableComposed, SolidityFunction
from slither.tools.arbitrum.checks.abstract_checks import (
    AbstractCheck,
    CheckClassification,
)

SOLIDITY_DANGEROUS_VARIABLES = {
    SolidityVariableComposed("tx.gasprice"),
    SolidityVariableComposed("block.coinbase"),
    SolidityVariableComposed("block.difficulty"),
    SolidityVariableComposed("block.gaslimit"),
    SolidityVariableComposed("block.difficulty"),
    SolidityVariableComposed("block.number"),
    SolidityVariableComposed("msg.sender"),
}

SOLIDITY_DANGEROUS_CALL = {
    SolidityFunction("gasleft()"),
    SolidityFunction("blockhash(uint256)"),
}


class SolidityOperations(AbstractCheck):
    ARGUMENT = "were-constant"
    IMPACT = CheckClassification.INFORMATIONAL

    HELP = "Solidity operations that behave differently"
    WIKI = "https://github.com/crytic/slither/wiki/Arbitrum-Checks#solidity-operations"
    WIKI_TITLE = "Solidity operations"

    # region wiki_description
    WIKI_DESCRIPTION = """
Detect Solidity operations that behave differently on Arbitrum.
"""
    # endregion wiki_description

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
"""
    # endregion wiki_exploit_scenario

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """
Review https://developer.offchainlabs.com/docs/solidity_support to ensure all the operations behave as expected.
"""

    # endregion wiki_recommendation

    def _check(self):
        results = []
        for contract in self.compilation_unit.contracts_derived:
            for function in contract.functions:
                intersection = set.intersection(set(function.solidity_variables_read), SOLIDITY_DANGEROUS_VARIABLES)

                for elem in intersection:
                    info = [function, " reads ", str(elem), "\n"]
                    json = self.generate_result(info)
                    results.append(json)

                intersection = set.intersection(set(function.solidity_calls), SOLIDITY_DANGEROUS_CALL)
                for elem in intersection:
                    info = [function, " calls ", str(elem), "\n"]
                    json = self.generate_result(info)
                    results.append(json)

        return results
