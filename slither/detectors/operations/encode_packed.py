"""
Module detecting usage of more than one dynamic type in abi.encodePacked() arguments which could lead to collision
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.slithir.operations import SolidityCall
from slither.analyses.data_dependency.data_dependency import is_tainted
from slither.core.solidity_types import ElementaryType
from slither.core.solidity_types import ArrayType


def _is_dynamic_type(arg):
    """
    Args:
        arg (function argument)
    Returns:
        Bool
    """
    if isinstance(arg.type, ElementaryType) and (arg.type.name in ["string", "bytes"]):
        return True
    if isinstance(arg.type, ArrayType) and arg.type.length is None:
        return True

    return False


def _detect_abi_encodePacked_collision(contract):
    """
    Args:
        contract (Contract)
    Returns:
        list((Function), (list (Node)))
    """
    ret = []
    # pylint: disable=too-many-nested-blocks
    for f in contract.functions_and_modifiers_declared:
        for n in f.nodes:
            for ir in n.irs:
                if isinstance(ir, SolidityCall) and ir.function == SolidityFunction(
                    "abi.encodePacked()"
                ):
                    dynamic_type_count = 0
                    for arg in ir.arguments:
                        if is_tainted(arg, contract) and _is_dynamic_type(arg):
                            dynamic_type_count += 1
                        elif dynamic_type_count > 1:
                            ret.append((f, n))
                            dynamic_type_count = 0
                        else:
                            dynamic_type_count = 0
                    if dynamic_type_count > 1:
                        ret.append((f, n))
    return ret


class EncodePackedCollision(AbstractDetector):
    """
    Detect usage of more than one dynamic type in abi.encodePacked() arguments which could to collision
    """

    ARGUMENT = "encode-packed-collision"
    HELP = "ABI encodePacked Collision"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#abi-encodePacked-collision"
    )

    WIKI_TITLE = "ABI encodePacked Collision"
    WIKI_DESCRIPTION = """Detect collision due to dynamic type usages in `abi.encodePacked`"""

    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Sign {
    function get_hash_for_signature(string name, string doc) external returns(bytes32) {
        return keccak256(abi.encodePacked(name, doc));
    }
}
```
Bob calls `get_hash_for_signature` with (`bob`, `This is the content`). The hash returned is used as an ID.
Eve creates a collision with the ID using (`bo`, `bThis is the content`) and compromises the system.
"""
    WIKI_RECOMMENDATION = """Do not use more than one dynamic type in `abi.encodePacked()`
(see the [Solidity documentation](https://solidity.readthedocs.io/en/v0.5.10/abi-spec.html?highlight=abi.encodePacked#non-standard-packed-modeDynamic)). 
Use `abi.encode()`, preferably."""

    def _detect(self):
        """Detect usage of more than one dynamic type in abi.encodePacked(..) arguments which could lead to collision"""
        results = []
        for c in self.compilation_unit.contracts:
            values = _detect_abi_encodePacked_collision(c)
            for func, node in values:
                info = [
                    func,
                    " calls abi.encodePacked() with multiple dynamic arguments:\n\t- ",
                    node,
                    "\n",
                ]
                json = self.generate_result(info)
                results.append(json)

        return results
