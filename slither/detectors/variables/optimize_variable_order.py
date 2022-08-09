from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class OtimizeVariableOrder(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = "optimize-var-order"
    HELP = "Find space optimizations from reordering variables"
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/trailofbits/slither/wiki/Optimizing-variable-order-detector"

    WIKI_TITLE = "Optimal Variable Order Detector"
    WIKI_DESCRIPTION = (
        "Detect optimizations in the variable order of structs to decrease the number of slots used"
    )
    WIKI_EXPLOIT_SCENARIO = """
```solidity
    struct original {
        uint128 a
        uint256 b
        uint128 c
    }
```
A struct is declared with an unoptimized variable order. The `original` struct will take 3 stroage slots because each variable will have its own slot."""
    WIKI_RECOMMENDATION = """
```solidity
    struct optimized {
        uint128 a
        uint128 c
        uint256 b
    }
```
The struct's variables are reordered to take advantage of Solidity's variable packing. The struct's variables `a` and `b` will both be packed into the same slot, resulting in the `optimized` struct only taking 2 storage slots."""
    
    BITS_PER_SLOT = 256

    def _detect(self):

        for contract in self.compilation_unit.contracts_derived:
            pass
            
        info = ["This is an example"]
        res = self.generate_result(info)

        return [res]
