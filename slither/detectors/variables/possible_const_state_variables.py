"""
Module detecting state variables that could be declared as constant
"""

from slither.core.solidity_types.elementary_type import ElementaryType
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import OperationWithLValue


class ConstCandidateStateVars(AbstractDetector):
    """
    State variables that could be declared as constant detector.
    Not all types for constants are implemented in Solidity as of 0.4.25.
    The only supported types are value types and strings (ElementaryType).
    Reference: https://solidity.readthedocs.io/en/latest/contracts.html#constant-state-variables
    """

    ARGUMENT = 'const-candidates-state'
    HELP = 'detect state variables that could be const'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    @staticmethod
    def lvalues_of_operations_with_lvalue(contract):
        ret = []
        for f in contract.functions:
            if f.name == 'fallback':  # Skip fallback function to avoid false positives
                continue
            for n in f.nodes:
                for ir in n.irs:
                    if isinstance(ir, OperationWithLValue):
                        ret.append(ir.lvalue)
        return ret

    @staticmethod
    def non_const_state_variables(contract):
        return [variable for variable in contract.state_variables if not variable.is_constant]

    def detect_const_candidates(self, contract):
        const_candidates = []
        non_const_state_vars = self.non_const_state_variables(contract)
        lvalues_of_operations = self.lvalues_of_operations_with_lvalue(contract)
        for non_const in non_const_state_vars:
            if non_const not in lvalues_of_operations \
                    and non_const not in const_candidates \
                    and isinstance(non_const.type, ElementaryType):
                const_candidates.append(non_const)

        return const_candidates

    def detect(self):
        """ Detect state variables that could be const
        """
        results = []
        for c in self.contracts:
            const_candidates = self.detect_const_candidates(c)
            if const_candidates:
                variable_names = [v.name for v in const_candidates]
                info = "State variables that could be const in %s, Contract: %s, Vars %s" % (self.filename,
                                                                                             c.name,
                                                                                             str(variable_names))
                self.log(info)

                sourceMapping = [v.source_mapping for v in const_candidates]

                results.append({'vuln': 'ConstStateVariableCandidates',
                                'sourceMapping': sourceMapping,
                                'filename': self.filename,
                                'contract': c.name,
                                'unusedVars': variable_names})
        return results
