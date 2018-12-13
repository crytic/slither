"""
Module detecting shadowing variables on abstract contract
Recursively check the called functions
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class ShadowingAbstractDetection(AbstractDetector):
    """
    Shadowing detection
    """

    ARGUMENT = 'shadowing-abstract'
    HELP = 'State variables shadowing from abstract contracts'
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#state-variable-shadowing-from-abstract-contracts'

    vuln_name = "ShadowingAbstractContract"

    def detect_shadowing(self, contract):
        ret = []
        variables_fathers = []
        for father in contract.inheritance:
            if all(not f.is_implemented for f in father.functions + father.modifiers):
                variables_fathers += [v for v in father.variables if v.contract == father]

        for var in [v for v in contract.variables if v.contract == contract]:
            shadow = [v for v in variables_fathers if v.name == var.name]
            if shadow:
                ret.append([var] + shadow)
        return ret


    def detect(self):
        """ Detect shadowing

        Recursively visit the calls
        Returns:
            list: {'vuln', 'filename,'contract','func', 'shadow'}

        """
        results = []
        for c in self.contracts:
            shadowing = self.detect_shadowing(c)
            if shadowing:
                for all_variables in shadowing:
                    shadow = all_variables[0]
                    variables = all_variables[1:]
                    info = '{}.{} ({}) shadows:\n'.format(shadow.contract.name,
                                                        shadow.name,
                                                        shadow.source_mapping_str)
                    for var in variables:
                        info += "\t- {}.{} ({})\n".format(var.contract.name,
                                                       var.name,
                                                       var.source_mapping_str)
                    self.log(info)

                    json = self.generate_json_result(info)
                    self.add_variables_to_json(all_variables, json)
                    results.append(json)

        return results
