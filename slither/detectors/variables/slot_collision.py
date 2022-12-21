"""
Module detecting likelihood of slot collision.

"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class SlotCollision(AbstractDetector):
    """
    Detect likelihood of slot-collision
    """

    ARGUMENT = "slot-collision"  # slither will launch the detector with slither.py --mydetector
    HELP = "Proxy contract take up slot 0"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#slot-collision"
    WIKI_TITLE = "SLOT_COLLISION"
    WIKI_DESCRIPTION = "SLOT_COLLISION"
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Proxy {
    address proxyOwner;
    // ...
}

contract impl {
    bool isInit;
    address owner;
    
    modifier initializer () {
        require(!isInit, "already initialized");
        _;
        isInit = true;
    }
    
    function init(address _owner) initializer public {
        owner = _owner;
    }
}
```
There is a collision between proxyOwner and isInit.   
By chance, isInit always is false.   
So attacker can change owner by calling init().   
"""
    WIKI_RECOMMENDATION = "Check proxy contract storage layout"

    def _detect(self):

        results = []

        for contract in self.compilation_unit.contracts_derived:

            if contract.is_upgradeable_proxy:
                for key, value in self.compilation_unit._storage_layouts[contract.name].items():
                    if value[0] == 0:
                        if len(contract.functions) == 0:
                            continue
                        info = [
                            "Slot collision found in ",
                            contract,
                            "\n",
                        ]
                        res = self.generate_result(info)
                        results.append(res)
        return results
