"""
Module detecting any path leading to usage of a local variable before it is declared.
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class PredeclarationUsageLocal(AbstractDetector):
    """
    Pre-declaration usage of local variable
    """

    ARGUMENT = "variable-scope"
    HELP = "Local variables used prior their declaration"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#pre-declaration-usage-of-local-variables"

    WIKI_TITLE = "Pre-declaration usage of local variables"
    WIKI_DESCRIPTION = "Detects the possible usage of a variable before the declaration is stepped over (either because it is later declared, or declared in another scope)."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract C {
    function f(uint z) public returns (uint) {
        uint y = x + 9 + z; // 'z' is used pre-declaration
        uint x = 7;

        if (z % 2 == 0) {
            uint max = 5;
            // ...
        }

        // 'max' was intended to be 5, but it was mistakenly declared in a scope and not assigned (so it is zero).
        for (uint i = 0; i < max; i++) {
            x += 1;
        }

        return x;
    }
}
```
In the case above, the variable `x` is used before its declaration, which may result in unintended consequences. 
Additionally, the for-loop uses the variable `max`, which is declared in a previous scope that may not always be reached. This could lead to unintended consequences if the user mistakenly uses a variable prior to any intended declaration assignment. It also may indicate that the user intended to reference a different variable."""
    # endregion wiki_exploit_scenario
    
    WIKI_RECOMMENDATION = "Move all variable declarations prior to any usage of the variable, and ensure that reaching a variable declaration does not depend on some conditional if it is used unconditionally."

    def detect_predeclared_local_usage(self, node, results, already_declared, visited):
        """
        Detects if a given node uses a variable prior to declaration in any code path.
        :param node: The node to initiate the scan from (searches recursively through all sons)
        :param already_declared: A set of variables already known to be declared in this path currently.
        :param already_visited: A set of nodes already visited in this path currently.
        :param results: A list of tuple(node, local_variable) denoting nodes which used a variable before declaration.
        :return: None
        """

        if node in visited:
            return

        visited = visited | {node}

        if node.variable_declaration:
            already_declared = already_declared | {node.variable_declaration}

        if not node in self.fix_point_information:
            self.fix_point_information[node] = []

        # If we already explored this node with the same information
        if already_declared:
            for fix_point in self.fix_point_information[node]:
                if fix_point == already_declared:
                    return

        if already_declared:
            self.fix_point_information[node] += [already_declared]

        for variable in set(node.local_variables_read + node.local_variables_written):
            if variable not in already_declared:
                result = (node, variable)
                if result not in results:
                    results.append(result)

        for son in node.sons:
            self.detect_predeclared_local_usage(son, results, already_declared, visited)

    def detect_predeclared_in_contract(self, contract):
        """
        Detects and returns all nodes in a contract which use a variable before it is declared.
        :param contract: Contract to detect pre-declaration usage of locals within.
        :return: A list of tuples: (function, list(tuple(node, local_variable)))
        """

        # Create our result set.
        results = []

        # Loop for each function and modifier's nodes and analyze for predeclared local variable usage.
        for function in contract.functions_and_modifiers_declared:
            predeclared_usage = []
            if function.nodes:
                self.detect_predeclared_local_usage(
                    function.nodes[0],
                    predeclared_usage,
                    set(function.parameters + function.returns),
                    set(),
                )
            if predeclared_usage:
                results.append((function, predeclared_usage))

        # Return the resulting set of nodes which set array length.
        return results

    def _detect(self):
        """
        Detect usage of a local variable before it is declared.
        """
        results = []

        # Fix_point_information contains a list of set
        # Each set contains the already declared variables saw in one path
        # If a path has the same set as a path already explored
        # We don't need to continue
        # pylint: disable=attribute-defined-outside-init
        self.fix_point_information = {}

        for contract in self.contracts:
            predeclared_usages = self.detect_predeclared_in_contract(contract)
            if predeclared_usages:
                for (predeclared_usage_function, predeclared_usage_nodes) in predeclared_usages:
                    for (
                        predeclared_usage_node,
                        predeclared_usage_local_variable,
                    ) in predeclared_usage_nodes:
                        info = [
                            "Variable '",
                            predeclared_usage_local_variable,
                            "' in ",
                            predeclared_usage_function,
                            " potentially used before declaration: ",
                            predeclared_usage_node,
                            "\n",
                        ]

                        res = self.generate_result(info)
                        results.append(res)

        return results
