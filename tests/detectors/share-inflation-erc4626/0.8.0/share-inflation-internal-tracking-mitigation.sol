pragma solidity 0.8.0;
// This test verifies that the detector does not trigger in cases where totalAssets() is tracked using an
// internal variable, and thus the vault's profit calculations cannot be tampered with using an external donation.

interface IERC20 {
    function transferFrom(address, address, uint256) external returns(bool);
    function balanceOf(address) external returns (uint256);
}

contract VaultImpl {
    address public asset;
    uint256 public totalSupply;
    uint256 public totalAssets;

    constructor(IERC20 _asset) {
        asset = address(_asset);
    }

    function deposit(uint256 amount, address receiver) public returns (uint256 sharesToMint) {
        if(totalSupply == 0 && totalAssets == 0){
            sharesToMint = amount;
            // [...]
        } else {
            sharesToMint = amount * totalSupply / totalAssets;
        }
        totalAssets += amount;
    }

    function mint(uint256 shares, address receiver) public returns (uint256 tokensDeposited) {
        if(totalSupply == 0 && totalAssets == 0){
            tokensDeposited = shares;
            // [...]
        } else {
            tokensDeposited = shares * totalAssets / totalSupply;
        }
        totalAssets += tokensDeposited;
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
