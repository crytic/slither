"""
Module detecting redundant statements.
"""
from typing import List

from slither.core.cfg.node import Node, NodeType
from slither.core.declarations.contract import Contract
from slither.core.expressions.elementary_type_name_expression import ElementaryTypeNameExpression
from slither.core.expressions.identifier import Identifier
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output


class RedundantStatements(AbstractDetector):
    """
    Use of Redundant Statements
    """

    ARGUMENT = "redundant-statements"
    HELP = "Redundant statements"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#redundant-statements"

    WIKI_TITLE = "Redundant Statements"
    WIKI_DESCRIPTION = "Detect the usage of redundant statements that have no effect."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract RedundantStatementsContract {

    constructor() public {
        uint; // Elementary Type Name
        bool; // Elementary Type Name
        RedundantStatementsContract; // Identifier
    }

    function test() public returns (uint) {
        uint; // Elementary Type Name
        assert; // Identifier
        test; // Identifier
        return 777;
    }
}
```
Each commented line references types/identifiers, but performs no action with them, so no code will be generated for such statements and they can be removed."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Remove redundant statements if they congest code but offer no value."

    # This is a disallowed list of tuple (node.type, type(node.expression))
    REDUNDANT_TOP_LEVEL_EXPRESSIONS = (ElementaryTypeNameExpression, Identifier)

    def detect_redundant_statements_contract(self, contract: Contract) -> List[Node]:
        """Detects the usage of redundant statements in a contract.

        Returns:
            list: nodes"""
        results = []

        # Loop through all functions + modifiers defined explicitly in this contract.
        for function in contract.functions_and_modifiers_declared:

            # Loop through each node in this function.
            for node in function.nodes:
                if node.expression:
                    if node.type == NodeType.EXPRESSION and isinstance(
                        node.expression, self.REDUNDANT_TOP_LEVEL_EXPRESSIONS
                    ):
                        results.append(node)

        return results

    def _detect(self) -> List[Output]:
        """Detect redundant statements

        Recursively visit the calls
        Returns:
            list: {'vuln', 'filename,'contract','func', 'redundant_statements'}

        """
        results = []
        for contract in self.contracts:
            redundant_statements = self.detect_redundant_statements_contract(contract)
            if redundant_statements:

                for redundant_statement in redundant_statements:
                    info: DETECTOR_INFO = [
                        'Redundant expression "',
                        redundant_statement,
                        '" in',
                        contract,
                        "\n",
                    ]
                    json = self.generate_result(info)
                    results.append(json)

        return results
