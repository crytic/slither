"""
Gas: Using calldata instead of memory for read-only external function parameters will reduce gas fees as well as contract deployment time cost.

"""


from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Operation
from slither.core.solidity_types import ElementaryType


class GasCalldataParameterCheck(AbstractDetector):
    """
    Gas: Using calldata instead of memory for read-only external function parameters will reduce gas fees as well as contract deployment time cost.
    """

    ARGUMENT = "calldata-check"
    HELP = "You can use calldata as storage location in a function rather than memory, if the function is external and read-only."
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#use-calldata-instead-of-memory-for-function-parameters"
    WIKI_TITLE = "Use calldata Instead of Memory for Function Parameters"
    WIKI_DESCRIPTION = "In some cases, having function arguments in calldata instead of memory is more optimal. When arguments are read-only on external functions, the data location should be calldata." 


    def pre_process(self):
        # keep track of the functions we've already checked
        self.detect = set()

    def _detect(self, function):
        # skip functions we've already checked
        if function in self.detect:
            return

        # skip functions without arguments
        if not function.arguments:
            return

        # skip functions that are not marked as external
        if not any(opcode in [Operation.EXTERNAL_FUNCTION_CALL, Operation.EXTERNAL_FUNCTION_CALL_CREATE] for opcode in function.slither.opcodes):
            return

        # check if all arguments are read-only
        if any(not arg.read_only for arg in function.arguments):
            return

        # check if all arguments are elementary types
        if any(not isinstance(arg.type, ElementaryType) for arg in function.arguments):
            return

        # check if all arguments are using calldata
        if any(arg.storage_location != 'calldata' for arg in function.arguments):
            self._issues.append((
                f"Function '{function.name}' is using memory for read-only external function parameters. "
                f"Consider using calldata instead to reduce gas fees and contract deployment time cost.",
                function.source_mapping,
            ))

        # mark function as checked
        self.detect.add(function)

    def analyze(self):
        # check each contract function
        for contract in self.contracts:
            for function in contract.functions:
                self.check_function(function)

        # check external function calls
        for call in self.slither.slt_runtime.calls:
            if call.type == Operation.EXTERNAL_FUNCTION_CALL:
                self.check_function(call.target_function)
            elif call.type == Operation.EXTERNAL_FUNCTION_CALL_CREATE:
                self.check_function(call.constructor)
