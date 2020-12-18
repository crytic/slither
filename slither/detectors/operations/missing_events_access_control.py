"""
Module detecting missing events for critical contract parameters set by owners and used in access control

"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.analyses.data_dependency.data_dependency import is_tainted
from slither.slithir.operations.event_call import EventCall
from slither.core.solidity_types.elementary_type import ElementaryType


class MissingEventsAccessControl(AbstractDetector):
    """
    Missing events for critical contract parameters set by owners and used in access control
    """

    ARGUMENT = "events-access"
    HELP = "Missing Events Access Control"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#missing-events-access-control"
    WIKI_TITLE = "Missing events access control"
    WIKI_DESCRIPTION = "Detect missing events for critical access control parameters"
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract C {

  modifier onlyAdmin {
    if (msg.sender != owner) throw;
    _;
  }

  function updateOwner(address newOwner) onlyAdmin external {
    owner = newOwner;
  }
}
```
`updateOwner()` has no event, so it is difficult to track off-chain owner changes.
"""

    WIKI_RECOMMENDATION = "Emit an event for critical parameter changes."

    @staticmethod
    def _detect_missing_events(contract):
        """
        Detects if critical contract parameters set by owners and used in access control are missing events
        :param contract: The contract to check
        :return: Functions with nodes of critical operations but no events
        """
        results = []

        # pylint: disable=too-many-nested-blocks
        for function in contract.functions_entry_points:
            nodes = []

            # Check for any events in the function and skip if found
            # Note: not checking if event corresponds to critical parameter
            if any(ir for node in function.nodes for ir in node.irs if isinstance(ir, EventCall)):
                continue

            # Ignore constructors and private/internal functions
            # Heuristic-1: functions with critical operations are typically "protected". Skip unprotected functions.
            if function.is_constructor or not function.is_protected():
                continue

            # Heuristic-2: Critical operations are where state variables are written and tainted
            # Heuristic-3: Variables of interest are address type that are used in modifiers i.e. access control
            # Heuristic-4: Critical operations present but no events in the function is not a good practice
            for node in function.nodes:
                for sv in node.state_variables_written:
                    if is_tainted(sv, function) and sv.type == ElementaryType("address"):
                        for mod in function.contract.modifiers:
                            if sv in mod.state_variables_read:
                                nodes.append((node, sv, mod))
            if nodes:
                results.append((function, nodes))
        return results

    def _detect(self):
        """Detect missing events for critical contract parameters set by owners and used in access control
        Returns:
            list: {'(function, node)'}
        """

        # Check derived contracts for missing events
        results = []
        for contract in self.slither.contracts_derived:
            missing_events = self._detect_missing_events(contract)
            for (function, nodes) in missing_events:
                info = [function, " should emit an event for: \n"]
                for (node, _sv, _mod) in nodes:
                    info += ["\t- ", node, " \n"]
                res = self.generate_result(info)
                results.append(res)
        return results
