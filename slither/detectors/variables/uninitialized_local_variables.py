"""
    Module detecting uninitialized local variables

    Recursively explore the CFG to only report uninitialized local variables that are
    read before being written
"""
from typing import List

from slither.core.cfg.node import Node, NodeType
from slither.core.declarations.function_contract import FunctionContract
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.output import Output


class UninitializedLocalVars(AbstractDetector):

    ARGUMENT = "uninitialized-local"
    HELP = "Uninitialized local variables"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#uninitialized-local-variables"

    WIKI_TITLE = "Uninitialized local variables"
    WIKI_DESCRIPTION = "Uninitialized local variables."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Uninitialized is Owner{
    function withdraw() payable public onlyOwner{
        address to;
        to.transfer(this.balance)
    }
}
```
Bob calls `transfer`. As a result, all Ether is sent to the address `0x0` and is lost."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Initialize all the variables. If a variable is meant to be initialized to zero, explicitly set it to zero to improve code readability."

    key = "UNINITIALIZEDLOCAL"

    def _detect_uninitialized(
        self, function: FunctionContract, node: Node, visited: List[Node]
    ) -> None:
        if node in visited:
            return

        visited = visited + [node]

        predecessors_context = []

        for predecessor in node.predecessors:
            if self.key in predecessor.context:
                predecessors_context += predecessor.context[self.key]

        # Exclude path that dont bring further information
        if node in self.visited_all_paths:
            if all(f_c in self.visited_all_paths[node] for f_c in predecessors_context):
                return
        else:
            self.visited_all_paths[node] = []

        self.visited_all_paths[node] = list(
            set(self.visited_all_paths[node] + predecessors_context)
        )

        # Remove a local variable declared in a for loop header
        if (
            node.type == NodeType.VARIABLE
            and len(node.successors)
            == 1  # Should always be true for a node that has a STARTLOOP successor
            and node.successors[0].type == NodeType.STARTLOOP
        ):
            if node.variable_declaration in predecessors_context:
                predecessors_context.remove(node.variable_declaration)

        if self.key in node.context:
            predecessors_context += node.context[self.key]

        variables_read = node.variables_read
        for uninitialized_local_variable in predecessors_context:
            if uninitialized_local_variable in variables_read:
                self.results.append((function, uninitialized_local_variable))

        # Only save the local variables that are not yet written
        uninitialized_local_variables = list(
            set(predecessors_context) - set(node.variables_written)
        )
        node.context[self.key] = uninitialized_local_variables

        for successor in node.successors:
            self._detect_uninitialized(function, successor, visited)

    def _detect(self) -> List[Output]:
        """Detect uninitialized local variables

        Recursively visit the calls
        Returns:
            dict: [contract name] = set(local variable uninitialized)
        """
        results = []

        # pylint: disable=attribute-defined-outside-init
        self.results = []
        self.visited_all_paths = {}

        for contract in self.compilation_unit.contracts:
            for function in contract.functions:
                if (
                    function.is_implemented
                    and function.contract_declarer == contract
                    and function.entry_point
                ):
                    if function.contains_assembly:
                        continue
                    # dont consider storage variable, as they are detected by another detector
                    uninitialized_local_variables = [
                        v for v in function.local_variables if not v.is_storage and v.uninitialized
                    ]
                    function.entry_point.context[self.key] = uninitialized_local_variables
                    self._detect_uninitialized(function, function.entry_point, [])
        all_results = list(set(self.results))
        for (function, uninitialized_local_variable) in all_results:

            info = [
                uninitialized_local_variable,
                " is a local variable never initialized\n",
            ]
            json = self.generate_result(info)
            results.append(json)

        return results
