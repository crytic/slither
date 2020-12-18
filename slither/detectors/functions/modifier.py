"""
Module detecting modifiers that are not guaranteed to execute _; or revert()/throw

Note that require()/assert() are not considered here. Even if they
are in the outermost scope, they do not guarantee a revert, so a
default value can still be returned.
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.cfg.node import NodeType


def is_revert(node):
    return node.type == NodeType.THROW or any(
        c.name in ["revert()", "revert(string"] for c in node.internal_calls
    )


def _get_false_son(node):
    """Select the son node corresponding to a false branch
    Following this node stays on the outer scope of the function
    """
    if node.type == NodeType.IF:
        return node.sons[1]

    if node.type == NodeType.IFLOOP:
        return next(s for s in node.sons if s.type == NodeType.ENDLOOP)

    return None


class ModifierDefaultDetection(AbstractDetector):
    """
    Detector for modifiers that return a default value
    """

    ARGUMENT = "incorrect-modifier"
    HELP = "Modifiers that can return the default value"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH
    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-modifier"

    WIKI_TITLE = "Incorrect modifier"
    WIKI_DESCRIPTION = "If a modifier does not execute `_` or revert, the execution of the function will return the default value, which can be misleading for the caller."
    WIKI_EXPLOIT_SCENARIO = """
```solidity
    modidfier myModif(){
        if(..){
           _;
        }
    }
    function get() myModif returns(uint){

    }
```
If the condition in `myModif` is false, the execution of `get()` will return 0."""

    WIKI_RECOMMENDATION = "All the paths in a modifier must execute `_` or revert."

    def _detect(self):
        results = []
        for c in self.contracts:
            for mod in c.modifiers:
                if mod.contract_declarer != c:
                    continue
                # Walk down the tree, only looking at nodes in the outer scope
                node = mod.entry_point
                while node is not None:
                    # If any node in the outer scope executes _; or reverts,
                    # we will never return a default value
                    if node.type == NodeType.PLACEHOLDER or is_revert(node):
                        break

                    # Move down, staying on the outer scope in branches
                    if len(node.sons) > 0:
                        node = _get_false_son(node) if node.contains_if() else node.sons[0]
                    else:
                        node = None
                else:
                    # Nothing was found in the outer scope
                    info = ["Modifier ", mod, " does not always execute _; or revert"]

                    res = self.generate_result(info)
                    results.append(res)

        return results
