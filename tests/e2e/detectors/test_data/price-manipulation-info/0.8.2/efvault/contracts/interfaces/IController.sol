// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IController {
    function totalAssets() external view returns (uint256);

    function deposit(uint256 _amount) external returns (uint256);

    function withdraw(uint256 _amount, address _receiver) external returns (uint256, uint256);
}
