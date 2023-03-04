from slither.detectors.abstract_detector import DetectorClassification, AbstractDetector
from slither.slithir.operations import SLoad, SStore, MLoad, MStore
from slither.core import Variable

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

    def _analyze(self):
        """
        Checks if storage variables are being cached in memory or being read directly from storage.
        """
        for variable in self.contract.variables:
            if isinstance(variable.type, (Variable,)):
                continue  # skip structs for now

            # check for SLOAD and SSTORE operations on the variable
            sload_operations = variable.slithir.filter(SLoad, read_from_storage=True)
            sstore_operations = variable.slithir.filter(SStore, write_to_storage=True)

            # check for MLOAD and MSTORE operations on the variable
            mload_operations = variable.slithir.filter(MLoad)
            mstore_operations = variable.slithir.filter(MStore)

            # check if the variable is being cached in memory or being read from storage
            if sload_operations and not (mload_operations or mstore_operations or sstore_operations):
                self.warn(f"{variable.name} is being read directly from storage. Consider caching it in memory to save gas.")
