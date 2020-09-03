import re
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.formatters.naming_convention.naming_convention import custom_format


class NamingConvention(AbstractDetector):
    """
    Check if naming conventions are followed
    https://solidity.readthedocs.io/en/v0.4.25/style-guide.html?highlight=naming_convention%20convention#naming_convention-conventions

    Exceptions:
    - Allow constant variables name/symbol/decimals to be lowercase (ERC20)
    - Allow '_' at the beggining of the mixed_case match for private variables and unused parameters
    - Ignore echidna properties (functions with names starting 'echidna_' or 'crytic_'
    """

    ARGUMENT = "naming-convention"
    HELP = "Conformity to Solidity naming conventions"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#conformity-to-solidity-naming-conventions"

    WIKI_TITLE = "Conformance to Solidity naming conventions"
    WIKI_DESCRIPTION = """
Solidity defines a [naming convention](https://solidity.readthedocs.io/en/v0.4.25/style-guide.html#naming-conventions) that should be followed.
#### Rule exceptions
- Allow constant variable name/symbol/decimals to be lowercase (`ERC20`).
- Allow `_` at the beginning of the `mixed_case` match for private variables and unused parameters."""

    WIKI_RECOMMENDATION = "Follow the Solidity [naming convention](https://solidity.readthedocs.io/en/v0.4.25/style-guide.html#naming-conventions)."

    STANDARD_JSON = False

    @staticmethod
    def is_cap_words(name):
        return re.search("^[A-Z]([A-Za-z0-9]+)?_?$", name) is not None

    @staticmethod
    def is_mixed_case(name):
        return re.search("^[a-z]([A-Za-z0-9]+)?_?$", name) is not None

    @staticmethod
    def is_mixed_case_with_underscore(name):
        # Allow _ at the beginning to represent private variable
        # or unused parameters
        return re.search("^[_]?[a-z]([A-Za-z0-9]+)?_?$", name) is not None

    @staticmethod
    def is_upper_case_with_underscores(name):
        return re.search("^[A-Z0-9_]+_?$", name) is not None

    @staticmethod
    def should_avoid_name(name):
        return re.search("^[lOI]$", name) is not None

    def _detect(self):  # pylint: disable=too-many-branches,too-many-statements

        results = []
        for contract in self.contracts:

            if not self.is_cap_words(contract.name):
                info = ["Contract ", contract, " is not in CapWords\n"]

                res = self.generate_result(info)
                res.add(contract, {"target": "contract", "convention": "CapWords"})
                results.append(res)

            for struct in contract.structures_declared:
                if not self.is_cap_words(struct.name):
                    info = ["Struct ", struct, " is not in CapWords\n"]

                    res = self.generate_result(info)
                    res.add(struct, {"target": "structure", "convention": "CapWords"})
                    results.append(res)

            for event in contract.events_declared:
                if not self.is_cap_words(event.name):
                    info = ["Event ", event, " is not in CapWords\n"]

                    res = self.generate_result(info)
                    res.add(event, {"target": "event", "convention": "CapWords"})
                    results.append(res)

            for func in contract.functions_declared:
                if func.is_constructor:
                    continue
                if not self.is_mixed_case(func.name):
                    if func.visibility in [
                        "internal",
                        "private",
                    ] and self.is_mixed_case_with_underscore(func.name):
                        continue
                    if func.name.startswith("echidna_") or func.name.startswith("crytic_"):
                        continue
                    info = ["Function ", func, " is not in mixedCase\n"]

                    res = self.generate_result(info)
                    res.add(func, {"target": "function", "convention": "mixedCase"})
                    results.append(res)

                for argument in func.parameters:
                    # Ignore parameter names that are not specified i.e. empty strings
                    if argument.name == "":
                        continue
                    if argument in func.variables_read_or_written:
                        correct_naming = self.is_mixed_case(argument.name)
                    else:
                        correct_naming = self.is_mixed_case_with_underscore(argument.name)
                    if not correct_naming:
                        info = ["Parameter ", argument, " is not in mixedCase\n"]

                        res = self.generate_result(info)
                        res.add(argument, {"target": "parameter", "convention": "mixedCase"})
                        results.append(res)

            for var in contract.state_variables_declared:
                if self.should_avoid_name(var.name):
                    if not self.is_upper_case_with_underscores(var.name):
                        info = [
                            "Variable ",
                            var,
                            " used l, O, I, which should not be used\n",
                        ]

                        res = self.generate_result(info)
                        res.add(
                            var, {"target": "variable", "convention": "l_O_I_should_not_be_used",},
                        )
                        results.append(res)

                if var.is_constant is True:
                    # For ERC20 compatibility
                    if var.name in ["symbol", "name", "decimals"]:
                        continue

                    if not self.is_upper_case_with_underscores(var.name):
                        info = [
                            "Constant ",
                            var,
                            " is not in UPPER_CASE_WITH_UNDERSCORES\n",
                        ]

                        res = self.generate_result(info)
                        res.add(
                            var,
                            {
                                "target": "variable_constant",
                                "convention": "UPPER_CASE_WITH_UNDERSCORES",
                            },
                        )
                        results.append(res)

                else:
                    if var.visibility == "private":
                        correct_naming = self.is_mixed_case_with_underscore(var.name)
                    else:
                        correct_naming = self.is_mixed_case(var.name)
                    if not correct_naming:
                        info = ["Variable ", var, " is not in mixedCase\n"]

                        res = self.generate_result(info)
                        res.add(var, {"target": "variable", "convention": "mixedCase"})
                        results.append(res)

            for enum in contract.enums_declared:
                if not self.is_cap_words(enum.name):
                    info = ["Enum ", enum, " is not in CapWords\n"]

                    res = self.generate_result(info)
                    res.add(enum, {"target": "enum", "convention": "CapWords"})
                    results.append(res)

            for modifier in contract.modifiers_declared:
                if not self.is_mixed_case(modifier.name):
                    info = ["Modifier ", modifier, " is not in mixedCase\n"]

                    res = self.generate_result(info)
                    res.add(modifier, {"target": "modifier", "convention": "mixedCase"})
                    results.append(res)

        return results

    @staticmethod
    def _format(slither, result):
        custom_format(slither, result)
