"""
Module detecting unused state variables
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

class UnusedStateVars(AbstractDetector):
    """
    Unused state variables detector
    """

    ARGUMENT = 'unused-state'
    HELP = 'unused state variables'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    def detect_unused(self, contract):
        if contract.is_signature_only():
            return None
        # Get all the variables read in all the functions and modifiers
        variables_used = [x.state_variables_read + x.state_variables_written for x in
                          (contract.functions + contract.modifiers)]
        # Flat list
        variables_used = [item for sublist in variables_used for item in sublist]
        # Return the variables unused that are not public
        return [x for x in contract.variables if
                x not in variables_used and x.visibility != 'public']

    def detect(self):
        """ Detect unused state variables
        """
        results = []
        for c in self.slither.contracts_derived:
            unusedVars = self.detect_unused(c)
            if unusedVars:
                unusedVarsName = [v.name for v in unusedVars]
                info = "Unused state variables in %s, Contract: %s, Vars %s" % (self.filename,
                                                                                c.name,
                                                                                str(unusedVarsName))
                self.log(info)

                sourceMapping = [v.source_mapping for v in unusedVars]

                results.append({'vuln': 'unusedStateVars',
                                'sourceMapping': sourceMapping,
                                'filename': self.filename,
                                'contract': c.name,
                                'unusedVars': unusedVarsName})
        return results
