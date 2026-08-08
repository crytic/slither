"""
Module detecting unused events
"""

from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations.event_call import EventCall
from slither.utils.output import Output


class UnusedEvents(AbstractDetector):
    """
    Detect events that are declared but never emitted
    """

    ARGUMENT = "unused-events"
    HELP = "Events that are not emitted"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unused-events"

    WIKI_TITLE = "Unused events"
    WIKI_DESCRIPTION = "Detect events that are declared but never emitted."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Example {
    event Unused(address indexed user);
    event Used(uint256 value);

    function action() external {
        emit Used(100);
    }
}
```
`Unused` is never emitted and should be removed."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Remove unused events or emit them where appropriate."

    def _detect(self) -> list[Output]:
        results = []

        # Collect all emitted event names across the entire compilation unit
        events_emitted: set[str] = set()
        for contract in self.compilation_unit.contracts_derived:
            for function in contract.functions_and_modifiers:
                for node in function.nodes:
                    for ir in node.irs:
                        if isinstance(ir, EventCall):
                            events_emitted.add(str(ir.name))

        for contract in sorted(self.compilation_unit.contracts, key=lambda x: x.name):
            if contract.is_interface or contract.is_from_dependency():
                continue

            for event in sorted(contract.events_declared, key=lambda x: x.full_name):
                if event.name not in events_emitted:
                    info: DETECTOR_INFO = [
                        event,
                        " is never emitted in ",
                        contract,
                        "\n",
                    ]
                    res = self.generate_result(info)
                    results.append(res)

        return results
