"""
Gas: Consider using a clone when deploying a factory contract.

"""
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.solidity_types import FunctionType
from slither.solc_parsing import SolcParsing
from slither.core.solidity_types import ContractType


class GasCloneApplicabilityCheck(AbstractDetector):
    """
    Gas: Consider using a clone when deploying a factory contract.
    """

    ARGUMENT = "clone-applicability-check"
    HELP = "If this is a factory contract, a clone will save you a lot of gas and provide identical function and utility."
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#use-clones-for-cheap-contract-deployments"
    WIKI_TITLE = "Use Clones for Cheap Contract Deployments"
    WIKI_DESCRIPTION = "Porter Finance deployed using clones and found that it was 10x cheaper gas-wise. It is worth checking the wiki to see how you could make your factory contract a clone."

    def _get_factory_functions(self, contract):
        factory_functions = []
        for function in contract.functions:
            if isinstance(function.type, FunctionType) and function.type.is_public and function.type.name == "create":
                factory_functions.append(function)
        return factory_functions

    def analyze(self):
        # Get all the contracts in the analyzed project
        all_contracts = SolcParsing.get_contracts(self.slither.crytic_project.all_source_codes)

        # Check each contract for factory functions
        for contract in all_contracts:
            if isinstance(contract, ContractType) and self._get_factory_functions(contract):
                self._issues.append({
                    "contract": contract.name,
                    "title": self.WIKI_TITLE,
                    "description": self.WIKI_DESCRIPTION,
                    "type": self.__class__.__name__,
                    "severity": self.IMPACT,
                    "confidence": self.CONFIDENCE,
                    "locations": [{"node": contract.node}]
                })
