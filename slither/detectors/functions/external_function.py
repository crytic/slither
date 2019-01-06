from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.slithir.operations import (HighLevelCall, SolidityCall )
from slither.slithir.operations import (InternalCall, InternalDynamicCall)

class ExternalFunction(AbstractDetector):
    """
    Detect public function that could be declared as external

    IMPROVEMENT: Add InternalDynamicCall check
    https://github.com/trailofbits/slither/pull/53#issuecomment-432809950
    """

    ARGUMENT = 'external-function'
    HELP = 'Public function that could be declared as external'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#public-function-that-could-be-declared-as-external'

    @staticmethod
    def detect_functions_called(contract):
        """ Returns a list of InternallCall, SolidityCall
            calls made in a function

        Returns:
            (list): List of all InternallCall, SolidityCall
        """
        result = []

        # Obtain all functions reachable by this contract.
        for func in contract.all_functions_called:
            # Loop through all nodes in the function, add all calls to a list.
            for node in func.nodes:
                for ir in node.irs:
                    if isinstance(ir, (InternalCall, SolidityCall)):
                        result.append(ir.function)
        return result

    @staticmethod
    def _contains_internal_dynamic_call(contract):
        """
        Checks if a contract contains a dynamic call either in a direct definition, or through inheritance.

        Returns:
            (boolean): True if this contract contains a dynamic call (including through inheritance).
        """
        for func in contract.all_functions_called:
            for node in func.nodes:
                for ir in node.irs:
                    if isinstance(ir, (InternalDynamicCall)):
                        return True
        return False

    @staticmethod
    def get_base_most_function(function):
        """
        Obtains the base function definition for the provided function. This could be used to obtain the original
        definition of a function, if the provided function is an override.

        Returns:
            (function): Returns the base-most function of a provided function. (The original definition).
        """
        # Loop through the list of inherited contracts and this contract, to find the first function instance which
        # matches this function's signature. Note here that `inheritance` is in order from most basic to most extended.
        for contract in function.contract.inheritance + [function.contract]:

            # Loop through the functions not inherited (explicitly defined in this contract).
            for f in contract.functions_not_inherited:

                # If it matches names, this is the base most function.
                if f.full_name == function.full_name:
                    return f

        # Somehow we couldn't resolve it, which shouldn't happen, as the provided function should be found if we could
        # not find some any more basic.
        raise Exception("Could not resolve the base-most function for the provided function.")

    @staticmethod
    def get_all_function_definitions(base_most_function):
        """
        Obtains all function definitions given a base-most function. This includes the provided function, plus any
        overrides of that function.

        Returns:
            (list): Returns any the provided function and any overriding functions defined for it.
        """
        # We assume the provided function is the base-most function, so we check all derived contracts
        # for a redefinition
        return [base_most_function] + [function for derived_contract in base_most_function.contract.derived_contracts
                                       for function in derived_contract.functions
                                       if function.full_name == base_most_function.full_name]

    def detect(self):
        results = []

        all_info = ''

        # Create a set to track contracts with dynamic calls. All contracts with dynamic calls could potentially be
        # calling functions internally, and thus we can't assume any function in such contracts isn't called by them.
        dynamic_call_contracts = set()

        # Create a completed functions set to skip over functions already processed (any functions which are the base
        # of, or override hierarchically are processed together).
        completed_functions = set()

        # First we build our set of all contracts with dynamic calls
        for contract in self.contracts:
            if self._contains_internal_dynamic_call(contract):
                dynamic_call_contracts.add(contract)

        # Loop through all not-inherited contracts.
        for contract in self.slither.contracts_derived:

            # Filter false-positives: Immediately filter this contract if it's in blacklist
            if contract in dynamic_call_contracts:
                continue

            # Next we'll want to loop through all functions defined directly in this contract.
            for function in contract.functions_not_inherited:

                # If the function is a constructor, or is public, we skip it.
                if function.is_constructor or function.visibility != "public":
                    continue

                # Optimization: If this function has already been processed, we stop.
                if function in completed_functions:
                    continue

                # Get the base-most function to know our origin of this function.
                base_most_function = self.get_base_most_function(function)

                # Get all possible contracts which can call this function (or an override).
                all_possible_sources = [base_most_function.contract] + base_most_function.contract.derived_contracts

                # Get all function signatures (overloaded and not), mark as completed and we process them now.
                # Note: We mark all function definitions as the same, as they must all share visibility to override.
                all_function_definitions = set(self.get_all_function_definitions(base_most_function))
                completed_functions = completed_functions.union(all_function_definitions)

                # Filter false-positives: Determine if any of these sources have dynamic calls, if so, flag all of these
                # function definitions, and then flag all functions in all contracts that make dynamic calls.
                sources_with_dynamic_calls = set(all_possible_sources) & dynamic_call_contracts
                if sources_with_dynamic_calls:
                    functions_in_dynamic_call_sources = set([f for dyn_contract in sources_with_dynamic_calls
                                                             for f in dyn_contract if not f.is_constructor])
                    completed_functions = completed_functions.union(functions_in_dynamic_call_sources)
                    continue

                # Detect all functions called in each source, if any match our current signature, we skip
                # otherwise, this is a candidate (in all sources) to be changed visibility for.
                is_called = False
                for possible_source in all_possible_sources:
                    functions_called = self.detect_functions_called(possible_source)
                    if set(functions_called) & all_function_definitions:
                        is_called = True
                        break

                # If any of this function's definitions are called, we skip it.
                if is_called:
                    continue

                # Loop for each function definition, and recommend it be declared external.
                for function_definition in all_function_definitions:
                    txt = "{}.{} ({}) should be declared external\n"
                    info = txt.format(function_definition.contract.name,
                                      function_definition.name,
                                      function_definition.source_mapping_str)
                    all_info += info

                    json = self.generate_json_result(info)
                    self.add_function_to_json(function_definition, json)
                    results.append(json)

        if all_info != '':
            self.log(all_info)
        return results
