from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
import re


class NamingConvention(AbstractDetector):
    """
    Check if naming conventions are followed
    https://solidity.readthedocs.io/en/v0.4.25/style-guide.html?highlight=naming_convention%20convention#naming_convention-conventions
    """

    ARGUMENT = 'naming-convention'
    HELP = 'Conformance to Solidity naming conventions'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    @staticmethod
    def is_cap_words(name):
        return re.search('^[A-Z]([A-Za-z0-9]+)?_?$', name) is not None

    @staticmethod
    def is_mixed_case(name):
        return re.search('^[a-z]([A-Za-z0-9]+)?_?$', name) is not None

    @staticmethod
    def is_upper_case_with_underscores(name):
        return re.search('^[A-Z0-9_]+_?$', name) is not None

    @staticmethod
    def should_avoid_name(name):
        return re.search('^[lOI]$', name) is not None

    def detect(self):

        results = []
        for contract in self.contracts:

            if self.is_cap_words(contract.name) is False:
                info = "Contract '{}' is not in CapWords".format(contract.name)
                self.log(info)

                results.append({'vuln': 'NamingConvention',
                                'filename': self.filename,
                                'contract': contract.name,
                                'sourceMapping': contract.source_mapping})

            for struct in contract.structures:

                if self.is_cap_words(struct.name) is False:
                    info = "Struct '{}' is not in CapWords, Contract: '{}' ".format(struct.name, contract.name)
                    self.log(info)

                    results.append({'vuln': 'NamingConvention',
                                    'filename': self.filename,
                                    'contract': contract.name,
                                    'struct': struct.name,
                                    'sourceMapping': struct.source_mapping})

            for event in contract.events:

                if self.is_cap_words(event.name) is False:
                    info = "Event '{}' is not in CapWords, Contract: '{}' ".format(event.name, contract.name)
                    self.log(info)

                    results.append({'vuln': 'NamingConvention',
                                    'filename': self.filename,
                                    'contract': contract.name,
                                    'event': event.name,
                                    'sourceMapping': event.source_mapping})

            for func in contract.functions:

                if self.is_mixed_case(func.name) is False:
                    info = "Function '{}' is not in mixedCase, Contract: '{}' ".format(func.name, contract.name)
                    self.log(info)

                    results.append({'vuln': 'NamingConvention',
                                    'filename': self.filename,
                                    'contract': contract.name,
                                    'function': func.name,
                                    'sourceMapping': func.source_mapping})

                for argument in func.parameters:

                    argument_name = argument.name
                    if argument_name and argument_name.startswith('_'):
                        argument_name = argument_name[1::]

                    if self.is_mixed_case(argument_name) is False:
                        info = "Parameter '{}' is not in mixedCase, Contract: '{}', Function: '{}'' " \
                            .format(argument.name, argument.name, contract.name)
                        self.log(info)

                        results.append({'vuln': 'NamingConvention',
                                        'filename': self.filename,
                                        'contract': contract.name,
                                        'function': func.name,
                                        'argument': argument.name,
                                        'sourceMapping': argument.source_mapping})

            for var in contract.state_variables:

                if self.should_avoid_name(var.name):
                    if self.is_upper_case_with_underscores(var.name) is False:
                        info = "Variable '{}' l, O, I should not be used, Contract: '{}' " \
                            .format(var.name, contract.name)
                        self.log(info)

                        results.append({'vuln': 'NamingConvention',
                                        'filename': self.filename,
                                        'contract': contract.name,
                                        'constant': var.name,
                                        'sourceMapping': var.source_mapping})

                if var.is_constant is True:
                    if self.is_upper_case_with_underscores(var.name) is False:
                        info = "Constant '{}' is not in UPPER_CASE_WITH_UNDERSCORES, Contract: '{}' " \
                            .format(var.name, contract.name)
                        self.log(info)

                        results.append({'vuln': 'NamingConvention',
                                        'filename': self.filename,
                                        'contract': contract.name,
                                        'constant': var.name,
                                        'sourceMapping': var.source_mapping})
                else:

                    var_name = var.name
                    if var_name and var_name.startswith('_'):
                        var_name = var_name[1::]

                    if self.is_mixed_case(var_name) is False:
                        info = "Variable '{}' is not in mixedCase, Contract: '{}' ".format(var.name, contract.name)
                        self.log(info)

                        results.append({'vuln': 'NamingConvention',
                                        'filename': self.filename,
                                        'contract': contract.name,
                                        'variable': var.name,
                                        'sourceMapping': var.source_mapping})

            for enum in contract.enums:
                if self.is_cap_words(enum.name) is False:
                    info = "Enum '{}' is not in CapWords, Contract: '{}' ".format(enum.name, contract.name)
                    self.log(info)

                    results.append({'vuln': 'NamingConvention',
                                    'filename': self.filename,
                                    'contract': contract.name,
                                    'enum': enum.name,
                                    'sourceMapping': enum.source_mapping})

            for modifier in contract.modifiers:
                if self.is_mixed_case(modifier.name) is False:
                    info = "Modifier '{}' is not in mixedCase, Contract: '{}' ".format(modifier.name, contract.name)
                    self.log(info)

                    results.append({'vuln': 'NamingConvention',
                                    'filename': self.filename,
                                    'contract': contract.name,
                                    'modifier': modifier.name,
                                    'sourceMapping': modifier.source_mapping})

        return results
