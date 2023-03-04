"""
Gas: Detecting Constant Keccak Variables

"""
from collections import defaultdict

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.analyses.data_dependency.data_dependency import is_tainted
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations import Call, Keccak

class ConstantKeccakVariableDetector(AbstractDetector):
    """
    Gas: Detecting Constant Keccak Variables
    """

    ARGUMENT = "constant-to-immutable-check"
    HELP = "The keccak variable can be changed to immutable rather than constant."
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#change-constant-to-immutable-for-keccak-variables"
    WIKI_TITLE = "Change Constant to Immutable for keccak Variables"
    WIKI_DESCRIPTION = "Saving keccak variables as constants results in hashing being done whenever the variable is used. Extra hashing means extra gas. Changing these keccak variables from constant to immutable will save gas." 

    def _detect_constant_keccak_variables(self, contract):
        """
        Checks if any keccak variable is declared as constant

        :param contract: Contract to be analyzed
        :return: dictionary containing information about the detected issue
        """

        issues = defaultdict(list)

        # Iterate through each function in the contract
        for function in contract.functions:

            # Iterate through each block in the function
            for block in function.blocks:

                # Iterate through each instruction in the block
                for instruction in block.instructions:

                    # Check if the instruction is a keccak hash operation
                    if isinstance(instruction, Keccak):

                        # Check if the keccak variable is declared as constant
                        for variable in instruction.variables:
                            if variable.is_constant:
                                # Report the issue
                                issues[ConstantKeccakVariableDetector.ARGUMENT].append(
                                    f"Keccak variable {variable.name} is declared as constant at block {block.id}")

        return dict(issues)
