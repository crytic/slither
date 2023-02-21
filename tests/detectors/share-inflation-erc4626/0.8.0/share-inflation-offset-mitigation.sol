pragma solidity 0.8.0;
// This test verifies the detector does not trigger when a vault implements the decimal offset mitigation
// described here: https://ethereum-magicians.org/t/address-eip-4626-inflation-attacks-with-virtual-shares-and-assets/12677
// Note the vault's profit calculation can still be manipulated using external donations.


interface IERC20 {
    function transferFrom(address, address, uint256) external returns(bool);
    function balanceOf(address) external returns (uint256);
}

contract VaultImpl {
    address public asset;
    uint256 public totalSupply;
    uint256 offset = 5;

    constructor(IERC20 _asset) {
        asset = address(_asset);
    }

    function totalAssets() public returns (uint256) {
        return IERC20(asset).balanceOf(address(this));
    }

    function deposit(uint256 amount, address receiver) public returns (uint256 sharesToMint) {
        uint256 supplyOffset = totalSupply + 10**offset;
        sharesToMint = amount * supplyOffset / (totalAssets() + 1);
    }

    function mint(uint256 shares, address receiver) public returns (uint256 tokensDeposited) {
        uint256 supplyOffset = totalSupply + 10**offset;

        tokensDeposited = shares * (totalAssets()+1) / supplyOffset;
        // add a wei to round it up
        tokensDeposited += 1;
    }


    // null ops so the detector identifies this contract as erc4626
    function withdraw(uint256,address,address) public returns (uint256){
        return 0;
    }
    function redeem(uint256,address,address) public returns (uint256){
        return 0;
    }
    function previewMint(uint256) public returns (uint256){
        return 0;
    }
    function previewRedeem(uint256) public returns (uint256){
        return 0;
    }
    function previewDeposit(uint256) public returns (uint256){
        return 0;
    }
    function previewWithdraw(uint256) public returns (uint256){
        return 0;
    }
    function maxRedeem(address) public returns (uint256){
        return 0;
    }
    function maxDeposit(address) public returns (uint256){
        return 0;
    }
    function maxMint(address) public returns (uint256){
        return 0;
    }
    function maxWithdraw(address) public returns (uint256){
        return 0;
    }
    function convertToShares(uint256) public returns (uint256) {
        return 0;
    }
    function convertToAssets(uint256) public returns (uint256) {
        return 0;
    }
    function balanceOf(address) public returns (uint256){
        return 0;
    }
    function transfer(address,uint256) public {

    }
    function transferFrom(address,address,uint256) public {

    }
    function approve(address,uint256) public {

    }
    function allowance(address,address) public returns (uint256) {
        return 0;
    }
}
