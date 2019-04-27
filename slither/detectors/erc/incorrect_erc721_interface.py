"""
Detect incorrect erc721 interface.
"""
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.detectors.erc.incorrect_erc20_interface import is_possible_erc20


def is_possible_erc721(contract):
    """
    Checks if the provided contract could be attempting to implement ERC721 standards.
    :param contract: The contract to check for token compatibility.
    :return: Returns a boolean indicating if the provided contract met the token standard.
    """
    full_names = set([f.full_name for f in contract.functions])
    return is_possible_erc20(contract) and \
        ('ownerOf(uint256)' in full_names or
            'safeTransferFrom(address,address,uint256,bytes)' in full_names or
            'safeTransferFrom(address,address,uint256)' in full_names or
            'setApprovalForAll(address,bool)' in full_names or
            'getApproved(uint256)' in full_names or
            'isApprovedForAll(address,address)' in full_names)


class IncorrectERC721InterfaceDetection(AbstractDetector):
    """
    Incorrect ERC721 Interface
    """

    ARGUMENT = 'erc721-interface'
    HELP = 'Incorrect ERC721 interfaces'
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-erc721-interface'

    WIKI_TITLE = 'Incorrect erc721 interface'
    WIKI_DESCRIPTION = 'Incorrect return values for ERC721 functions. A contract compiled with solidity > 0.4.22 interacting with these functions will fail to execute them, as the return value is missing.'
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract Token{
    function ownerOf(uint256 _tokenId) external view returns (bool);
    //...
}
```
`Token.ownerOf` does not return an address as ERC721 expects. Bob deploys the token. Alice creates a contract that interacts with it but assumes a correct ERC721 interface implementation. Alice's contract is unable to interact with Bob's contract.'''

    WIKI_RECOMMENDATION = 'Set the appropriate return values and value-types for the defined ERC721 functions.'

    @staticmethod
    def incorrect_erc721_interface(signature):
        (name, parameters, returnVars) = signature

        # ERC721
        if name == 'balanceOf' and parameters == ['address'] and returnVars != ['uint256']:
            return True
        if name == 'ownerOf' and parameters == ['uint256'] and returnVars != ['address']:
            return True
        if name == 'safeTransferFrom' and parameters == ['address', 'address', 'uint256', 'bytes'] and returnVars != []:
            return True
        if name == 'safeTransferFrom' and parameters == ['address', 'address', 'uint256'] and returnVars != []:
            return True
        if name == 'transferFrom' and parameters == ['address', 'address', 'uint256'] and returnVars != []:
            return True
        if name == 'approve' and parameters == ['address', 'uint256'] and returnVars != []:
            return True
        if name == 'setApprovalForAll' and parameters == ['address', 'bool'] and returnVars != []:
            return True
        if name == 'getApproved' and parameters == ['uint256'] and returnVars != ['address']:
            return True
        if name == 'isApprovedForAll' and parameters == ['address', 'address'] and returnVars != ['bool']:
            return True

        # ERC165 (dependency)
        if name == 'supportsInterface' and parameters == ['bytes4'] and returnVars != ['bool']:
            return True

        return False

    @staticmethod
    def detect_incorrect_erc721_interface(contract):
        """ Detect incorrect ERC721 interface

        Returns:
            list(str) : list of incorrect function signatures
        """

        # Verify this is an ERC721 contract.
        if not is_possible_erc721(contract) or not is_possible_erc20(contract):
            return []

        functions = [f for f in contract.functions if IncorrectERC721InterfaceDetection.incorrect_erc721_interface(f.signature)]
        return functions

    def _detect(self):
        """ Detect incorrect erc721 interface

        Returns:
            dict: [contract name] = set(str)  events
        """
        results = []
        for c in self.contracts:
            functions = IncorrectERC721InterfaceDetection.detect_incorrect_erc721_interface(c)
            if functions:
                info = "{} ({}) has incorrect ERC721 function interface(s):\n"
                info = info.format(c.name,
                                   c.source_mapping_str)
                for function in functions:
                    info += "\t-{} ({})\n".format(function.name, function.source_mapping_str)
                json = self.generate_json_result(info)
                self.add_functions_to_json(functions, json)
                results.append(json)

        return results
