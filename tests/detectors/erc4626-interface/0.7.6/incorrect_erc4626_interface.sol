abstract contract ERC20{
    function transfer(address to, uint value) external virtual;
    function approve(address spender, uint value) external virtual;
    function transferFrom(address from, address to, uint value) external virtual;
    function totalSupply() external virtual;
    function balanceOf(address who) external virtual;
    function allowance(address owner, address spender) external virtual;
}

abstract contract Vault is ERC20 {
    function asset() external virtual;
    function totalAssets() external virtual;
    function convertToShares(uint256 assets) external virtual;
    function convertToAssets(uint256 shares) external virtual;
    function maxDeposit(address receiver) external virtual;
    function previewDeposit(uint256 assets) external virtual;
    function deposit(uint256 assets, address receiver) external virtual;
    function maxMint(address receiver) external virtual;
    function previewMint(uint256 shares) external virtual;
    function mint(uint256 shares, address receiver) external virtual;
    function maxWithdraw(address owner) external virtual;
    function previewWithdraw(uint256 assets) external virtual;
    function withdraw(uint256 assets, address receiver, address owner) external virtual;
    function maxRedeem(address owner) external virtual;
    function previewRedeem(uint256 shares) external virtual;
    function redeem(uint256 shares, address receiver, address owner) external virtual;
}