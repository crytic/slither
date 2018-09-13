"""
    Module detecting state uninitialized variables
    Recursively check the called functions

    The heuristic chekcs that:
    - state variables are read or called
    - the variables does not call push (avoid too many FP)

    Only analyze "leaf" contracts (contracts that are not inherited by another contract)
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

from slither.visitors.expression.findPush import FindPush


class UninitializedStorageVars(AbstractDetector):
    """
    """

    ARGUMENT = 'uninitialized-storage'
    HELP = 'Uninitialized storage variables'
    CLASSIFICATION = DetectorClassification.HIGH

    def detect(self):
        """ Detect uninitialized state variables

        Recursively visit the calls
        Returns:
            dict: [contract name] = set(state variable uninitialized)
        """
        results = []
        for contract in self.slither.contracts:
            for function in contract.functions:
                uninitialized_storage_variables = [v for v in function.variables if v.is_storage and v.uninitialized]

                if uninitialized_storage_variables:
                    vars_name = [v.name for v in uninitialized_storage_variables]

                    info = "Uninitialized storage variables in %s, " % self.filename + \
                           "Contract: %s, Function: %s, Variables %s" % (contract.name,
                                                                         function.name,
                                                                         vars_name)
                    self.log(info)

                    source = [function.source_mapping]
                    source += [v.source_mapping for v in uninitialized_storage_variables]

                    results.append({'vuln': 'UninitializedStorageVars',
                                    'sourceMapping': source,
                                    'filename': self.filename,
                                    'contract': contract.name,
                                    'function': function.name,
                                    'variables': vars_name})

        return results
