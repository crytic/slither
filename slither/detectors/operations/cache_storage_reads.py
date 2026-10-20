from slither.core.cfg.node import Node, NodeType
from slither.core.declarations import Function
from slither.core.solidity_types import ElementaryType
from slither.core.variables import StateVariable
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Call
from slither.utils.output import Output


def _isolated_loop_nodes(function: Function) -> list[Node]:
    starts = [n for n in function.nodes if n.type is NodeType.STARTLOOP]
    if len(starts) != 1 or function.contains_assembly or function.modifiers:
        return []
    if any(isinstance(ir, Call) for n in function.nodes for ir in n.irs):
        return []
    pending = list(starts[0].sons)
    visited: set[Node] = set()
    while pending:
        node = pending.pop()
        if node in visited or node.type is NodeType.ENDLOOP:
            continue
        visited.add(node)
        pending.extend(node.sons)
    return sorted(visited, key=lambda n: n.node_id)


def _is_stored_scalar(variable: StateVariable) -> bool:
    return (
        variable.is_stored
        and isinstance(variable.type, ElementaryType)
        and not variable.type.storage_size[1]
    )


class GasCacheStorageReads(AbstractDetector):
    ARGUMENT = "cache-storage-reads"
    HELP = "Invariant scalar storage reads inside isolated loops"
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM
    LANGUAGE = "solidity"
    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#cache-storage-reads"
    WIKI_TITLE = "Cache storage reads"
    WIKI_DESCRIPTION = (
        "Finds scalar storage reads repeated by a single loop when the function never writes "
        "that variable. Excludes all calls, modifiers, assembly, nested loops, constants, "
        "immutables and reference types. Compiler optimizations may already hoist these reads."
    )
    WIKI_EXPLOIT_SCENARIO = """
```solidity
for (uint256 i; i < count; ++i) { sum += value; }
// Cache value before the loop when it is invariant and the compiler does not.
```
"""
    WIKI_RECOMMENDATION = (
        "Consider caching the value in a local of the same type immediately before the loop. Inspect generated "
        "code and benchmark first: no saving is claimed when the compiler already caches it."
    )

    def _detect(self) -> list[Output]:
        results = []
        for function in self.compilation_unit.functions:
            nodes = _isolated_loop_nodes(function)
            reads = {v for n in nodes for v in n.state_variables_read if _is_stored_scalar(v)}
            for variable in sorted(reads, key=lambda v: v.canonical_name):
                if variable in function.state_variables_written:
                    continue
                results.append(
                    self.generate_result(
                        [
                            function,
                            " repeatedly reads invariant storage variable ",
                            variable,
                            " in loop ",
                            nodes[0],
                            "; consider a local cache if the compiler does not already hoist the read.\n",
                        ]
                    )
                )
        return sorted(results, key=lambda r: r.data["description"])
