"""
Module detecting missing zero-check.

"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Binary, BinaryType
from slither.slithir.variables.constant import Constant
from slither.analyses.data_dependency.data_dependency import get_all_dependencies


class ZeroCheck(AbstractDetector):
    """
    Detect missing zero-check
    """

    ARGUMENT = "zero-check"  # slither will launch the detector with slither.py --mydetector
    HELP = "Caution zero boundary"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.LOW

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#zero-check"
    WIKI_TITLE = "ZERO_CHECK"
    WIKI_DESCRIPTION = "ZERO_CHECK"
    WIKI_EXPLOIT_SCENARIO = """
```solidity
interface IERC1155 {
    function safeTransferFrom(address, address, uint256, uint256, bytes calldata) external;
}
interface IERC165 {
    function supportsInterface(bytes4) view external returns (bool);
}
interface IERC721{
    function safeTransferFrom(address, address, uint256) external;
}
contract A {
    //  _nftAddress => _tokenId => _owner
    bytes4 private constant INTERFACE_ID_ERC721 = 0x80ac58cd;
    struct Listing{
        uint _quantity;
    }
    mapping(address => mapping(uint256 => mapping(address => Listing))) public listings;

    function buyItem(
        address _nftAddress,
        uint256 _tokenId,
        address _owner,
        uint256 _quantity
    ) public {
        require(listings[_nftAddress][_tokenId][_owner]._quantity >= _quantity, "");
        if (IERC165(_nftAddress).supportsInterface(INTERFACE_ID_ERC721)) {
            IERC721(_nftAddress).safeTransferFrom(_owner, msg.sender, _tokenId);
        } else {
            IERC1155(_nftAddress).safeTransferFrom(_owner, msg.sender, _tokenId, _quantity, bytes(""));
        }
    }
}
```
In ERC721, to buy one NFT is equal to buy zero NFT because the quantity of NFT of unique ID is only one. 
https://rekt.news/treasure-dao-rekt/
https://arbiscan.io/address/0x812cda2181ed7c45a35a691e0c85e231d218e273#code#F17#L226
"""
    WIKI_RECOMMENDATION = "Check there is no problem when value is zero"

    def detect_important_variables(self, func):
        specific_variable_names = [
            "quantity",
            "amount",
            "value",
        ]  # heuristic key point. you can update.
        important_variables = []
        for variable in func._parameters:
            for specific_name in specific_variable_names:
                if specific_name.lower() in variable.name.lower():
                    important_variables += [variable]
                    break
        return important_variables

    def detect_important_conditions(self, func, contract):

        important_variables = self.detect_important_variables(func)
        is_checked = [False] * len(important_variables)

        tmp = get_all_dependencies(contract)

        for node in func.nodes:
            for ir in node.irs:
                if isinstance(ir, Binary):

                    is_verified = False
                    # variable != 0
                    # 0 != variable
                    # variable > 0 GREATER
                    # 0 < variable LESS

                    operand = None
                    if ir.type is BinaryType.NOT_EQUAL:
                        if isinstance(ir.variable_left, Constant) and ir.variable_left.value == 0:
                            is_verified = True
                            operand = ir.variable_right

                        if isinstance(ir.variable_right, Constant) and ir.variable_right.value == 0:
                            is_verified = True
                            operand = ir.variable_left
                    if ir.type is BinaryType.LESS:
                        if isinstance(ir.variable_left, Constant) and ir.variable_left.value == 0:
                            is_verified = True
                            operand = ir.variable_right
                    if ir.type is BinaryType.GREATER:
                        if isinstance(ir.variable_right, Constant) and ir.variable_right.value == 0:
                            is_verified = True
                            operand = ir.variable_left

                    if is_verified is True:
                        for idx in range(len(important_variables)):
                            if (
                                operand == important_variables[idx]
                                or important_variables[idx] in tmp[operand]
                            ):
                                is_checked[idx] = True

        is_safe = True
        for res in is_checked:
            if res == False:
                is_safe = False
        return is_safe

    def _detect(self):
        results = []
        for contract in self.contracts:
            for func in contract.functions:
                # to decrease false positive
                if func._pure == True or func._view == True:
                    continue

                if self.detect_important_conditions(func, contract) is False:
                    info = [
                        "Missing zero check found in ",
                        func,
                        "\n",
                    ]
                    res = self.generate_result(info)
                    results.append(res)
        return results
