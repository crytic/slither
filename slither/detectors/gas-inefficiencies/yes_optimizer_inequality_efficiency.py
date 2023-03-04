"""
Gas: If the optimizer is enabled, using > 0 outside of a require statement is slightly more gas efficient than using ! = 0. Opposite applies for within a require statement (! = 0 is more efficient than > 0).

"""
from collections import defaultdict

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification, Issue
from slither.slithir.operations import VariableIncrements
from slither.analyses.data_dependency.data_dependency import is_tainted
from slither.core.solidity_types.elementary_type import ElementaryType


class GasYesOptimizerInequalityCheck(AbstractDetector):
    """
    Gas: If the optimizer is enabled, using > 0 outside of a require statement is slightly more gas efficient than using ! = 0. Opposite applies for within a require statement (! = 0 is more efficient than > 0).
    """

    ARGUMENT = "yes-optimizer-inequality-efficiency"
    HELP = "Use ! = 0 within your require statements rather than > 0, and > 0 outside your require statements rather than ! = 0, to save gas."
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#-0-is-cheaper-than--0-sometimes"
    WIKI_TITLE = "> 0 is cheaper than ! = 0 sometimes."
    WIKI_DESCRIPTION = "With optimizer enabled, using the > 0 inequality outside of any require statements is slightly more gas efficient than using ! = 0. The opposite applies inside a require statement, where ! = 0 rather than > 0 will be the more gas-efficient option." 

def _analyze(self, contract):
    require_statements = contract.get_function_calls("require")
    if not require_statements:
        return

    optimizer_enabled = contract.solidity_version.optimizer_enabled

    for require_statement in require_statements:
        for operand in require_statement.condition.operands:
            if not isinstance(operand, VariableIncrements):
                continue

            # Check if the optimizer is enabled
            if optimizer_enabled:
                # Check if the inequality is > 0
                if operand.operator == ">" and is_tainted(operand.right):
                    self._issues.append(Issue(contract, require_statement, self.get_type_name(), self.IMPACT, self.CONFIDENCE, f"Use '!= 0' instead of '>' in '{operand}' inside '{require_statement}'", self._location_from_ir(operand)))
                # Check if the inequality is != 0
                elif operand.operator == "!=" and is_tainted(operand.right) and not is_tainted(operand.left):
                    self._issues.append(Issue(contract, require_statement, self.get_type_name(), self.IMPACT, self.CONFIDENCE, f"Use '>' instead of '!= 0' in '{operand}' inside '{require_statement}'", self._location_from_ir(operand)))
            else:
                # Check if the inequality is > 0
                if operand.operator == ">" and not is_tainted(operand.right):
                    self._issues.append(Issue(contract, require_statement, self.get_type_name(), self.IMPACT, self.CONFIDENCE, f"Use '!= 0' instead of '>' in '{operand}' inside '{require_statement}'", self._location_from_ir(operand)))
                # Check if the inequality is != 0
                elif operand.operator == "!=" and is_tainted(operand.right) and not is_tainted(operand.left):
                    self._issues.append(Issue(contract, require_statement, self.get_type_name(), self.IMPACT, self.CONFIDENCE, f"Use '>' instead of '!= 0' in '{operand}' inside '{require_statement}'", self._location_from_ir(operand)))
