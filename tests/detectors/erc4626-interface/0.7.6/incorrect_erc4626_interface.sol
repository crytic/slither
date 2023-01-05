
abstract contract Vault {
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