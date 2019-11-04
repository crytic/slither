"""
Module detecting state variables that could be declared as constant
"""

from slither.core.solidity_types.elementary_type import ElementaryType
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.visitors.expression.export_values import ExportValues
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.core.variables.state_variable import StateVariable
from slither.formatters.variables.possible_const_state_variables import format


class ConstCandidateStateVars(AbstractDetector):
    """
    State variables that could be declared as constant detector.
    Not all types for constants are implemented in Solidity as of 0.4.25.
    The only supported types are value types and strings (ElementaryType).
    Reference: https://solidity.readthedocs.io/en/latest/contracts.html#constant-state-variables
    """

    ARGUMENT = 'constable-states'
    HELP = 'State variables that could be declared constant'
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#state-variables-that-could-be-declared-constant'


    WIKI_TITLE = 'State variables that could be declared constant'
    WIKI_DESCRIPTION = 'Constant state variable should be declared constant to save gas.'
    WIKI_RECOMMENDATION = 'Add the `constant` attributes to the state variables that never change.'

    @staticmethod
    def _valid_candidate(v):
        return isinstance(v.type, ElementaryType) and not v.is_constant

    # https://solidity.readthedocs.io/en/v0.5.2/contracts.html#constant-state-variables
    valid_solidity_function = [SolidityFunction('keccak256()'),
                               SolidityFunction('keccak256(bytes)'),
                               SolidityFunction('sha256()'),
                               SolidityFunction('sha256(bytes)'),
                               SolidityFunction('ripemd160()'),
                               SolidityFunction('ripemd160(bytes)'),
                               SolidityFunction('ecrecover(bytes32,uint8,bytes32,bytes32)'),
                               SolidityFunction('addmod(uint256,uint256,uint256)'),
                               SolidityFunction('mulmod(uint256,uint256,uint256)')]

    @staticmethod
    def _is_constant_var(v):
        if isinstance(v, StateVariable):
            return v.is_constant
        return False

    def _constant_initial_expression(self, v):
        if not v.expression:
            return True

        export = ExportValues(v.expression)
        values = export.result()
        if not values:
            return True
        if all((val in self.valid_solidity_function or self._is_constant_var(val) for val in values)):
            return True
        return False



    def _detect(self):
        """ Detect state variables that could be const
        """
        results = []

        all_variables = [c.state_variables for c in self.slither.contracts]
        all_variables = set([item for sublist in all_variables for item in sublist])
        all_non_constant_elementary_variables = set([v for v in all_variables
                                                     if self._valid_candidate(v)])

        all_functions = [c.all_functions_called for c in self.slither.contracts]
        all_functions = list(set([item for sublist in all_functions for item in sublist]))

        all_variables_written = [f.state_variables_written for f in all_functions if not f.is_constructor_variables]
        all_variables_written = set([item for sublist in all_variables_written for item in sublist])

        constable_variables = [v for v in all_non_constant_elementary_variables
                               if (not v in all_variables_written) and self._constant_initial_expression(v)]
        # Order for deterministic results
        constable_variables = sorted(constable_variables, key=lambda x: x.canonical_name)

        # Create a result for each finding
        for v in constable_variables:
            info = "{} should be constant ({})\n".format(v.canonical_name,
                                                         v.source_mapping_str)
            json = self.generate_json_result(info)
            self.add_variable_to_json(v, json)

            results.append(json)

        return results

    @staticmethod
    def _format(slither, result):
        format(slither, result)
