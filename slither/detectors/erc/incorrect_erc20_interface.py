"""
Detect incorrect erc20 interface.
Some contracts do not return a bool on transfer/transferFrom/approve, which may lead to preventing the contract to be used with contracts compiled with recent solc (>0.4.22)
"""
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class IncorrectERC20InterfaceDetection(AbstractDetector):
    """
    Incorrect ERC20 Interface
    """

    ARGUMENT = 'erc20-interface'
    HELP = 'Incorrect ERC20 interfaces'
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-erc20-interface'

    WIKI_TITLE = 'Incorrect erc20 interface'
    WIKI_DESCRIPTION = 'Incorrect return values for ERC20 functions. A contract compiled with solidity > 0.4.22 interacting with these functions will fail to execute them, as the return value is missing.'
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract Token{
    function transfer(address to, uint value) external;
    //...
}
```
`Token.transfer` does not return a boolean. Bob deploys the token. Alice creates a contract that interacts with it but assumes a correct ERC20 interface implementation. Alice's contract is unable to interact with Bob's contract.'''

    WIKI_RECOMMENDATION = 'Set the appropriate return values and value-types for the defined ERC20 functions.'

    @staticmethod
    def incorrect_erc20_interface(signature):
        (name, parameters, returnVars) = signature

        if name == 'transfer' and parameters == ['address', 'uint256'] and returnVars != ['bool']:
            return True

        if name == 'transferFrom' and parameters == ['address', 'address', 'uint256'] and returnVars != ['bool']:
            return True

        if name == 'approve' and parameters == ['address', 'uint256'] and returnVars != ['bool']:
            return True

        if name == 'allowance' and parameters == ['address', 'address'] and returnVars != ['uint256']:
            return True

        if name == 'balanceOf' and parameters == ['address'] and returnVars != ['uint256']:
            return True

        if name == 'totalSupply' and parameters == [] and returnVars != ['uint256']:
            return True

        return False

    @staticmethod
    def detect_incorrect_erc20_interface(contract):
        """ Detect incorrect ERC20 interface

        Returns:
            list(str) : list of incorrect function signatures
        """

        # Verify this is an ERC20 contract.
        if not contract.is_possible_erc20():
            return []

        # If this contract implements a function from ERC721, we can assume it is an ERC721 token. These tokens
        # offer functions which are similar to ERC20, but are not compatible.
        if contract.is_possible_erc721():
            return []

        funcs = contract.functions
        functions = [f for f in funcs if IncorrectERC20InterfaceDetection.incorrect_erc20_interface(f.signature)]

        return functions

    def _detect(self):
        """ Detect incorrect erc20 interface

        Returns:
            dict: [contract name] = set(str)  events
        """
        results = []
        for c in self.slither.contracts_derived:
            functions = IncorrectERC20InterfaceDetection.detect_incorrect_erc20_interface(c)
            if functions:
                for function in functions:
                    info = [c, " has incorrect ERC20 function interface:", function, "\n"]
                    json = self.generate_result(info)

                    results.append(json)

        return results
