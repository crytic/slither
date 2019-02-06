"""
Module detecting potential C3 linearization bugs (for internal use by printers)
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class C3LinearizationShadowingInternal(AbstractDetector):
    """
    C3 Linearization Shadowing
    """

    ARGUMENT = 'shadowing-c3-internal'
    HELP = 'C3 Linearization Shadowing (Internal)'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    # This detector is not meant to be called as a generic detector
    # It's only used by inheritances printers
    WIKI = 'undefined'
    WIKI_TITLE = 'undefined'
    WIKI_DESCRIPTION = 'undefined'
    WIKI_EXPLOIT_SCENARIO = 'undefined'
    WIKI_RECOMMENDATION = 'undefined'


    def detect_shadowing_definitions(self, contract):
        """
        Detects if a contract has two or more underlying contracts it inherits from which could potentially suffer from
        C3 linearization shadowing bugs.

        :param contract: The contract to check for potential C3 linearization shadowing within.
        :return: A list of list of tuples: (contract, function), where each inner list describes colliding functions.
        """

        # Loop through all contracts, and all underlying functions.
        results = {}
        for i in range(0, len(contract.immediate_inheritance) - 1):
            inherited_contract1 = contract.immediate_inheritance[i]

            for function1 in inherited_contract1.functions_and_modifiers:
                # If this function has already be handled or is unimplemented, we skip it
                if function1.full_name in results or function1.is_constructor or not function1.is_implemented:
                    continue

                # Define our list of function instances which overshadow each other.
                functions_matching = [(inherited_contract1, function1)]

                # Loop again through other contracts and functions to compare to.
                for x in range(i + 1, len(contract.immediate_inheritance)):
                    inherited_contract2 = contract.immediate_inheritance[x]

                    # Loop for each function in this contract
                    for function2 in inherited_contract2.functions_and_modifiers:
                        # Skip this function if it is the last function that was shadowed.
                        if function2 == functions_matching[-1][1] or function2.is_constructor or not function2.is_implemented:
                            continue

                        # If this function does have the same full name, it is shadowing through C3 linearization.
                        if function1.full_name == function2.full_name:
                            functions_matching.append((inherited_contract2, function2))

                # If we have more than one definition matching the same signature, we add it to the results.
                if len(functions_matching) > 1:
                    results[function1.full_name] = functions_matching

        return list(results.values())

    def detect(self):
        """
        Detect shadowing as a result of C3 linearization of contracts at the same inheritance depth-level.

        Recursively visit the calls
        Returns:
            list: {'vuln', 'filename,'contract','func', 'shadows'}

        """

        results = []
        for contract in self.contracts:
            shadows = self.detect_shadowing_definitions(contract)
            if shadows:
                for shadow in shadows:
                    for (shadow_contract, shadow_function) in shadow:
                        results.append({'contract': shadow_function.contract.name,
                                        'function': shadow_function.full_name})

        return results
