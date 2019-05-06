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

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#conformance-to-solidity-naming-conventions'

    WIKI_TITLE = 'Conformance to Solidity naming conventions'
    WIKI_DESCRIPTION = '''
Solidity defines a [naming convention](https://solidity.readthedocs.io/en/v0.4.25/style-guide.html#naming-conventions) that should be followed.
#### Rules exceptions
- Allow constant variables name/symbol/decimals to be lowercase (ERC20)
- Allow `_` at the beginning of the mixed_case match for private variables and unused parameters.'''

    WIKI_RECOMMENDATION = 'Follow the Solidity [naming convention](https://solidity.readthedocs.io/en/v0.4.25/style-guide.html#naming-conventions).'


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

    def _detect(self):

        results = []
        for contract in self.contracts:

            if not self.is_cap_words(contract.name):
                info = "Contract '{}' ({}) is not in CapWords\n".format(contract.name,
                                                                        contract.source_mapping_str)

                json = self.generate_json_result(info)
                self.add_contract_to_json(contract, json, {
                    "target": "contract",
                    "convention": "CapWords"
                })
                results.append(json)

            for struct in contract.structures:
                if struct.contract != contract:
                    continue

                if not self.is_cap_words(struct.name):
                    info = "Struct '{}.{}' ({}) is not in CapWords\n"
                    info = info.format(struct.contract.name, struct.name, struct.source_mapping_str)

                    json = self.generate_json_result(info)
                    self.add_struct_to_json(struct, json, {
                        "target": "structure",
                        "convention": "CapWords"
                    })
                    results.append(json)

            for event in contract.events:
                if event.contract != contract:
                    continue

                if not self.is_cap_words(event.name):
                    info = "Event '{}.{}' ({}) is not in CapWords\n"
                    info = info.format(event.contract.name, event.name, event.source_mapping_str)

                    json = self.generate_json_result(info)
                    self.add_event_to_json(event, json, {
                        "target": "event",
                        "convention": "CapWords"
                    })
                    results.append(json)

            for func in contract.functions:
                if func.contract != contract:
                    continue

                if not self.is_mixed_case(func.name):
                    info = "Function '{}.{}' ({}) is not in mixedCase\n"
                    info = info.format(func.contract.name, func.name, func.source_mapping_str)

                    json = self.generate_json_result(info)
                    self.add_function_to_json(func, json, {
                        "target": "function",
                        "convention": "mixedCase"
                    })
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

                        json = self.generate_json_result(info)
                        self.add_variable_to_json(argument, json, {
                            "target": "parameter",
                            "convention": "mixedCase"
                        })
                        results.append(json)

            for var in contract.state_variables:
                if var.contract != contract:
                    continue

                if self.should_avoid_name(var.name):
                    if not self.is_upper_case_with_underscores(var.name):
                        info = "Variable '{}.{}' ({}) used l, O, I, which should not be used\n"
                        info = info.format(var.contract.name, var.name, var.source_mapping_str)

                        json = self.generate_json_result(info)
                        self.add_variable_to_json(var, json, {
                            "target": "variable",
                            "convention": "l_O_I_should_not_be_used"
                        })
                        results.append(json)

                if var.is_constant is True:
                    # For ERC20 compatibility
                    if var.name in ['symbol', 'name', 'decimals']:
                        continue

                    if not self.is_upper_case_with_underscores(var.name):
                        info = "Constant '{}.{}' ({}) is not in UPPER_CASE_WITH_UNDERSCORES\n"
                        info = info.format(var.contract.name, var.name, var.source_mapping_str)

                        json = self.generate_json_result(info)
                        self.add_variable_to_json(var, json, {
                            "target": "variable_constant",
                            "convention": "UPPER_CASE_WITH_UNDERSCORES"
                        })
                        results.append(json)

                else:
                    if var.visibility == 'private':
                        correct_naming = self.is_mixed_case_with_underscore(var.name)
                    else:
                        correct_naming = self.is_mixed_case(var.name)
                    if not correct_naming:
                        info = "Variable '{}.{}' ({}) is not in mixedCase\n"
                        info = info.format(var.contract.name, var.name, var.source_mapping_str)

                        json = self.generate_json_result(info)
                        self.add_variable_to_json(var, json, {
                            "target": "variable",
                            "convention": "mixedCase"
                        })
                        results.append(json)

            for enum in contract.enums:
                if enum.contract != contract:
                    continue

                if not self.is_cap_words(enum.name):
                    info = "Enum '{}.{}' ({}) is not in CapWords\n"
                    info = info.format(enum.contract.name, enum.name, enum.source_mapping_str)

                    json = self.generate_json_result(info)
                    self.add_enum_to_json(enum, json, {
                        "target": "enum",
                        "convention": "CapWords"
                    })
                    results.append(json)


            for modifier in contract.modifiers:
                if modifier.contract != contract:
                    continue

                if not self.is_mixed_case(modifier.name):
                    info = "Modifier '{}.{}' ({}) is not in mixedCase\n"
                    info = info.format(modifier.contract.name,
                                       modifier.name,
                                       modifier.source_mapping_str)

                    json = self.generate_json_result(info)
                    self.add_function_to_json(modifier, json, {
                        "target": "modifier",
                        "convention": "mixedCase"
                    })
                    results.append(json)


        return results
