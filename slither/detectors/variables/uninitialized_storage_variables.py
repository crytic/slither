"""
    Module detecting uninitialized storage variables

    Recursively explore the CFG to only report uninitialized storage variables that are
    written before being read
"""
from typing import List

from slither.core.cfg.node import Node
from slither.core.declarations.function_contract import FunctionContract
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.output import Output


class UninitializedStorageVars(AbstractDetector):

    ARGUMENT = "uninitialized-storage"
    HELP = "Uninitialized storage variables"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#uninitialized-storage-variables"

    WIKI_TITLE = "Uninitialized storage variables"
    WIKI_DESCRIPTION = "An uninitialized storage variable will act as a reference to the first state variable, and can override a critical variable."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Uninitialized{
    address owner = msg.sender;

    struct St{
        uint a;
    }

    function func() {
        St st;
        st.a = 0x0;
    }
}
```
Bob calls `func`. As a result, `owner` is overridden to `0`.
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Initialize all storage variables."

    # node.context[self.key] contains the uninitialized storage variables
    key = "UNINITIALIZEDSTORAGE"

    def _detect_uninitialized(
        self, function: FunctionContract, node: Node, visited: List[Node]
    ) -> None:
        if node in visited:
            return

        visited = visited + [node]

        fathers_context = []

        for father in node.fathers:
            if self.key in father.context:
                fathers_context += father.context[self.key]

        # Exclude paths that dont bring further information
        if node in self.visited_all_paths:
            if all(f_c in self.visited_all_paths[node] for f_c in fathers_context):
                return
        else:
            self.visited_all_paths[node] = []

        self.visited_all_paths[node] = list(set(self.visited_all_paths[node] + fathers_context))

        if self.key in node.context:
            fathers_context += node.context[self.key]

        variables_read = node.variables_read
        for uninitialized_storage_variable in fathers_context:
            if uninitialized_storage_variable in variables_read:
                self.results.append((function, uninitialized_storage_variable))

        # Only save the storage variables that are not yet written
        uninitialized_storage_variables = list(set(fathers_context) - set(node.variables_written))
        node.context[self.key] = uninitialized_storage_variables

        for son in node.sons:
            self._detect_uninitialized(function, son, visited)

    def _detect(self) -> List[Output]:
        """Detect uninitialized storage variables

        Recursively visit the calls
        Returns:
            dict: [contract name] = set(storage variable uninitialized)
        """
        results = []

        # pylint: disable=attribute-defined-outside-init
        self.results = []
        self.visited_all_paths = {}

        for contract in self.compilation_unit.contracts:
            for function in contract.functions:
                if function.is_implemented and function.entry_point:
                    locals_except_params = set(function.variables) - set(function.parameters)
                    uninitialized_storage_variables = [
                        v for v in locals_except_params if v.is_storage and v.uninitialized
                    ]

                    function.entry_point.context[self.key] = uninitialized_storage_variables
                    self._detect_uninitialized(function, function.entry_point, [])

        for (function, uninitialized_storage_variable) in self.results:
            info = [
                uninitialized_storage_variable,
                " is a storage variable never initialized\n",
            ]
            json = self.generate_result(info)
            results.append(json)

        return results
