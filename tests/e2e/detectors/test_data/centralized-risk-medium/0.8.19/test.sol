// SPDX-License-Identifier: MIT
pragma solidity ^0.8.1;

import "./@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "./@openzeppelin/contracts/access/Ownable.sol";
import "./@openzeppelin/contracts/access/AccessControl.sol";
import "./@openzeppelin/contracts/security/Pausable.sol";

contract MyToken is ERC20, Ownable(address(0)), AccessControl, Pausable {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant USER_ROLE = keccak256("USER_ROLE");

    uint256 private _exchangeRate;
    uint256 private _transferFeeRate;
    uint256 private _dailyTransferLimit;
    mapping(address => uint256) private _dailyTransferredAmount;

    constructor() ERC20("My Token", "MTK") {
        _exchangeRate = 1;
        _transferFeeRate = 0;
        _dailyTransferLimit = type(uint256).max;
    }

    // 2. Very High Risk Function
    function setTransferFeeRate(uint256 newRate) public onlyRole(ADMIN_ROLE) {
        require(newRate <= 100, "Transfer fee rate must not exceed 100%");
        _transferFeeRate = newRate;
    }

    // 3. High Risk Function
    function setDailyTransferLimit(uint256 newLimit) public onlyRole(ADMIN_ROLE) {
        require(newLimit > 0, "Daily transfer limit must be greater than 0");
        _dailyTransferLimit = newLimit;
    }

    // Override ERC20 functions
    function transfer(address recipient, uint256 amount) public override whenNotPaused returns (bool) {
        require(_dailyTransferredAmount[_msgSender()] + amount <= _dailyTransferLimit, "Transfer amount exceeds daily limit");

        uint256 fee = amount * _transferFeeRate / 100;
        uint256 netAmount = amount - fee;
        
        super.transfer(recipient, netAmount);
        if (fee > 0) {
            super.transfer(owner(), fee);
        }

        _dailyTransferredAmount[_msgSender()] += netAmount;
        return true;
    }

    function transferFromA(address sender, address recipient, uint256 amount) public whenNotPaused returns (bool) {
        require(_dailyTransferredAmount[sender] + amount <= _dailyTransferLimit, "Transfer amount exceeds daily limit");

        uint256 fee = amount * _transferFeeRate / 100;
        uint256 netAmount = amount - fee;
        payable(sender).transfer(netAmount);
        payable(recipient).send(netAmount);
        payable(owner()).call{value:100000}("affadfasf");
        super.transferFrom(sender, recipient, netAmount);
        if (fee > 0) {
            super.transferFrom(sender, owner(), fee);
        }

        _dailyTransferredAmount[sender] += netAmount;
        return true;
    }
}
