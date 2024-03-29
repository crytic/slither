// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {IERC20} from "./IERC20.sol";
import "./Ownable.sol";


interface ILpIncentive {
    function distributeAirdrop(address user) external;
}

contract RLLpIncentive is ILpIncentive, Ownable {

    struct AirdropInfo {
        uint256 lastUpdateTimestamp;
        uint256 index;
    }

    uint constant internal LP_MINT_TOTAL = 8e6 * 1e18;
    //for mainnet
    uint constant internal SECOND_PER_DAY = 24 * 60 * 60;
    uint constant internal LP_MINT_PER_DAY = 5000 * 1e18;

    //for test TODO
    //    uint constant internal LP_MINT_PER_DAY = 1 * 1e18;
    //    uint constant internal SECOND_PER_DAY = 10 * 60; // half hour

    uint constant internal PRECISION = 1e18;

    IERC20 public lpToken;
    IERC20 public rewardToken;
    uint256 public initEmissionsPerSecond;
    uint256 public hasDistributed;
    uint256 public airdropStartTime;
    AirdropInfo public globalAirdropInfo;
    mapping(address => uint256) public usersIndex;
    mapping(address => uint256) public userUnclaimedRewards;

    constructor(IERC20 _lpToken, IERC20 _rewardToken) {
        lpToken = _lpToken;
        rewardToken = _rewardToken;
        initEmissionsPerSecond = LP_MINT_PER_DAY / SECOND_PER_DAY;
    }

    function setAirdropStartTime(uint256 _airdropStartTime) public onlyOwner {
        airdropStartTime = _airdropStartTime;
    }

    function distributeAirdrop(address user) public override {
        if (block.timestamp < airdropStartTime) {
            return;
        }
        updateIndex();
        uint256 rewards = getUserUnclaimedRewards(user);
        usersIndex[user] = globalAirdropInfo.index;
        if (rewards > 0) {
            uint256 bal = rewardToken.balanceOf(address(this));
            if (bal >= rewards) {
                rewardToken.transfer(user, rewards);
                userUnclaimedRewards[user] = 0;
            }
        }
    }

    function getUserUnclaimedRewards(address user) public view returns (uint256) {
        if (block.timestamp < airdropStartTime) {
            return 0;
        }
        (uint256 newIndex,) = getNewIndex();
        uint256 userIndex = usersIndex[user];
        if (userIndex >= newIndex || userIndex == 0) {
            return userUnclaimedRewards[user];
        } else {
            return userUnclaimedRewards[user] + (newIndex - userIndex) * lpToken.balanceOf(user) / PRECISION;
        }
    }

    function updateIndex() public {
        (uint256 newIndex, uint256 emissions) = getNewIndex();
        globalAirdropInfo.index = newIndex;
        globalAirdropInfo.lastUpdateTimestamp = block.timestamp;
        hasDistributed += emissions;
    }

    function getNewIndex() public view returns (uint256, uint256) {
        uint totalSupply = lpToken.totalSupply();
        if (globalAirdropInfo.lastUpdateTimestamp >= block.timestamp ||
        hasDistributed >= LP_MINT_TOTAL || totalSupply == 0 || globalAirdropInfo.lastUpdateTimestamp == 0) {
            if (globalAirdropInfo.index == 0) {
                return (PRECISION, 0);
            } else {
                return (globalAirdropInfo.index, 0);
            }
        }
        uint256 emissions = initEmissionsPerSecond * uint256(block.timestamp - globalAirdropInfo.lastUpdateTimestamp);
        return (globalAirdropInfo.index + emissions * PRECISION / totalSupply, emissions);
    }
}