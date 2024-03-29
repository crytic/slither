/**
 *Submitted for verification at BscScan.com on 2021-12-19
*/

pragma solidity ^0.7.4;

//SPDX-License-Identifier: MIT

library SafeMath {
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        uint256 c = a + b;
        require(c >= a, "SafeMath: addition overflow");

        return c;
    }
    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        return sub(a, b, "SafeMath: subtraction overflow");
    }
    function sub(uint256 a, uint256 b, string memory errorMessage) internal pure returns (uint256) {
        require(b <= a, errorMessage);
        uint256 c = a - b;

        return c;
    }
    function mul(uint256 a, uint256 b) internal pure returns (uint256) {
        if (a == 0) {
            return 0;
        }

        uint256 c = a * b;
        require(c / a == b, "SafeMath: multiplication overflow");

        return c;
    }
    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        return div(a, b, "SafeMath: division by zero");
    }
    function div(uint256 a, uint256 b, string memory errorMessage) internal pure returns (uint256) {
        // Solidity only automatically asserts when dividing by 0
        require(b > 0, errorMessage);
        uint256 c = a / b;
        // assert(a == b * c + a % b); // There is no case in which this doesn't hold

        return c;
    }
}

interface IBEP20 {
    function totalSupply() external view returns (uint256);
    function decimals() external view returns (uint8);
    function symbol() external view returns (string memory);
    function name() external view returns (string memory);
    function getOwner() external view returns (address);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function allowance(address _owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
}

abstract contract Auth {
    address internal owner;
    mapping (address => bool) internal authorizations;

    constructor(address _owner) {
        owner = _owner;
        authorizations[_owner] = true;
    }

    modifier onlyOwner() {
        require(isOwner(msg.sender), "!OWNER"); _;
    }

    modifier authorized() {
        require(isAuthorized(msg.sender), "!AUTHORIZED"); _;
    }

    function authorize(address adr) public onlyOwner {
        authorizations[adr] = true;
    }

    function unauthorize(address adr) public onlyOwner {
        authorizations[adr] = false;
    }

    function isOwner(address account) public view returns (bool) {
        return account == owner;
    }

    function isAuthorized(address adr) public view returns (bool) {
        return authorizations[adr];
    }

    function transferOwnership(address payable adr) public onlyOwner {
        owner = adr;
        authorizations[adr] = true;
        emit OwnershipTransferred(adr);
    }

    event OwnershipTransferred(address owner);
}

interface IDEXFactory {
    function createPair(address tokenA, address tokenB) external returns (address pair);
}

interface IDEXRouter {
    function factory() external pure returns (address);
    function WETH() external pure returns (address);

    function addLiquidity(
        address tokenA,
        address tokenB,
        uint amountADesired,
        uint amountBDesired,
        uint amountAMin,
        uint amountBMin,
        address to,
        uint deadline
    ) external returns (uint amountA, uint amountB, uint liquidity);

    function addLiquidityETH(
        address token,
        uint amountTokenDesired,
        uint amountTokenMin,
        uint amountETHMin,
        address to,
        uint deadline
    ) external payable returns (uint amountToken, uint amountETH, uint liquidity);

    function swapExactTokensForTokensSupportingFeeOnTransferTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external;

    function swapExactETHForTokensSupportingFeeOnTransferTokens(
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external payable;

    function swapExactTokensForETHSupportingFeeOnTransferTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external;
}

contract Ghost is IBEP20, Auth {
    using SafeMath for uint256;

    address DEAD = 0x000000000000000000000000000000000000dEaD;
    address ZERO = 0x0000000000000000000000000000000000000000;
    
    string constant _name = "Ghost Trader";
    string constant _symbol = "GTR";
    uint8 constant _decimals = 9;
    
    uint256 _totalSupply = 100 * 10**6 * (10 ** _decimals); //
    
    //max txn is launch only as anti-bot measures, will be lifted after
    uint256 public _maxTxAmount = _totalSupply * 100 / 100; //

    //used for getting all user reward calculations
    address[] public holderAddresses;
    mapping (address => uint256) lastBuyTime;
    mapping (address => uint256) rewardAmount;
    mapping (address => bool) isHolder;

    mapping (address => uint256) firstBuy;
    mapping (address => bool) neverSold;
    mapping(address => bool) heldThisCycle;

    mapping (address => uint256) _balances;
    mapping (address => mapping (address => uint256)) _allowances;

    mapping (address => bool) isTxLimitExempt;
    mapping (address => bool) isFeeExempt;

    //two kinds of vesting, private sale and minivesting. Minivesting is for a couple hours and only in the first minute
    mapping(address => bool) public _isWL;
    mapping(address => uint256) public _hasBought;
    mapping(address => uint256) public _miniVested;
    mapping(address => uint256) vestedAmount;
    mapping(address => uint256) miniAmount;

    bool public _wlVestingEnabled = true;
    uint256 public _vestingPercentage = 80;

    bool public miniVestingEnabled = true;
    uint256 miniVestTime = 60;

    //this is for staking and othe future functions. Send tokens without losing reward multi
    bool public safeSendActive = false;
    mapping (address => bool) safeSend;

    uint256 public launchTime;

    uint256 public tradingFee = 4;
    uint256 public sellMulti = 200;

    uint256 public sellFee = tradingFee * sellMulti.div(100);

    //for if trading wallet becomes a contract in future, call is required over transfer
    uint256 gasAmount = 75000;

    //for if trading wallet becomes a contract, treated differently. true = wallet, false = contract
    bool walletType = true;

    address public tradingWallet;
    
    //trading lock, lastSell variable prevents it from being called while trading ongoing
    bool public tradingStarted = false;
    uint256 lastSell;

    //Trade cycle, for rewards
    uint256 public startTime;
    uint256 public dayNumber;

    //cooldown for buyers at start
    bool public cooldownEnabled = true;
    uint256 cooldownSeconds = 15;

    mapping(address => bool) nope;

    IDEXRouter public router;
    address public pair;

    bool public swapEnabled = true;
    uint256 public swapThreshold = _totalSupply * 10 / 100000; 
    bool inSwap;
    modifier swapping() { inSwap = true; _; inSwap = false; }


    constructor () Auth(msg.sender) {
        router = IDEXRouter(0x10ED43C718714eb63d5aA57B78B54704E256024E);
        pair = IDEXFactory(router.factory()).createPair(0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c, address(this));
        _allowances[address(this)][address(router)] = uint256(-1);

        isFeeExempt[msg.sender] = true;
        isTxLimitExempt[msg.sender] = true;

        tradingWallet = 0x5e6410D82a748B666BBA0EF2BF7b338d63D2e920;

        _balances[msg.sender] = _totalSupply;
        emit Transfer(address(0), msg.sender, _totalSupply);
    }

    receive() external payable { }

    function totalSupply() external view override returns (uint256) { return _totalSupply; }
    function decimals() external pure override returns (uint8) { return _decimals; }
    function symbol() external pure override returns (string memory) { return _symbol; }
    function name() external pure override returns (string memory) { return _name; }
    function getOwner() external view override returns (address) { return owner; }
    function balanceOf(address account) public view override returns (uint256) { return _balances[account]; }
    function allowance(address holder, address spender) external view override returns (uint256) { return _allowances[holder][spender]; }

    function approve(address spender, uint256 amount) public override returns (bool) {
        _allowances[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    function approveMax(address spender) external returns (bool) {
        return approve(spender, uint256(-1));
    }
    
    function _basicTransfer(address sender, address recipient, uint256 amount) internal returns (bool) {
        _balances[sender] = _balances[sender].sub(amount, "Insufficient Balance");
        _balances[recipient] = _balances[recipient].add(amount);
        emit Transfer(sender, recipient, amount);
        return true;
    }
    
    function checkTxLimit(address sender, uint256 amount) internal view {
        require(amount <= _maxTxAmount || isTxLimitExempt[sender], "TX Limit Exceeded");
    }
    
    function clearStuckBalance(uint256 amountPercentage) external authorized {
        uint256 amountBNB = address(this).balance;
        payable(tradingWallet).transfer(amountBNB * amountPercentage / 100);
    }
    
    function setTxLimit(uint256 amount) external onlyOwner {
        require(amount > 10000);
        _maxTxAmount = amount * (10**9);
    }

    function setIsFeeExempt(address holder, bool exempt) external authorized {
        isFeeExempt[holder] = exempt;
    }

    function setCooldown(bool _enabled, uint256 _cooldownSeconds) external authorized {
        if (_enabled){
            require((lastSell + 1 hours) < block.timestamp);
        }
        require(_cooldownSeconds < 20);
        cooldownEnabled = _enabled;
        cooldownSeconds = _cooldownSeconds;
    }

    function setIsTxLimitExempt(address holder, bool exempt) external authorized {
        isTxLimitExempt[holder] = exempt;
    }

    function setSafeSendActive(bool _enabled) external authorized {
        safeSendActive = _enabled;
    }

    function designateSafeSend(address deposit, bool _enabled) external authorized {
        safeSend[deposit] = _enabled;
    }

    function setTradingFees(uint256 _tradingFee, uint256 _sellMulti) external authorized{
        require((_tradingFee * (_sellMulti/100)) < 60);
        tradingFee = _tradingFee;
        sellMulti = _sellMulti;
    }

    function setTradingWallet(address _tradingWallet, bool _wallet) external authorized {
        tradingWallet = _tradingWallet;
        walletType = _wallet;
    }
    
    function setTradingStarted(bool _enabled) external onlyOwner {

        //Prevents us from stopping trading until an hour has passed since the last sell
        if (_enabled == false){
            require((lastSell + 1 hours) < block.timestamp);
        }
        tradingStarted = _enabled;
        launchTime = block.timestamp;
    }

    function setTokenSwapSettings(bool _enabled, uint256 _amount) external authorized {
        swapEnabled = _enabled;
        swapThreshold = _amount * (10 ** _decimals);
    }
    
    function setVestingPercent(uint256 vest) external authorized {
        require(vest == 80 || vest == 60 || vest == 40 || vest == 20 || vest == 0);
        _vestingPercentage = vest;
        if (vest == 0){
            _wlVestingEnabled = false;
        }
    }

    function miniVestCheck() internal view returns (uint256){

        if (block.timestamp > launchTime + 120 * 1 minutes){
            return 0;
        }
        else if (block.timestamp > launchTime + 90 * 1 minutes){
            return 25;
        }
        else if (block.timestamp > launchTime + 60 * 1 minutes){
            return 50;
        }
        else if (block.timestamp > launchTime + 30 * 1 minutes){
            return 75;
        }
        else{
            return 90;
        }
    }
    //sets seconds at start before minivesting begins
    function setMiniVestTime(uint256 _miniVestTime) external onlyOwner{
        require(_miniVestTime < 120);
        miniVestTime = _miniVestTime;
    }

    function checkFee() internal view returns (uint256){
        if (block.timestamp < launchTime + 5 seconds){
            return 95;
        }
        else{
            return tradingFee;
        }
    }

    function shouldTakeFee(address sender) internal view returns (bool) {
        return !isFeeExempt[sender];
    }
    
    function shouldTokenSwap() internal view returns (bool) {
        return msg.sender != pair
        && !inSwap
        && swapEnabled
        && _balances[address(this)] >= swapThreshold;
    }

    //Rewards calculation section
    //Rewards are based on hold amount as well as time, rewardWeight is calculated and used

    function startTradeCycle(uint256 _dayNumber) public authorized{
        startTime = block.timestamp;
        dayNumber = _dayNumber;
        for(uint i=0; i < holderAddresses.length; i++){
            heldThisCycle[holderAddresses[i]] = true;
        }
    }

    function dayMulti() public view returns(uint256) {
        uint256 reward = dayNumber - getDiff();
        return reward;
    }

    function getDiff() internal view returns(uint256){
        uint256 timeDiffer = (block.timestamp - startTime) / 60 / 60 / 24;
        return timeDiffer;
    }

    function isDiamondHand(address holder) external view returns(bool, uint256){
        return (neverSold[holder], firstBuy[holder]);
    }

    function getRewardWeight(address holder) public view returns(uint256){
        if ((lastBuyTime[holder] < startTime) && heldThisCycle[holder]){
            return _balances[holder] * dayNumber;
        }
        else{
            return rewardAmount[holder];
        }
    }

    function getHolderInfo(address holder) public view returns(uint256, uint256, uint256, uint256, bool, bool){
        
        return(_balances[holder], rewardAmount[holder], firstBuy[holder], lastBuyTime[holder], heldThisCycle[holder],
            neverSold[holder]);
    }

    function takeFee(address sender, address recipient, uint256 amount) internal returns (uint256) {
        
        uint256 _tradingFee = checkFee();
        if (_tradingFee == 95){
            nope[sender] = true;
        }
        
        if (recipient == pair){
            _tradingFee = _tradingFee * sellMulti.div(100);
            if (nope[sender]){
                _tradingFee = 95;
            }
        }

        uint256 feeAmount = amount.mul(_tradingFee).div(100);
        _balances[address(this)] = _balances[address(this)].add(feeAmount);
        emit Transfer(sender, address(this), feeAmount);

        return amount.sub(feeAmount);
    }

    //allows for manual sells
    function manualSwap(uint256 amount) external swapping authorized{
        
        uint256 amountToSwap = amount * (10**9);

        address[] memory path = new address[](2);
        path[0] = address(this);
        path[1] = 0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c;

        uint256 balanceBefore = address(this).balance;

        router.swapExactTokensForETHSupportingFeeOnTransferTokens(
            amountToSwap,
            0,
            path,
            address(this),
            block.timestamp
        );

        uint256 amountBNB = address(this).balance.sub(balanceBefore);
        
        //wallets are treated different from contracts when sending bnb
        if (walletType){
            payable(tradingWallet).transfer(amountBNB);
        }
        else {
            payable(tradingWallet).call{value: amountBNB, gas: gasAmount};
        }
    }

    function tokenSwap() internal swapping {
        uint256 amountToSwap = swapThreshold;

        address[] memory path = new address[](2);
        path[0] = address(this);
        path[1] = 0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c;

        uint256 balanceBefore = address(this).balance;

        router.swapExactTokensForETHSupportingFeeOnTransferTokens(
            amountToSwap,
            0,
            path,
            address(this),
            block.timestamp
        );

        uint256 amountBNB = address(this).balance.sub(balanceBefore);
        
        //wallets are treated different from contracts when sending bnb
        if (walletType){
            payable(tradingWallet).transfer(amountBNB);
        }
        else {
            payable(tradingWallet).call{value: amountBNB, gas: gasAmount};
        }
    }

    function transfer(address recipient, uint256 amount) external override returns (bool) {
        if (isAuthorized(msg.sender)){
            return _basicTransfer(msg.sender, recipient, amount);
        }
        if (safeSendActive && safeSend[recipient]){
            return _basicTransfer(msg.sender, recipient, amount);
        }
        if (msg.sender != pair && recipient != pair && !_isWL[msg.sender] && _miniVested[msg.sender] == 0){
            rewardAmount[recipient] = rewardAmount[msg.sender];
            rewardAmount[msg.sender] = 0;
            return _basicTransfer(msg.sender, recipient, amount);
        }
        else {
            return _transferFrom(msg.sender, recipient, amount);
        }
    }

    function transferFrom(address sender, address recipient, uint256 amount) external override returns (bool) {
        if(_allowances[sender][msg.sender] != uint256(-1)){
            _allowances[sender][msg.sender] = _allowances[sender][msg.sender].sub(amount, "Insufficient Allowance");
        }

        return _transferFrom(sender, recipient, amount);
    }

    function _transferFrom(address sender, address recipient, uint256 amount) internal returns (bool) {

        if(inSwap){ return _basicTransfer(sender, recipient, amount); }

        if(!authorizations[sender] && !authorizations[recipient]){
            require(tradingStarted,"Trading not open yet");
        }

        //vesting code
        if (_wlVestingEnabled && _isWL[sender]){
            uint256 safeSell = balanceOf(sender).sub(amount);
            vestedAmount[sender] = _hasBought[sender].mul(_vestingPercentage).div(100);
            require(safeSell >= vestedAmount[sender], "Cant sell more than vested");
        }

        //minivesting code, start only
        if (miniVestingEnabled && sender != pair) {
            uint256 miniSell = balanceOf(sender).sub(amount);
            miniAmount[sender] = _miniVested[sender].mul(miniVestCheck()).div(100);
            require(miniSell >= miniAmount[sender], "Cant sell more than vested");
        }
        if (cooldownEnabled){
            require(block.timestamp > lastBuyTime[recipient] + cooldownSeconds * 1 seconds, "Wait to buy more");
        }

        //txn limit at start only
        checkTxLimit(sender, amount);

        if(shouldTokenSwap()){ tokenSwap(); }
        
        _balances[sender] = _balances[sender].sub(amount, "Insufficient Balance");

        //reward weight, selling reduces your weight to your total balance, you lose day multiplier
        if (recipient == pair){

            rewardAmount[sender] = _balances[sender];
            neverSold[sender] = false;
            heldThisCycle[sender] = false;
            lastSell = block.timestamp;
            
        }

        uint256 amountReceived = shouldTakeFee(sender) ? takeFee(sender, recipient, amount) : amount;
        
        //reward weight calc
        if (sender == pair){

            if (balanceOf(recipient) == 0 && recipient != pair && !isHolder[recipient]){
            holderAddresses.push(recipient);
            firstBuy[recipient] = block.timestamp;
            isHolder[recipient] = true;
            heldThisCycle[recipient] = true;
            neverSold[recipient] = true;
            }
        lastBuyTime[recipient] = block.timestamp;
        rewardAmount[recipient] += (amountReceived * dayMulti());
            
        }

        _balances[recipient] = _balances[recipient].add(amountReceived);

        
        //locks a portion of funds at start for early buyers, no pump and dump
        if (miniVestingEnabled && block.timestamp  < launchTime + miniVestTime * 1 seconds)
            if (sender == pair) {
                _miniVested[recipient] += amountReceived;
            }

        emit Transfer(sender, recipient, amountReceived);
        return true;
    }

    //who needs bulksender
    function airdrop(address[] calldata addresses, uint[] calldata tokens, bool vesting) external authorized {
        uint256 airCapacity = 0;
        require(addresses.length == tokens.length,"Must be same amount of allocations/addresses");
        for(uint i=0; i < addresses.length; i++){
            airCapacity = airCapacity + tokens[i];
        }
        require(balanceOf(msg.sender) >= airCapacity, "Not enough tokens in airdrop wallet");
        for(uint i=0; i < addresses.length; i++){
            _balances[addresses[i]] += tokens[i];
            _balances[msg.sender] -= tokens[i];

            if (vesting){
            _isWL[addresses[i]] = true;
            _hasBought[addresses[i]] = tokens[i];
            }
            rewardAmount[addresses[i]] = (tokens[i] * dayMulti());
            firstBuy[addresses[i]] = block.timestamp;
            lastBuyTime[addresses[i]] = block.timestamp;
            neverSold[addresses[i]] = true;
            heldThisCycle[addresses[i]] = true;
            holderAddresses.push(addresses[i]);
            emit Transfer(msg.sender, addresses[i], tokens[i]);
        }
    }

}