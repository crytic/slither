"""
Gas: Detecting Revert Strings

"""
from collections import defaultdict

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.solidity_types import String

class RevertStringDetector(AbstractDetector):
    """
    Gas: Detecting Revert Strings
    """

    ARGUMENT = "custom-error-check"
    HELP = "Custom errors allow for a more convenient and gas-efficient way of explaining to users why an operation failed."
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#use-custom-errors-instead-of-revert-strings-to-save-gas"
    WIKI_TITLE = "Use Custom Errors Instead of Revert Strings To Save Gas"
    WIKI_DESCRIPTION = "Custom errors from Solidity 0.8.4 are cheaper than revert strings (cheaper deployment cost and runtime cost when the revert condition is met)."

    def _detect_revert_strings(self, contract):
        """
        Checks if any revert string is being used

        :param contract: Contract to be analyzed
        :return: dictionary containing information about the detected issue
        """

        issues = defaultdict(list)

        # Iterate through each function in the contract
        for function in contract.functions:

            # Check if the function has a string parameter with name "reason"
            for arg in function.arguments:
                if isinstance(arg.type, String) and arg.name == "reason":

                    # Report the issue
                    issues[RevertStringDetector.ARGUMENT].append(
                        f"Function {function.name} is using a revert string in argument {arg.name}")

        return dict(issues)
