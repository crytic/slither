"""
Module detecting state variables that could be declared as constant
"""

from collections import defaultdict
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import OperationWithLValue
from slither.core.variables.state_variable import StateVariable
from slither.core.expressions.literal import Literal


class ConstCandidateStateVars(AbstractDetector):
    """
    State variables that could be declared as constant detector.
    Not all types for constants are implemented in Solidity as of 0.4.25.
    The only supported types are value types and strings (ElementaryType).
    Reference: https://solidity.readthedocs.io/en/latest/contracts.html#constant-state-variables
    """

    ARGUMENT = 'constable-states'
    HELP = 'State variables that could be declared constant'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#state-variables-that-could-be-declared-constant'

    @staticmethod
    def lvalues_of_operations_with_lvalue(contract):
        ret = []
        for f in contract.all_functions_called + contract.modifiers:
            for n in f.nodes:
                for ir in n.irs:
                    if isinstance(ir, OperationWithLValue) and isinstance(ir.lvalue, StateVariable):
                        ret.append(ir.lvalue)
        return ret

    @staticmethod
    def non_const_state_variables(contract):
        return [variable for variable in contract.state_variables
                if not variable.is_constant and type(variable.expression) == Literal]

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
        all_info = ''
        for c in self.slither.contracts_derived:
            const_candidates = self.detect_const_candidates(c)
            if const_candidates:
                variables_by_contract = defaultdict(list)

                for state_var in const_candidates:
                    variables_by_contract[state_var.contract.name].append(state_var)

                for contract, variables in variables_by_contract.items():
                    variable_names = [v.name for v in variables]
                    for v in variables:
                        all_info += "{}.{} should be constant ({})\n".format(contract, v.name, v.source_mapping_str)

                    sourceMapping = [v.source_mapping for v in const_candidates]

                    results.append({'vuln': 'ConstStateVariableCandidates',
                                    'sourceMapping': sourceMapping,
                                    'filename': self.filename,
                                    'contract': c.name,
                                    'unusedVars': variable_names})
        if all_info != '':
            self.log(all_info)
        return results
