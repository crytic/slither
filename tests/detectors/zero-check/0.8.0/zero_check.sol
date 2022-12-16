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