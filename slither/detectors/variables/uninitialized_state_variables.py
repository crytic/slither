"""
    Module detecting state uninitialized variables
    Recursively check the called functions

    The heuristic chekcs that:
    - state variables are read or called
    - the variables does not call push (avoid too many FP)

    Only analyze "leaf" contracts (contracts that are not inherited by another contract)
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

from slither.visitors.expression.find_push import FindPush


class UninitializedStateVarsDetection(AbstractDetector):
    """
    Constant function detector
    """

    ARGUMENT = 'uninitialized-state'
    HELP = 'Uninitialized state variables'
    CLASSIFICATION = DetectorClassification.HIGH

    def detect_uninitialized(self, contract):
        # get all the state variables read by all functions
        var_read = [f.state_variables_read for f in contract.functions_all_called + contract.modifiers]
        # flat list
        var_read = [item for sublist in var_read for item in sublist]
        # remove state variable that are initiliazed at contract construction
        var_read = [v for v in var_read if v.uninitialized]

        # get all the state variables written by the functions
        var_written = [f.state_variables_written for f in contract.functions_all_called + contract.modifiers]
        # flat list
        var_written = [item for sublist in var_written for item in sublist]

        all_push = [f.apply_visitor(FindPush) for f in contract.functions]
        # flat list
        all_push = [item for sublist in all_push for item in sublist]

        uninitialized_vars = list(set([v for v in var_read if \
                                       v not in var_written and \
                                       v not in all_push and \
                                       v.type not in contract.using_for]))  # Note: does not handle using X for *

        return [(v, contract.get_functions_reading_from_variable(v)) for v in uninitialized_vars]

    def detect(self):
        """ Detect uninitialized state variables

        Recursively visit the calls
        Returns:
            dict: [contract name] = set(state variable uninitialized)
        """
        results = []
        for c in self.slither.contracts_derived:
            ret = self.detect_uninitialized(c)
            for variable, functions in ret:
                info = "Uninitialized state variable in %s, " % self.filename + \
                       "Contract: %s, Variable: %s, Used in %s" % (c.name,
                                                               str(variable),
                                                               [str(f) for f in functions])
                self.log(info)

                source = [variable.source_mapping]
                source += [f.source_mapping for f in functions]

                results.append({'vuln': 'UninitializedStateVars',
                                'sourceMapping': source,
                                'filename': self.filename,
                                'contract': c.name,
                                'functions': [str(f) for f in functions],
                                'variable': str(variable)})

        return results
