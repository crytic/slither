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
    WIKI_DESCRIPTION = 'Lack of return value for the ERC20 `approve`/`transfer`/`transferFrom` functions. A contract compiled with solidity > 0.4.22 interacting with these functions will fail to execute them, as the return value is missing.'
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract Token{
    function transfer(address to, uint value) external;
    //...
}
```
`Token.transfer` does not return a boolean. Bob deploys the token. Alice creates a contract that interacts with it but assumes a correct ERC20 interface implementation. Alice's contract is unable to interact with Bob's contract.'''

    WIKI_RECOMMENDATION = 'Return a boolean for the `approve`/`transfer`/`transferFrom` functions.'

    @staticmethod
    def incorrect_erc20_interface(signature):
        (name, parameters, returnVars) = signature

        if name == 'transfer' and parameters == ['address', 'uint256'] and returnVars != ['bool']:
            return True

        if name == 'transferFrom' and parameters == ['address', 'address', 'uint256'] and returnVars != ['bool']:
            return True

        if name == 'approve' and parameters == ['address', 'uint256'] and returnVars != ['bool']:
            return True

        return False

    @staticmethod
    def detect_incorrect_erc20_interface(contract):
        """ Detect incorrect ERC20 interface

        Returns:
            list(str) : list of incorrect function signatures
        """
        functions = [f for f in contract.functions if f.original_contract == contract and \
                     IncorrectERC20InterfaceDetection.incorrect_erc20_interface(f.signature)]
        return functions

    def _detect(self):
        """ Detect incorrect erc20 interface

        Returns:
            dict: [contrat name] = set(str)  events
        """
        results = []
        for c in self.contracts:
            functions = IncorrectERC20InterfaceDetection.detect_incorrect_erc20_interface(c)
            if functions:
                info = "{} ({}) has incorrect ERC20 function interface(s):\n"
                info = info.format(c.name,
                                   c.source_mapping_str)
                for function in functions:
                    info += "\t-{} ({})\n".format(function.name, function.source_mapping_str)
                json = self.generate_json_result(info)
                self.add_functions_to_json(functions, json)
                results.append(json)

        return results
