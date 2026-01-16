"""
Detect events with address parameters that have no indexed parameters
"""

from slither.core.declarations.event import Event
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.output import Output


class UnindexedEventAddress(AbstractDetector):
    """
    Detect events with address parameters that have no indexed parameters.

    Indexing address parameters enables efficient off-chain filtering of events.
    """

    ARGUMENT = "unindexed-event-address"
    HELP = "Events with address parameters but no indexed parameters"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation"
        "#unindexed-event-address-parameters"
    )

    WIKI_TITLE = "Unindexed event address parameters"
    WIKI_DESCRIPTION = (
        "Detects events that have address-type parameters but no indexed parameters. "
        "Indexing event parameters enables efficient off-chain filtering."
    )

    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Token {
    event Transfer(address from, address to, uint256 value);

    function transfer(address to, uint256 value) external {
        // ...
        emit Transfer(msg.sender, to, value);
    }
}
```
The `Transfer` event has address parameters but none are indexed.
Off-chain tools cannot efficiently filter transfers by sender or recipient address."""

    WIKI_RECOMMENDATION = (
        "Add the `indexed` keyword to address parameters in events "
        "to enable efficient off-chain filtering."
    )

    @staticmethod
    def _has_unindexed_address(event: Event) -> bool:
        """
        Check if an event has address parameters but no indexed parameters.

        Args:
            event: The event to check.

        Returns:
            True if the event has address params but no indexed params.
        """
        has_address = False
        has_indexed = False

        for param in event.elems:
            if param.indexed:
                has_indexed = True
            if param.type == ElementaryType("address"):
                has_address = True

        return has_address and not has_indexed

    def _detect(self) -> list[Output]:
        """
        Detect events with address parameters but no indexed parameters.

        Returns:
            List of detection results.
        """
        results: list[Output] = []

        # Check contract-level events
        for contract in self.contracts:
            for event in contract.events_declared:
                if self._has_unindexed_address(event):
                    info = [
                        "Event ",
                        event,
                        " has address parameters but no indexed parameters\n",
                    ]
                    res = self.generate_result(info)
                    results.append(res)

        # Check top-level events
        for event in self.compilation_unit.events_top_level:
            if self._has_unindexed_address(event):
                info = [
                    "Event ",
                    event,
                    " has address parameters but no indexed parameters\n",
                ]
                res = self.generate_result(info)
                results.append(res)

        return results
