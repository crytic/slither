from slither.detectors.abstract_detector import DetectorClassification, AbstractDetector
from slither.slithir.operations import Operation

class StorageCacheDetector(AbstractDetector):
    """
    Gas: Caching storage variables into memory is cheaper than reading it directly from storage every time.
    """

    ARGUMENT = "storage-cache-check"
    HELP = "Consider caching your storage variables into memory rather than in storage. It is much more efficient gas-wise when reading the variable if it is cached in memory."
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#caching-storage-variables-in-memory-to-save-gas"
    WIKI_TITLE = "Caching Storage Variables in Memory To Save Gas"
    WIKI_DESCRIPTION = "Anytime you are reading from storage more than once, it is cheaper in gas cost to cache the variable in memory: a SLOAD cost 100gas, while MLOAD and MSTORE cost 3 gas. Gas savings: at least 97 gas."

    def _detect(self):
        """
        Checks if storage variables are being cached in memory or being read directly from storage.
        """
        cache = {} # To keep track of cached variables
        issues = {} # To store the results
        for function in self.contract.functions:
            # Collect all the operations in the function
            ops = function.slithir.filter(lambda op: isinstance(op, Operation))
            for op in ops:
                # check if the operation is loading a variable from storage
                if op.read_from_storage and not op.write_to_storage:
                    # check if the variable is already cached
                    if op.variable.name in cache:
                        continue
                    else:
                        # cache the variable in memory
                        cache[op.variable.name] = True
                        issues[op.variable.name] = {
                            "description": f"{op.variable.name} is being read directly from storage. Consider caching it in memory to save gas.",
                            "severity": "warning"
                        }
        return issues
