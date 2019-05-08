"""
Detect mistakenly un-indexed ERC20 event parameters
"""
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class UnindexedERC20EventParameters(AbstractDetector):
    """
    Un-indexed ERC20 event parameters
    """

    ARGUMENT = 'erc20-indexed'
    HELP = 'Un-indexed ERC20 event parameters'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#unindexed-erc20-event-parameters'

    WIKI_TITLE = 'Unindexed ERC20 Event Parameters'
    WIKI_DESCRIPTION = 'Detects that events defined by the ERC20 specification which are meant to have some parameters as `indexed`, are missing the `indexed` keyword.'
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract ERC20Bad {
    // ...
    event Transfer(address from, address to, uint value);
    event Approval(address owner, address spender, uint value);

    // ...
}
```
In this case, Transfer and Approval events should have the 'indexed' keyword on their two first parameters, as defined by the ERC20 specification. Failure to include these keywords will not include the parameter data in the transaction/block's bloom filter. This may cause external tooling searching for these parameters to overlook them, and fail to index logs from this token contract.'''

    WIKI_RECOMMENDATION = 'Add the `indexed` keyword to event parameters which should include it, according to the ERC20 specification.'

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
        for event in contract.events:

            # Only handle events which are declared in this contract.
            if event.contract != contract:
                continue

            # If this is transfer/approval events, expect the first two parameters to be indexed.
            if event.full_name in ["Transfer(address,address,uint256)",
                                   "Approval(address,address,uint256)"]:
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
                    info = "ERC20 event {}.{} ({}) does not index parameter '{}'\n".format(c.name, event.name, event.source_mapping_str, parameter.name)

                    # Add the events to the JSON (note: we do not add the params/vars as they have no source mapping).
                    json = self.generate_json_result(info)
                    self.add_event_to_json(event, json, {
                        "parameter_name": parameter.name
                    })
                    results.append(json)

        return results
