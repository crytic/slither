"""
Module detecting unused modifiers
"""

from slither.core.declarations import Modifier
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output


class UnusedModifiers(AbstractDetector):
    """
    Detect modifiers that are declared but never applied to any function
    """

    ARGUMENT = "unused-modifiers"
    HELP = "Modifiers that are not applied"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unused-modifiers"

    WIKI_TITLE = "Unused modifiers"
    WIKI_DESCRIPTION = "Detect modifiers that are declared but never applied to any function."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Example {
    modifier unused() {
        require(msg.sender == address(0));
        _;
    }

    modifier used() {
        require(msg.value > 0);
        _;
    }

    function pay() external payable used {
        // ...
    }
}
```
`unused` is never applied and should be removed."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Remove unused modifiers or apply them where appropriate."

    def _detect(self) -> list[Output]:
        results = []

        # Collect all modifiers that are applied to any function
        modifiers_used: set[str] = set()
        for contract in self.compilation_unit.contracts_derived:
            for function in contract.functions:
                for modifier in function.modifiers:
                    if isinstance(modifier, Modifier):
                        modifiers_used.add(modifier.canonical_name)

        # Collect virtual modifiers that are overridden in child contracts
        # (overridden_by may not be populated for modifiers, so check manually)
        overridden_modifiers: set[str] = set()
        for contract in self.compilation_unit.contracts:
            for inherited_mod in contract.modifiers_inherited:
                for declared_mod in contract.modifiers_declared:
                    if inherited_mod.name == declared_mod.name:
                        overridden_modifiers.add(inherited_mod.canonical_name)

        for modifier in sorted(
            self.compilation_unit.modifiers, key=lambda x: x.canonical_name
        ):
            if not isinstance(modifier, Modifier):
                continue

            if modifier.contract_declarer.is_from_dependency():
                continue

            if modifier.contract_declarer.is_interface:
                continue

            # Skip if the modifier is used
            if modifier.canonical_name in modifiers_used:
                continue

            # Skip if not implemented (abstract)
            if not modifier.is_implemented:
                continue

            # Skip virtual modifiers that are overridden in child contracts
            # (part of inheritance design pattern)
            if modifier.is_virtual and (
                modifier.overridden_by
                or modifier.canonical_name in overridden_modifiers
            ):
                continue

            info: DETECTOR_INFO = [
                modifier,
                " is never used and should be removed\n",
            ]
            res = self.generate_result(info)
            results.append(res)

        return results
