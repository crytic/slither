"""
Module detecting state variables that could be declared as constant
"""

from slither.core.solidity_types.elementary_type import ElementaryType
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

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
    def _valid_candidate(v):
        return isinstance(v.type, ElementaryType) and not v.is_constant

    def detect(self):
        """ Detect state variables that could be const
        """
        results = []
        all_info = ''

        all_variables = [c.state_variables for c in self.slither.contracts]
        all_variables = set([item for sublist in all_variables for item in sublist])
        all_non_constant_elementary_variables = set([v for v in all_variables
                                                     if self._valid_candidate(v)])

        all_functions = [c.all_functions_called for c in self.slither.contracts]
        all_functions = list(set([item for sublist in all_functions for item in sublist]))

        all_variables_written = [f.state_variables_written for f in all_functions]
        all_variables_written = set([item for sublist in all_variables_written for item in sublist])

        constable_variables = [v for v in all_non_constant_elementary_variables
                               if not v in all_variables_written]
        # Order for deterministic results
        constable_variables = sorted(constable_variables, key=lambda x: x.canonical_name)
        for v in constable_variables:
            info = "{}.{} should be constant ({})\n".format(v.contract.name,
                                                            v.name,
                                                            v.source_mapping_str)
            all_info += info
        if all_info != '':
            json = self.generate_json_result(all_info)
            self.add_variables_to_json(constable_variables, json)
            results.append(json)
            self.log(all_info)
        return results
