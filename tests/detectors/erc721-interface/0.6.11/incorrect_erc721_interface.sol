// pragma solidity ^0.4.24;

interface IERC165 {
    function supportsInterface(bytes4 interfaceID) external;
}
abstract contract Token is IERC165{
    function balanceOf(address _owner) external virtual;
    function ownerOf(uint256 _tokenId) external virtual;
    function safeTransferFrom(address _from, address _to, uint256 _tokenId, bytes calldata data) external virtual returns (bool);
    function safeTransferFrom(address _from, address _to, uint256 _tokenId) external virtual returns (bool);
    function transferFrom(address _from, address _to, uint256 _tokenId) external virtual returns (bool);
    function approve(address _approved, uint256 _tokenId) external virtual returns (bool);
    function setApprovalForAll(address _operator, bool _approved) external virtual returns (bool);
    function getApproved(uint256 _tokenId) external virtual;
    function isApprovedForAll(address _owner, address _operator) external virtual;
}
