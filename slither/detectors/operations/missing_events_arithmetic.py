"""
Module detecting missing events for critical contract parameters set by owners and used in arithmetic

"""
from typing import List, Tuple

from slither.analyses.data_dependency.data_dependency import is_tainted
from slither.core.cfg.node import Node
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract
from slither.core.solidity_types.elementary_type import ElementaryType, Int, Uint
from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations.event_call import EventCall
from slither.utils.output import Output


class MissingEventsArithmetic(AbstractDetector):
    """
    Missing events for critical contract parameters set by owners and used in arithmetic
    """

    ARGUMENT = "events-maths"
    HELP = "Missing Events Arithmetic"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#missing-events-arithmetic"
    WIKI_TITLE = "Missing events arithmetic"
    WIKI_DESCRIPTION = "Detect missing events for critical arithmetic parameters."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract C {

    modifier onlyOwner {
        if (msg.sender != owner) throw;
        _;
    }

    function setBuyPrice(uint256 newBuyPrice) onlyOwner public {
        buyPrice = newBuyPrice;
    }

    function buy() external {
     ... // buyPrice is used to determine the number of tokens purchased
    }    
}
```
`setBuyPrice()` does not emit an event, so it is difficult to track changes in the value of `buyPrice` off-chain. 
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Emit an event for critical parameter changes."

    @staticmethod
    def _detect_unprotected_use(
        contract: Contract, sv: StateVariable
    ) -> List[Tuple[Node, FunctionContract]]:
        unprotected_functions = [
            function for function in contract.functions_declared if not function.is_protected()
        ]
        return [
            (node, function)
            for function in unprotected_functions
            for node in function.nodes
            if sv in node.state_variables_read
        ]

    def _detect_missing_events(
        self, contract: Contract
    ) -> List[Tuple[FunctionContract, List[Tuple[Node, List[Tuple[Node, FunctionContract]]]]]]:
        """
        Detects if critical contract parameters set by owners and used in arithmetic are missing events
        :param contract: The contract to check
        :return: Functions with nodes of critical operations but no events
        """
        results = []

        for function in contract.functions_entry_points:
            nodes = []

            # Check for any events in the function and skip if found
            # Note: not checking if event corresponds to critical parameter
            if any(ir for node in function.nodes for ir in node.irs if isinstance(ir, EventCall)):
                continue

            # Ignore constructors and private/internal functions
            # Heuristic-1: functions writing to critical parameters are typically "protected".
            # Skip unprotected functions.
            if function.is_constructor or not function.is_protected():
                continue

            # Heuristic-2: Critical operations are where state variables are written and tainted
            # Heuristic-3: Variables of interest are int/uint types that are used (mostly in arithmetic)
            # in other unprotected functions
            # Heuristic-4: Critical operations present but no events in the function is not a good practice
            for node in function.nodes:
                for sv in node.state_variables_written:
                    if (
                        is_tainted(sv, function)
                        and isinstance(sv.type, ElementaryType)
                        and sv.type.type in Int + Uint
                    ):
                        used_nodes = self._detect_unprotected_use(contract, sv)
                        if used_nodes:
                            nodes.append((node, used_nodes))

            if nodes:
                results.append((function, nodes))
        return results

    def _detect(self) -> List[Output]:
        """Detect missing events for critical contract parameters set by owners and used in arithmetic
        Returns:
            list: {'(function, node)'}
        """

        # Check derived contracts for missing events
        results = []
        for contract in self.compilation_unit.contracts_derived:
            missing_events = self._detect_missing_events(contract)
            for (function, nodes) in missing_events:
                info: DETECTOR_INFO = [function, " should emit an event for: \n"]
                for (node, _) in nodes:
                    info += ["\t- ", node, " \n"]
                res = self.generate_result(info)
                results.append(res)
        return results
