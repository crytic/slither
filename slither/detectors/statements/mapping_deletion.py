"""
Detect deletion on structure containing a mapping
"""

from slither.core.declarations import Structure
from slither.core.solidity_types import MappingType, UserDefinedType
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Delete


class MappingDeletionDetection(AbstractDetector):
    """
    Mapping deletion detector
    """

    ARGUMENT = "mapping-deletion"
    HELP = "Deletion on mapping containing a structure"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#deletion-on-mapping-containing-a-structure"

    WIKI_TITLE = "Deletion on mapping containing a structure"
    WIKI_DESCRIPTION = "A deletion in a structure containing a mapping will not delete the mapping (see the [Solidity documentation](https://solidity.readthedocs.io/en/latest/types.html##delete)). The remaining data may be used to compromise the contract."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
    struct BalancesStruct{
        address owner;
        mapping(address => uint) balances;
    }
    mapping(address => BalancesStruct) public stackBalance;

    function remove() internal{
         delete stackBalance[msg.sender];
    }
```
`remove` deletes an item of `stackBalance`.
The mapping `balances` is never deleted, so `remove` does not work as intended."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = (
        "Use a lock mechanism instead of a deletion to disable structure containing a mapping."
    )

    @staticmethod
    def detect_mapping_deletion(contract):
        """Detect deletion on structure containing a mapping

        Returns:
            list (function, structure, node)
        """
        ret = []
        # pylint: disable=too-many-nested-blocks
        for f in contract.functions:
            for node in f.nodes:
                for ir in node.irs:
                    if isinstance(ir, Delete):
                        value = ir.variable
                        if isinstance(value.type, UserDefinedType) and isinstance(
                            value.type.type, Structure
                        ):
                            st = value.type.type
                            if any(isinstance(e.type, MappingType) for e in st.elems.values()):
                                ret.append((f, st, node))
        return ret

    def _detect(self):
        """Detect mapping deletion

        Returns:
            list: {'vuln', 'filename,'contract','func','struct''}
        """
        results = []
        for c in self.contracts:
            mapping = MappingDeletionDetection.detect_mapping_deletion(c)
            for (func, struct, node) in mapping:
                info = [func, " deletes ", struct, " which contains a mapping:\n"]
                info += ["\t-", node, "\n"]

                res = self.generate_result(info)
                results.append(res)

        return results
