"""
Module detecting unimplemented functions
Recursively check the called functions

Collect all the implemented and unimplemented functions of all the contracts
Check for unimplemented functions that are never implemented
Consider public state variables as implemented functions
Do not consider fallback function or constructor
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

# Since 0.5.1, Solidity allows creating state variable matching a function signature.
older_solc_versions = ["0.5.0"] + ["0.4." + str(x) for x in range(0, 27)]


class UnimplementedFunctionDetection(AbstractDetector):
    """
    Unimplemented functions detector
    """

    ARGUMENT = "unimplemented-functions"
    HELP = "Unimplemented functions"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unimplemented-functions"

    WIKI_TITLE = "Unimplemented functions"
    WIKI_DESCRIPTION = "Detect functions that are not implemented on derived-most contracts."
    WIKI_EXPLOIT_SCENARIO = """
```solidity
interface BaseInterface {
    function f1() external returns(uint);
    function f2() external returns(uint);
}

interface BaseInterface2 {
    function f3() external returns(uint);
}

contract DerivedContract is BaseInterface, BaseInterface2 {
    function f1() external returns(uint){
        return 42;
    }
}
```
`DerivedContract` does not implement `BaseInterface.f2` or `BaseInterface2.f3`.
As a result, the contract will not properly compile. 
All unimplemented functions must be implemented on a contract that is meant to be used."""

    WIKI_RECOMMENDATION = "Implement all unimplemented functions in any contract you intend to use directly (not simply inherit from)."

    @staticmethod
    def _match_state_variable(contract, f):
        return any(s.full_name == f.full_name for s in contract.state_variables)

    def _detect_unimplemented_function(self, contract):
        """
        Detects any function definitions which are not implemented in the given contract.
        :param contract: The contract to search unimplemented functions for.
        :return: A list of functions which are not implemented.
        """

        # If it's simply a contract signature, we have no functions.
        if contract.is_signature_only():
            return set()

        # Populate our unimplemented functions set with any functions not implemented in this contract, excluding the
        # fallback function and constructor.
        unimplemented = set()
        for f in contract.all_functions_called:
            if (
                not f.is_implemented
                and not f.is_constructor
                and not f.is_fallback
                and not f.is_constructor_variables
            ):
                if self.slither.solc_version not in older_solc_versions:
                    # Since 0.5.1, Solidity allows creating state variable matching a function signature
                    if not self._match_state_variable(contract, f):
                        unimplemented.add(f)
                else:
                    unimplemented.add(f)
        return unimplemented

    def _detect(self):
        """Detect unimplemented functions

        Recursively visit the calls
        Returns:
            list: {'vuln', 'filename,'contract','func'}
        """
        results = []
        for contract in self.slither.contracts_derived:
            functions = self._detect_unimplemented_function(contract)
            if functions:
                info = [contract, " does not implement functions:\n"]

                for function in sorted(functions, key=lambda x: x.full_name):
                    info += ["\t- ", function, "\n"]

                res = self.generate_result(info)
                results.append(res)
        return results
