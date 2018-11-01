from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
import re


class NamingConvention(AbstractDetector):
    """
    Check if naming conventions are followed
    https://solidity.readthedocs.io/en/v0.4.25/style-guide.html?highlight=naming_convention%20convention#naming_convention-conventions

    Exceptions:
    - Allow constant variables name/symbol/decimals to be lowercase (ERC20)
    - Allow '_' at the beggining of the mixed_case match for private variables and unused parameters
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
    def is_mixed_case_with_underscore(name):
        # Allow _ at the beginning to represent private variable
        # or unused parameters
        return re.search('^[a-z_]([A-Za-z0-9]+)?_?$', name) is not None

    @staticmethod
    def is_upper_case_with_underscores(name):
        return re.search('^[A-Z0-9_]+_?$', name) is not None

    @staticmethod
    def should_avoid_name(name):
        return re.search('^[lOI]$', name) is not None

    def detect(self):

        results = []
        for contract in sorted(self.contracts, key=lambda c: c.name):

            if not self.is_cap_words(contract.name):
                info = "Contract '{}' is not in CapWords".format(contract.name)
                self.log(info)

                results.append({'vuln': 'NamingConvention',
                                'filename': self.filename,
                                'contract': contract.name,
                                'sourceMapping': contract.source_mapping})

            for struct in sorted(contract.structures, key=lambda x: x.name):
                if struct.contract != contract:
                    continue

                if not self.is_cap_words(struct.name):
                    info = "Struct '{}' is not in CapWords, Contract: '{}' ".format(struct.name, contract.name)
                    self.log(info)

                    results.append({'vuln': 'NamingConvention',
                                    'filename': self.filename,
                                    'contract': contract.name,
                                    'struct': struct.name,
                                    'sourceMapping': struct.source_mapping})

            for event in sorted(contract.events, key=lambda x: x.name):
                if event.contract != contract:
                    continue

                if not self.is_cap_words(event.name):
                    info = "Event '{}' is not in CapWords, Contract: '{}' ".format(event.name, contract.name)
                    self.log(info)

                    results.append({'vuln': 'NamingConvention',
                                    'filename': self.filename,
                                    'contract': contract.name,
                                    'event': event.name,
                                    'sourceMapping': event.source_mapping})

            for func in sorted(contract.functions, key=lambda x: x.name):
                if func.contract != contract:
                    continue

                if not self.is_mixed_case(func.name):
                    info = "Function '{}' is not in mixedCase, Contract: '{}' ".format(func.name, contract.name)
                    self.log(info)

                    results.append({'vuln': 'NamingConvention',
                                    'filename': self.filename,
                                    'contract': contract.name,
                                    'function': func.name,
                                    'sourceMapping': func.source_mapping})

                for argument in sorted(func.parameters, key=lambda x: x.name):
                    if argument in func.variables_read_or_written:
                        correct_naming = self.is_mixed_case(argument.name)
                    else:
                        correct_naming = self.is_mixed_case_with_underscore(argument.name)
                    if not correct_naming:
                        info = "Parameter '{}' is not in mixedCase, Contract: '{}', Function: '{}'' " \
                            .format(argument.name, argument.name, contract.name)
                        self.log(info)

                        results.append({'vuln': 'NamingConvention',
                                        'filename': self.filename,
                                        'contract': contract.name,
                                        'function': func.name,
                                        'argument': argument.name,
                                        'sourceMapping': argument.source_mapping})

            for var in sorted(contract.state_variables, key=lambda x: x.name):
                if var.contract != contract:
                    continue

                if self.should_avoid_name(var.name):
                    if not self.is_upper_case_with_underscores(var.name):
                        info = "Variable '{}' l, O, I should not be used, Contract: '{}' " \
                            .format(var.name, contract.name)
                        self.log(info)

                        results.append({'vuln': 'NamingConvention',
                                        'filename': self.filename,
                                        'contract': contract.name,
                                        'constant': var.name,
                                        'sourceMapping': var.source_mapping})

                if var.is_constant is True:
                    # For ERC20 compatibility
                    if var.name in ['symbol', 'name', 'decimals']:
                        continue

                    if not self.is_upper_case_with_underscores(var.name):
                        info = "Constant '{}' is not in UPPER_CASE_WITH_UNDERSCORES, Contract: '{}' " \
                            .format(var.name, contract.name)
                        self.log(info)

                        results.append({'vuln': 'NamingConvention',
                                        'filename': self.filename,
                                        'contract': contract.name,
                                        'constant': var.name,
                                        'sourceMapping': var.source_mapping})
                else:
                    if var.visibility == 'private':
                        correct_naming = self.is_mixed_case_with_underscore(var.name)
                    else:
                        correct_naming = self.is_mixed_case(var.name)
                    if not correct_naming:
                        info = "Variable '{}' is not in mixedCase, Contract: '{}' ".format(var.name, contract.name)
                        self.log(info)

                        results.append({'vuln': 'NamingConvention',
                                        'filename': self.filename,
                                        'contract': contract.name,
                                        'variable': var.name,
                                        'sourceMapping': var.source_mapping})

            for enum in sorted(contract.enums, key=lambda x: x.name):
                if enum.contract != contract:
                    continue

                if not self.is_cap_words(enum.name):
                    info = "Enum '{}' is not in CapWords, Contract: '{}' ".format(enum.name, contract.name)
                    self.log(info)

                    results.append({'vuln': 'NamingConvention',
                                    'filename': self.filename,
                                    'contract': contract.name,
                                    'enum': enum.name,
                                    'sourceMapping': enum.source_mapping})

            for modifier in sorted(contract.modifiers, key=lambda x: x.name):
                if modifier.contract != contract:
                    continue

                if not self.is_mixed_case(modifier.name):
                    info = "Modifier '{}' is not in mixedCase, Contract: '{}' ".format(modifier.name, contract.name)
                    self.log(info)

                    results.append({'vuln': 'NamingConvention',
                                    'filename': self.filename,
                                    'contract': contract.name,
                                    'modifier': modifier.name,
                                    'sourceMapping': modifier.source_mapping})

        return results
