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

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#conformance-to-solidity-naming-conventions'

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
        all_info = ''
        for contract in self.contracts:

            if not self.is_cap_words(contract.name):
                info = "Contract '{}' ({}) is not in CapWords\n".format(contract.name,
                                                                        contract.source_mapping_str)
                all_info += info

                json = self.generate_json_result(info)
                json['type'] = 'contract'
                json['convention'] = 'CapWords'
                json['name'] = {'name': contract.name,
                                'source_mapping': contract.source_mapping}
                results.append(json)

            for struct in contract.structures:
                if struct.contract != contract:
                    continue

                if not self.is_cap_words(struct.name):
                    info = "Struct '{}.{}' ({}) is not in CapWords\n"
                    info = info.format(struct.contract.name, struct.name, struct.source_mapping_str)
                    all_info += info

                    json = self.generate_json_result(info)
                    json['type'] = 'structure'
                    json['convention'] = 'CapWords'
                    json['name'] = {'name': struct.name,
                                    'source_mapping': struct.source_mapping}
                    results.append(json)
            for event in contract.events:
                if event.contract != contract:
                    continue

                if not self.is_cap_words(event.name):
                    info = "Event '{}.{}' ({}) is not in CapWords\n"
                    info = info.format(event.contract.name, event.name, event.source_mapping_str)
                    all_info += info

                    json = self.generate_json_result(info)
                    json['type'] = 'event'
                    json['convention'] = 'CapWords'
                    json['name'] = {'name': event.name,
                                    'source_mapping': event.source_mapping}
                    results.append(json)

            for func in contract.functions:
                if func.contract != contract:
                    continue

                if not self.is_mixed_case(func.name):
                    info = "Function '{}.{}' ({}) is not in mixedCase\n"
                    info = info.format(func.contract.name, func.name, func.source_mapping_str)
                    all_info += info

                    json = self.generate_json_result(info)
                    json['type'] = 'function'
                    json['convention'] = 'mixedCase'
                    json['name'] = {'name': func.name,
                                    'source_mapping': func.source_mapping}
                    results.append(json)

                for argument in func.parameters:
                    if argument in func.variables_read_or_written:
                        correct_naming = self.is_mixed_case(argument.name)
                    else:
                        correct_naming = self.is_mixed_case_with_underscore(argument.name)
                    if not correct_naming:
                        info = "Parameter '{}' of {}.{} ({}) is not in mixedCase\n"
                        info = info.format(argument.name,
                                           argument.function.contract.name,
                                           argument.function,
                                           argument.source_mapping_str)
                        all_info += info

                        json = self.generate_json_result(info)
                        json['type'] = 'parameter'
                        json['convention'] = 'mixedCase'
                        json['name'] = {'name': argument.name,
                                        'source_mapping': argument.source_mapping}
                        results.append(json)

            for var in contract.state_variables:
                if var.contract != contract:
                    continue

                if self.should_avoid_name(var.name):
                    if not self.is_upper_case_with_underscores(var.name):
                        info = "Variable '{}.{}' ({}) used l, O, I, which should not be used\n"
                        info = info.format(var.contract.name, var.name, var.source_mapping_str)
                        all_info += info

                        json = self.generate_json_result(info)
                        json['type'] = 'variable'
                        json['convention'] = 'l_O_I_should_not_be_used'
                        json['name'] = {'name': var.name,
                                        'source_mapping': var.source_mapping}
                        results.append(json)

                if var.is_constant is True:
                    # For ERC20 compatibility
                    if var.name in ['symbol', 'name', 'decimals']:
                        continue

                    if not self.is_upper_case_with_underscores(var.name):
                        info = "Constant '{}.{}' ({}) is not in UPPER_CASE_WITH_UNDERSCORES\n"
                        info = info.format(var.contract.name, var.name, var.source_mapping_str)
                        all_info += info

                        json = self.generate_json_result(info)
                        json['type'] = 'variable_constant'
                        json['convention'] = 'UPPER_CASE_WITH_UNDERSCORES'
                        json['name'] = {'name': var.name,
                                        'source_mapping': var.source_mapping}
                        results.append(json)

                else:
                    if var.visibility == 'private':
                        correct_naming = self.is_mixed_case_with_underscore(var.name)
                    else:
                        correct_naming = self.is_mixed_case(var.name)
                    if not correct_naming:
                        info = "Variable '{}.{}' ({}) is not in mixedCase\n"
                        info = info.format(var.contract.name, var.name, var.source_mapping_str)
                        all_info += info

                        json = self.generate_json_result(info)
                        json['type'] = 'variable'
                        json['convention'] = 'mixedCase'
                        json['name'] = {'name': var.name,
                                        'source_mapping': var.source_mapping}
                        results.append(json)

            for enum in contract.enums:
                if enum.contract != contract:
                    continue

                if not self.is_cap_words(enum.name):
                    info = "Enum '{}.{}' ({}) is not in CapWords\n"
                    info = info.format(enum.contract.name, enum.name, enum.source_mapping_str)
                    all_info += info

                    json = self.generate_json_result(info)
                    json['type'] = 'enum'
                    json['convention'] = 'CapWords'
                    json['name'] = {'name': enum.name,
                                    'source_mapping': enum.source_mapping}
                    results.append(json)


            for modifier in contract.modifiers:
                if modifier.contract != contract:
                    continue

                if not self.is_mixed_case(modifier.name):
                    info = "Modifier '{}.{}' ({}) is not in mixedCase\n"
                    info = info.format(modifier.contract.name,
                                       modifier.name,
                                       modifier.source_mapping_str)
                    all_info += info

                    json = self.generate_json_result(info)
                    json['type'] = 'modifier'
                    json['convention'] = 'mixedCase'
                    json['name'] = {'name': modifier.name,
                                    'source_mapping': modifier.source_mapping}
                    results.append(json)

        if all_info != '':
            self.log(all_info)

        return results
