pragma solidity ^0.8.24;

contract TSURUWrapper{
    bool private _opened = false;
    address public immutable erc721Contract;
    uint256 public constant _maxTotalSupply = 431_386_000 * 1e18;
    uint256 private constant ERC721_RATIO = 400 * 1e18;
    mapping(address owner => uint256) private _balancesOfOwner;
    uint256 private _holders;
    uint256 private _totalSupply;
    function totalSupply() public view virtual returns (uint256) {
        return _totalSupply;
    }
    function onERC721Received(
        address,
        address from,
        uint256,
        bytes calldata
    ) external returns (bytes4) {
        require(_opened, "Already yet open.");
        require(msg.sender == address(erc721Contract), "Unauthorized token");
        _safeMint(from, ERC721_RATIO); // Adjust minting based on the ERC721_RATIO
        return this.onERC721Received.selector;
    }

    function _safeMint(address account, uint256 value) internal {
        require(_maxTotalSupply > totalSupply() + value, "Max supply exceeded.");

        // _mint(account, value);
        
        if (_balancesOfOwner[account] == 0) {
            ++_holders;
        }
        _balancesOfOwner[account] = _balancesOfOwner[account] + value;
    }
}