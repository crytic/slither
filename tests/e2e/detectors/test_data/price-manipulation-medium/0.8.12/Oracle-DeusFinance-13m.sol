// SPDX-License-Identifier: MIT

pragma solidity 0.8.12;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);

    function totalSupply() external view returns (uint256);
}

contract Oracle {
    IERC20 public dei;
    IERC20 public usdc;
    IERC20 public pair;

    constructor(
        IERC20 dei_,
        IERC20 usdc_,
        IERC20 pair_
    ) {
        dei = dei_;
        usdc = usdc_;
        pair = pair_;
    }

    function getPrice() external view returns (uint256) {
        return
            ((dei.balanceOf(address(pair)) + (usdc.balanceOf(address(pair)) * 1e12)) *
                1e18) / pair.totalSupply();
    }
}