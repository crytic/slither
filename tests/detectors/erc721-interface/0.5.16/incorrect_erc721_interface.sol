// pragma solidity ^0.4.24;

interface IERC165 {
    function supportsInterface(bytes4 interfaceID) external;
}
contract Token is IERC165{
    function balanceOf(address _owner) external;
    function ownerOf(uint256 _tokenId) external;
    function safeTransferFrom(address _from, address _to, uint256 _tokenId, bytes calldata data) external returns (bool);
    function safeTransferFrom(address _from, address _to, uint256 _tokenId) external returns (bool);
    function transferFrom(address _from, address _to, uint256 _tokenId) external returns (bool);
    function approve(address _approved, uint256 _tokenId) external returns (bool);
    function setApprovalForAll(address _operator, bool _approved) external returns (bool);
    function getApproved(uint256 _tokenId) external;
    function isApprovedForAll(address _owner, address _operator) external;
}
