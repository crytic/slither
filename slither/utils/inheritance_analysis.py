
class InheritanceAnalysis:
    """
    Detects various properties of inheritance in a slither project.
    """

    @staticmethod
    def detect_c3_function_shadowing(contract):
        """
        Detects and obtains functions which are indirectly shadowed via multiple inheritance by C3 linearization
        properties, despite not directly inheriting from each other.

        :param contract: The contract to check for potential C3 linearization shadowing within.
        :return: A list of list of tuples: (contract, function), where each inner list describes colliding functions.
        The later elements in the inner list overshadow the earlier ones. The contract-function pair's function does not
        need to be defined in its paired contract, it may have been inherited within it.
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

    @staticmethod
    def detect_direct_function_shadowing(contract):
        """
        Detects and obtains functions which are shadowed immediately by the provided ancestor contract.
        :param contract: The ancestor contract which we check for function shadowing within.
        :return: A list of tuples (overshadowing_function, overshadowed_immediate_base_contract, overshadowed_function)
        -overshadowing_function is the function defined within the provided contract that overshadows another
        definition.
        -overshadowed_immediate_base_contract is the immediate inherited-from contract that provided the shadowed
        function (could have provided it through inheritance, does not need to directly define it).
        -overshadowed_function is the function definition which is overshadowed by the provided contract's definition.
        """
        functions_declared = {function.full_name: function for function in contract.functions_and_modifiers_not_inherited}
        results = {}
        for base_contract in reversed(contract.immediate_inheritance):
            for base_function in base_contract.functions_and_modifiers:

                # We already found the most immediate shadowed definition for this function, skip to the next.
                if base_function.full_name in results:
                    continue

                # If this function is implemented and it collides with a definition in our immediate contract, we add
                # it to our results.
                if base_function.is_implemented and base_function.full_name in functions_declared:
                    results[base_function.full_name] = (functions_declared[base_function.full_name], base_contract, base_function)

        return list(results.values())

    @staticmethod
    def detect_function_shadowing(contracts, direct_shadowing=True, indirect_shadowing=True):
        """
        Detects all overshadowing and overshadowed functions in the provided contracts.
        :param contracts: The contracts to detect shadowing within.
        :param direct_shadowing: Include results from direct inheritance/inheritance ancestry.
        :param indirect_shadowing: Include results from indirect inheritance collisions as a result of multiple
        inheritance/c3 linearization.
        :return: Returns a set of tuples(overshadowing_contract, overshadowing_function, overshadowed_contract, overshadowed_function).
        The contract-function pair's function does not need to be defined in its paired contract, it may have been
        inherited within it.
        """
        results = set()
        for contract in contracts:

            # Detect immediate inheritance shadowing.
            shadows = InheritanceAnalysis.detect_direct_function_shadowing(contract)

            for (overshadowing_function, overshadowed_base_contract, overshadowed_function) in shadows:
                results.add((contract, overshadowing_function, overshadowed_base_contract, overshadowed_function))

            # Detect c3 linearization shadowing (multi inheritance shadowing).
            shadows = InheritanceAnalysis.detect_c3_function_shadowing(contract)
            for colliding_functions in shadows:
                for i in range(0, len(colliding_functions) - 1):
                    if colliding_functions[i][1] != colliding_functions[-1][1]:
                        results.add((colliding_functions[-1][0], colliding_functions[-1][1],
                                     colliding_functions[i][0], colliding_functions[i][1]))

        return results
