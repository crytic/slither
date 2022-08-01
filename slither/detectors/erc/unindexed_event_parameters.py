"""
Detect mistakenly un-indexed ERC20 event parameters
"""
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class UnindexedERC20EventParameters(AbstractDetector):
    """
    Un-indexed ERC20 event parameters
    """

    ARGUMENT = "erc20-indexed"
    HELP = "Un-indexed ERC20 event parameters"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unindexed-erc20-event-parameters"

    WIKI_TITLE = "Unindexed ERC20 event parameters"
    WIKI_DESCRIPTION = "Detects whether events defined by the `ERC20` specification that should have some parameters as `indexed` are missing the `indexed` keyword."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract ERC20Bad {
    // ...
    event Transfer(address from, address to, uint value);
    event Approval(address owner, address spender, uint value);

    // ...
}
```
`Transfer` and `Approval` events should have the 'indexed' keyword on their two first parameters, as defined by the `ERC20` specification.
Failure to include these keywords will exclude the parameter data in the transaction/block's bloom filter, so external tooling searching for these parameters may overlook them and fail to index logs from this token contract."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Add the `indexed` keyword to event parameters that should include it, according to the `ERC20` specification."

    STANDARD_JSON = False

    @staticmethod
    def detect_erc20_unindexed_event_params(contract):
        """
        Detect un-indexed ERC20 event parameters in a given contract.
        :param contract: The contract to check ERC20 events for un-indexed parameters in.
        :return: A list of tuple(event, parameter) of parameters which should be indexed.
        """
        # Create our result array
        results = []

        # If this contract isn't an ERC20 token, we return our empty results.
        if not contract.is_erc20():
            return results

        # Loop through all events to look for poor form.
        for event in contract.events_declared:

            # If this is transfer/approval events, expect the first two parameters to be indexed.
            if event.full_name in [
                "Transfer(address,address,uint256)",
                "Approval(address,address,uint256)",
            ]:
                if not event.elems[0].indexed:
                    results.append((event, event.elems[0]))
                if not event.elems[1].indexed:
                    results.append((event, event.elems[1]))

        # Return the results.
        return results

    def _detect(self):
        """
        Detect un-indexed ERC20 event parameters in all contracts.
        """
        results = []
        for c in self.contracts:
            unindexed_params = self.detect_erc20_unindexed_event_params(c)
            if unindexed_params:
                # Add each problematic event definition to our result list
                for (event, parameter) in unindexed_params:

                    info = [
                        "ERC20 event ",
                        event,
                        f"does not index parameter {parameter}\n",
                    ]

                    # Add the events to the JSON (note: we do not add the params/vars as they have no source mapping).
                    res = self.generate_result(info)

                    res.add(event, {"parameter_name": parameter.name})
                    results.append(res)

        return results
