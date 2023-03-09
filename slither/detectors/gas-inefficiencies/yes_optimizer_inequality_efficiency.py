"""
Gas: If the optimizer is enabled, using > 0 outside of a require statement is slightly more gas efficient than using ! = 0. Opposite applies for within a require statement (! = 0 is more efficient than > 0).

"""

from slither.detectors.abstract_detector import AbstractDetector
from slither.analyses.data_dependency.data_dependency import is_tainted
from slither.detectors.operations import variable_increments


class GasYesOptimizerInequalityCheck(AbstractDetector):
    """
    Gas: If the optimizer is enabled, using > 0 outside of a require statement is slightly more gas efficient than using ! = 0. Opposite applies for within a require statement (! = 0 is more efficient than > 0).
    """

    ARGUMENT = "yes-optimizer-inequality-efficiency"
    HELP = "Use ! = 0 within your require statements rather than > 0, and > 0 outside your require statements rather than ! = 0, to save gas."
    IMPACT = "OPTIMIZATION"
    CONFIDENCE = "MEDIUM"

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#-0-is-cheaper-than--0-sometimes"
    WIKI_TITLE = "> 0 is cheaper than ! = 0 sometimes."
    WIKI_DESCRIPTION = "With optimizer enabled, using the > 0 inequality outside of any require statements is slightly more gas efficient than using ! = 0. The opposite applies inside a require statement, where ! = 0 rather than > 0 will be the more gas-efficient option." 

    def __init__(self):
        self.issues = []

    def detect(self, contract):
        require_statements = contract.get_function_calls("require")
        if not require_statements:
            return {'result': self.issues}

        optimizer_enabled = contract.solidity_version.optimizer_enabled

        for require_statement in require_statements:
            for operand in require_statement.condition.operands:
                if not isinstance(operand, variable_increments):
                    continue

                # Check if the optimizer is enabled
                if optimizer_enabled:
                    # Check if the inequality is > 0
                    if operand.operator == ">" and is_tainted(operand.right):
                        self.issues.append({
                            'contract': contract,
                            'require_statement': require_statement,
                            'type': self.__class__.__name__,
                            'impact': self.IMPACT,
                            'confidence': self.CONFIDENCE,
                            'message': f"Use '!= 0' instead of '>' in '{operand}' inside '{require_statement}'",
                            'location': self._location_from_ir(operand),
                        })
                    # Check if the inequality is != 0
                    elif operand.operator == "!=" and is_tainted(operand.right) and not is_tainted(operand.left):
                        self.issues.append({
                            'contract': contract,
                            'require_statement': require_statement,
                            'type': self.__class__.__name__,
                            'impact': self.IMPACT,
                            'confidence': self.CONFIDENCE,
                            'message': f"Use '>' instead of '!= 0' in '{operand}' inside '{require_statement}'",
                            'location': self._location_from_ir(operand),
                        })
                else:
                    # Check if the inequality is > 0
                    if operand.operator == ">" and not is_tainted(operand.right):
                        self.issues.append({
                            'contract': contract,
                            'require_statement': require_statement,
                            'type': self.__class__.__name__,
                            'impact': self.IMPACT,
                            'confidence': self.CONFIDENCE,
                            'message': f"Use '!= 0' instead of '>' in '{operand}' inside '{require_statement}'",
                            'location': self._location_from_ir(operand),
                        })
                    # Check if the inequality is != 0
                    elif operand.operator == "!=" and is_tainted(operand.right) and not is_tainted(operand.left):
                        self.issues.append({
                            'contract': contract,
                            'require_statement': require_statement,
                            'type': self.__class__.__name__,
                            'impact': self.IMPACT,
                            'confidence': self.CONFIDENCE,
                            'message': f"Use '>' instead of '!= 0' in '{operand}' inside '{require_statement}'",
                            'location': self._location_from_ir(operand),
                        })
                        return {'result': self.issues}

    def _location_from_ir(self, ir):
        return {'line': ir.lineno, 'column': ir.col_offset}

