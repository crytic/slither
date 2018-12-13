"""
Module detecting unused state variables
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

class UnusedStateVars(AbstractDetector):
    """
    Unused state variables detector
    """

    ARGUMENT = 'unused-state'
    HELP = 'Unused state variables'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#unused-state-variables'

    def detect_unused(self, contract):
        if contract.is_signature_only():
            return None
        # Get all the variables read in all the functions and modifiers
        variables_used = [x.state_variables_read + x.state_variables_written for x in
                          (contract.all_functions_called + contract.modifiers)]
        # Flat list
        variables_used = [item for sublist in variables_used for item in sublist]
        # Return the variables unused that are not public
        return [x for x in contract.variables if
                x not in variables_used and x.visibility != 'public']

    def detect(self):
        """ Detect unused state variables
        """
        results = []
        all_info = ''
        for c in self.slither.contracts_derived:
            unusedVars = self.detect_unused(c)
            if unusedVars:
                info = ''
                for var in unusedVars:
                    info += "{}.{} ({}) is never used in {}\n".format(var.contract.name,
                                                                      var.name,
                                                                      var.source_mapping_str,
                                                                      c.name)

                all_info += info

                json = self.generate_json_result(info)
                self.add_variables_to_json(unusedVars, json)
                results.append(json)

        if all_info != '':
            self.log(all_info)
        return results
