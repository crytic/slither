// SPDX-License-Identifier: MIT
// OpenZeppelin Contracts (last updated v4.5.0) (token/ERC20/ERC20.sol)
pragma solidity ^0.8.0;

import "./IERC20.sol";
import "./IERC20Metadata.sol";
import "./Ownable.sol";
import "./IUniswapV2Router.sol";
import "./IUniswapV2Factory.sol";
import "./EnumerableSet.sol";

/**
 * @dev Implementation of the {IERC20} interface.
 *
 * This implementation is agnostic to the way tokens are created. This means
 * that a supply mechanism has to be added in a derived contract using {_mint}.
 * For a generic mechanism see {ERC20PresetMinterPauser}.
 *
 * TIP: For a detailed writeup see our guide
 * https://forum.zeppelin.solutions/t/how-to-implement-erc20-supply-mechanisms/226[How
 * to implement supply mechanisms].
 *
 * We have followed general OpenZeppelin Contracts guidelines: functions revert
 * instead returning `false` on failure. This behavior is nonetheless
 * conventional and does not conflict with the expectations of ERC20
 * applications.
 *
 * Additionally, an {Approval} event is emitted on calls to {transferFrom}.
 * This allows applications to reconstruct the allowance for all accounts just
 * by listening to said events. Other implementations of the EIP may not emit
 * these events, as it isn't required by the specification.
 *
 * Finally, the non-standard {decreaseAllowance} and {increaseAllowance}
 * functions have been added to mitigate the well-known issues around setting
 * allowances. See {IERC20-approve}.
 */


contract GDSToken is Ownable, IERC20, IERC20Metadata{
    
    using EnumerableSet for EnumerableSet.AddressSet;

    mapping(address => uint256) private _balances;
    mapping(address => mapping(address => uint256)) private _allowances;

    uint256 private _totalSupply;
	uint8 private constant _decimals = 18;
    string private _name = "GDS";
    string private _symbol = "GDS";
	
	mapping(address => bool) private isExcludedTxFee;
    mapping(address => bool) private isExcludedReward;
    mapping(address => bool) public isActivated;
    mapping(address => uint256) public inviteCount;
    mapping(address => bool) public uniswapV2Pairs;

    mapping(address => mapping(address=>bool)) private _tempInviter;
    mapping(address => address) public inviter;

    mapping(address => EnumerableSet.AddressSet) private children;

    mapping(uint256 => uint256) public everyEpochLpReward; 
    mapping(address => uint256) public destroyMiningAccounts;
    mapping(address => uint256) public lastBlock;
    mapping(address => uint256) public lastEpoch;

    bool public takeFee = true;
    uint256 private constant _denominator = 10000;
    uint256 public invite1Fee = 200;
    uint256 public invite2Fee = 100;
    uint256 public destroyFee = 300;
    uint256 public lpFee = 100;
    uint256 public miningRate = 150;
    uint256 public currentEpoch = 0;
    uint256 public lastEpochBlock = 0;
    uint256 public lastMiningAmount = 0;
    uint256 public lastDecreaseBlock = 0;
    uint256 public theDayBlockCount = 28800;//28800
    uint256 public everyDayLpMiningAmount = 58000 * 10 ** _decimals;
    uint256 public minUsdtAmount = 100 * 10 ** _decimals;//100
    
    IUniswapV2Router02 public immutable uniswapV2Router;
    address public gdsUsdtPair;
    address public gdsBnbPair;
    address public destoryPoolContract;
    address public lpPoolContract;

    bool public isOpenLpMining = false;
    bool public enableActivate = false;
    bool private isStart = false;

    address public dead = 0x000000000000000000000000000000000000dEaD;
    address public usdt = 0x55d398326f99059fF775485246999027B3197955;
    address private otherReward;
    address private _admin;
    

    /**
     * @dev Sets the values for {name} and {symbol}.
     *
     * The default value of {decimals} is 18. To select a different value for
     * {decimals} you should overload it.
     *
     * All two of these values are immutable: they can only be set once during
     * construction.
     */
    constructor() 
    {
        IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(
            0x10ED43C718714eb63d5aA57B78B54704E256024E
        );
        
        gdsUsdtPair = IUniswapV2Factory(_uniswapV2Router.factory())
            .createPair(address(this), usdt);

        uniswapV2Pairs[gdsUsdtPair] = true;
        

        gdsBnbPair = IUniswapV2Factory(_uniswapV2Router.factory())
            .createPair(address(this), _uniswapV2Router.WETH());
        uniswapV2Pairs[gdsBnbPair] = true;
        
        uniswapV2Router = _uniswapV2Router;

        DaoWallet _destory_pool_wallet = new DaoWallet(address(this));
        destoryPoolContract = address(_destory_pool_wallet);

        DaoWallet _lp_pool_wallet = new DaoWallet(address(this));
        lpPoolContract = address(_lp_pool_wallet);

        isExcludedTxFee[msg.sender] = true;
        isExcludedTxFee[address(this)] = true;
        isExcludedTxFee[dead] = true;
        isExcludedTxFee[destoryPoolContract] = true;
        isExcludedTxFee[lpPoolContract] = true;
        isExcludedTxFee[address(_uniswapV2Router)] = true;

        _mint(msg.sender,78000000 * 10 ** _decimals);
        _mint(destoryPoolContract,  480000000 * 10 ** _decimals);
        _mint(lpPoolContract,  42000000 * 10 ** _decimals);

        currentEpoch = 1;
        lastMiningAmount = 480000000 * 10 ** decimals();

        otherReward = msg.sender;
        _admin = msg.sender;
    }

    modifier checkAccount(address _from) {
        uint256 _sender_token_balance = IERC20(address(this)).balanceOf(_from);
        if(!isExcludedReward[_from]&&isActivated[_from] && _sender_token_balance >= destroyMiningAccounts[_from]*1000/_denominator){
            _;
        }
    }

    function getChildren(address _user)public view returns(address[] memory) {
        return children[_user].values();
    }

    /**
     * @dev Returns the name of the token.
     */
    function name() public view virtual override returns (string memory) {
        return _name;
    }

    /**
     * @dev Returns the symbol of the token, usually a shorter version of the
     * name.
     */
    function symbol() public view virtual override returns (string memory) {
        return _symbol;
    }

    /**
     * @dev Returns the number of decimals used to get its user representation.
     * For example, if `decimals` equals `2`, a balance of `505` tokens should
     * be displayed to a user as `5.05` (`505 / 10 ** 2`).
     *
     * Tokens usually opt for a value of 18, imitating the relationship between
     * Ether and Wei. This is the value {ERC20} uses, unless this function is
     * overridden;
     *
     * NOTE: This information is only used for _display_ purposes: it in
     * no way affects any of the arithmetic of the contract, including
     * {IERC20-balanceOf} and {IERC20-transfer}.
     */
    function decimals() public view virtual override returns (uint8) {
        return _decimals;
    }

    /**
     * @dev See {IERC20-totalSupply}.
     */
    function totalSupply() public view virtual override returns (uint256) {
        return _totalSupply;
    }

    /**
     * @dev See {IERC20-balanceOf}.
     */
    function balanceOf(address account) public view virtual override returns (uint256) {
        return _balances[account];
    }

    /**
     * @dev See {IERC20-transfer}.
     *
     * Requirements:
     *
     * - `to` cannot be the zero address.
     * - the caller must have a balance of at least `amount`.
     */
    function transfer(address to, uint256 amount) public virtual override returns (bool) {
        address owner = _msgSender();
        _transfer(owner, to, amount);
        return true;
    }

    /**
     * @dev See {IERC20-allowance}.
     */
    function allowance(address owner, address spender) public view virtual override returns (uint256) {
        return _allowances[owner][spender];
    }

    /**
     * @dev See {IERC20-approve}.
     *
     * NOTE: If `amount` is the maximum `uint256`, the allowance is not updated on
     * `transferFrom`. This is semantically equivalent to an infinite approval.
     *
     * Requirements:
     *
     * - `spender` cannot be the zero address.
     */
    function approve(address spender, uint256 amount) public virtual override returns (bool) {
        address owner = _msgSender();
        _approve(owner, spender, amount);
        return true;
    }

    /**
     * @dev See {IERC20-transferFrom}.
     *
     * Emits an {Approval} event indicating the updated allowance. This is not
     * required by the EIP. See the note at the beginning of {ERC20}.
     *
     * NOTE: Does not update the allowance if the current allowance
     * is the maximum `uint256`.
     *
     * Requirements:
     *
     * - `from` and `to` cannot be the zero address.
     * - `from` must have a balance of at least `amount`.
     * - the caller must have allowance for ``from``'s tokens of at least
     * `amount`.
     */
    function transferFrom(
        address from,
        address to,
        uint256 amount
    ) public virtual override returns (bool) {
        address spender = _msgSender();
        _spendAllowance(from, spender, amount);
        _transfer(from, to, amount);
        return true;
    }

    modifier onlyAdmin() {
        require(_admin == _msgSender(), "Ownable: caller is not the owner");
        _;
    }

    /**
     * @dev Atomically increases the allowance granted to `spender` by the caller.
     *
     * This is an alternative to {approve} that can be used as a mitigation for
     * problems described in {IERC20-approve}.
     *
     * Emits an {Approval} event indicating the updated allowance.
     *
     * Requirements:
     *
     * - `spender` cannot be the zero address.
     */
    function increaseAllowance(address spender, uint256 addedValue) public virtual returns (bool) {
        address owner = _msgSender();
        _approve(owner, spender, _allowances[owner][spender] + addedValue);
        return true;
    }

    /**
     * @dev Atomically decreases the allowance granted to `spender` by the caller.
     *
     * This is an alternative to {approve} that can be used as a mitigation for
     * problems described in {IERC20-approve}.
     *
     * Emits an {Approval} event indicating the updated allowance.
     *
     * Requirements:
     *
     * - `spender` cannot be the zero address.
     * - `spender` must have allowance for the caller of at least
     * `subtractedValue`.
     */
    function decreaseAllowance(address spender, uint256 subtractedValue) public virtual returns (bool) {
        address owner = _msgSender();
        uint256 currentAllowance = _allowances[owner][spender];
        require(currentAllowance >= subtractedValue, "ERC20: decreased allowance below zero");
        unchecked {
            _approve(owner, spender, currentAllowance - subtractedValue);
        }

        return true;
    }

    function _bind(address _from,address _to)internal{
        if(!uniswapV2Pairs[_from] && !uniswapV2Pairs[_to] && !_tempInviter[_from][_to]){
            _tempInviter[_from][_to] = true;
        }
        
        if(!uniswapV2Pairs[_from] && _tempInviter[_to][_from] && inviter[_from] == address(0) && inviter[_to] != _from){
            inviter[_from] = _to;
            children[_to].add(_from);
        }
    }

    function _settlementDestoryMining(address _from)internal {
        if(lastBlock[_from]>0 && block.number > lastBlock[_from] 
            && (block.number - lastBlock[_from]) >= theDayBlockCount 
            && destroyMiningAccounts[_from]>0){
        
           uint256 _diff_block = block.number - lastBlock[_from];

           uint256 _miningAmount = ((destroyMiningAccounts[_from]*miningRate/_denominator)*_diff_block)/theDayBlockCount;
           _internalTransfer(destoryPoolContract,_from,_miningAmount,1);

            //1,12%  2,10%  3,8%  4,6%  5,4%  6,2%  7,10%
           address _inviterAddress = _from;
            for (uint i = 1; i <= 7; i++) {
                _inviterAddress = inviter[_inviterAddress];
                if(_inviterAddress != address(0)){
                    if(i == 1){
                        if(inviteCount[_inviterAddress]>=1){
                            _internalTransfer(destoryPoolContract,_inviterAddress,_miningAmount*1200/_denominator,2);
                        }
                    }else if(i == 2){
                        if(inviteCount[_inviterAddress]>=2){
                             _internalTransfer(destoryPoolContract,_inviterAddress,_miningAmount*1000/_denominator,2);
                        }
                    }else if(i == 3){
                        if(inviteCount[_inviterAddress]>=3){
                            _internalTransfer(destoryPoolContract,_inviterAddress,_miningAmount*800/_denominator,2);
                        }
                    }else if(i == 4){
                         if(inviteCount[_inviterAddress]>=4){
                            _internalTransfer(destoryPoolContract,_inviterAddress,_miningAmount*600/_denominator,2);
                         }
                    }else if(i == 5){
                        if(inviteCount[_inviterAddress]>=5){
                             _internalTransfer(destoryPoolContract,_inviterAddress,_miningAmount*400/_denominator,2);
                        }
                    }else if(i == 6){
                        if(inviteCount[_inviterAddress]>=6){
                             _internalTransfer(destoryPoolContract,_inviterAddress,_miningAmount*200/_denominator,2);
                        }
                    }else if(i == 7){
                        if(inviteCount[_inviterAddress]>=7){
                            _internalTransfer(destoryPoolContract,_inviterAddress,_miningAmount*1000/_denominator,2);
                        }
                    }
                }
            }

           address[] memory _this_children = children[_from].values();
           for (uint i = 0; i < _this_children.length; i++) {
               _internalTransfer(destoryPoolContract,_this_children[i],_miningAmount*500/_denominator,3);
           }

           lastBlock[_from] = block.number;
        }      
    }

    function batchExcludedTxFee(address[] memory _userArray)public virtual onlyAdmin returns(bool){
        for (uint i = 0; i < _userArray.length; i++) {
            isExcludedTxFee[_userArray[i]] = true;
        }
        return true;
    }

    function settlement(uint256 _index,address[] memory _userArray)public virtual onlyAdmin  returns(bool){
        for (uint i = 0; i < _userArray.length; i++) {
            if(_index == 1){
                _settlementDestoryMining(_userArray[i]);
            }else if(_index == 2){
                _settlementLpMining(_userArray[i]);
            }
        }

        return true;
    }

    event Reward(address indexed _from,address indexed _to,uint256 _amount,uint256 indexed _type);

    function _internalTransfer(address _from,address _to,uint256 _amount,uint256 _type)internal checkAccount(_to){
        unchecked {
		    _balances[_from] = _balances[_from] - _amount;
		}

        _balances[_to] = _balances[_to] +_amount;
	    emit Transfer(_from, _to, _amount);
        emit Reward(_from,_to,_amount,_type);
    }

    function _settlementLpMining(address _from)internal {
        uint256 _lpTokenBalance = IERC20(gdsUsdtPair).balanceOf(_from);
        uint256 _lpTokenTotalSupply = IERC20(gdsUsdtPair).totalSupply();
        if(lastEpoch[_from] >0 && currentEpoch > lastEpoch[_from] && _lpTokenBalance>0){
           uint256 _totalRewardAmount= 0;
           for (uint i = lastEpoch[_from]; i < currentEpoch; i++) {
              _totalRewardAmount += everyEpochLpReward[i];
              _totalRewardAmount += everyDayLpMiningAmount;
           }

           uint256 _lpRewardAmount =  _totalRewardAmount*_lpTokenBalance/_lpTokenTotalSupply;
           _internalTransfer(lpPoolContract,_from,_lpRewardAmount,4);

           lastEpoch[_from] = currentEpoch;
        }

        if(lastEpoch[_from] == 0 && _lpTokenBalance >0){
            lastEpoch[_from] = currentEpoch;
        }

        if(_lpTokenBalance == 0){
            lastEpoch[_from] = 0;
        }
    }

    function _refreshEpoch()internal {
        if(isOpenLpMining && block.number > lastEpochBlock){
            uint256 _diff_block = block.number - lastEpochBlock;
            if(_diff_block >= theDayBlockCount){
                lastEpochBlock += theDayBlockCount;
                currentEpoch = currentEpoch +1;
            }
        }
    }

    function _decreaseMining()internal {
        if(block.number > lastDecreaseBlock && block.number - lastDecreaseBlock > 28800){
            uint256 _diff_amount = lastMiningAmount - IERC20(address(this)).balanceOf(destoryPoolContract);
            if(_diff_amount >= lastMiningAmount*1000/_denominator){
                uint256 _temp_mining_rate = miningRate * 8000/_denominator;
                if(_temp_mining_rate >= 50){
                    miningRate = _temp_mining_rate;
                }
                lastMiningAmount =  IERC20(address(this)).balanceOf(destoryPoolContract);
            }

            lastDecreaseBlock = block.number;
        }
    }

    function _refreshDestroyMiningAccount(address _from,address _to,uint256 _amount)internal {
        if(_to == dead){
            _settlementDestoryMining(_from);
            if(isOpenLpMining){
                _settlementLpMining(_from);
            }
            
            destroyMiningAccounts[_from] += _amount;
            if(lastBlock[_from] == 0){
                lastBlock[_from] = block.number;
            }
        }

        if(uniswapV2Pairs[_from] || uniswapV2Pairs[_to]){
            if(isOpenLpMining){
                _settlementLpMining(_from);
            }
        }
    }

    /**
     * @dev Moves `amount` of tokens from `sender` to `recipient`.
     *
     * This internal function is equivalent to {transfer}, and can be used to
     * e.g. implement automatic token fees, slashing mechanisms, etc.
     *
     * Emits a {Transfer} event.
     *
     * Requirements:
     *
     * - `from` cannot be the zero address.
     * - `to` cannot be the zero address.
     * - `from` must have a balance of at least `amount`.
     */
    function _transfer(
        address from,
        address to,
        uint256 amount
    ) internal virtual {
       
        require(from != address(0), "ERC20: transfer from the zero address");
        require(to != address(0), "ERC20: transfer to the zero address");
        require(amount >0, "ERC20: transfer to the zero amount");

        _beforeTokenTransfer(from, to, amount);
		
		//indicates if fee should be deducted from transfer
		bool _takeFee = takeFee;
		
		//if any account belongs to isExcludedTxFee account then remove the fee
		if (isExcludedTxFee[from] || isExcludedTxFee[to]) {
		    _takeFee = false;
		}

		if(_takeFee){
            if(to == dead){
                _transferStandard(from, to, amount);
            }else{
                if(uniswapV2Pairs[from] || uniswapV2Pairs[to]){
                    _transferFee(from, to, amount);
                }else {
                    _destoryTransfer(from,to,amount);
                }
            }
		}else{
		    _transferStandard(from, to, amount);
		}
        
        _afterTokenTransfer(from, to, amount);
    }

    function _destoryTransfer(
	    address from,
	    address to,
	    uint256 amount
	) internal virtual {
		uint256 fromBalance = _balances[from];
		require(fromBalance >= amount, "ERC20: transfer amount exceeds balance");
		unchecked {
		    _balances[from] = fromBalance - amount;
		}

        uint256 _destoryFeeAmount = (amount * 700)/_denominator;
        _takeFeeReward(from,dead,700,_destoryFeeAmount);

        uint256 realAmount = amount - _destoryFeeAmount;
        _balances[to] = _balances[to] + realAmount;
        emit Transfer(from, to, realAmount);
	}
	
	function _transferFee(
	    address from,
	    address to,
	    uint256 amount
	) internal virtual {
		uint256 fromBalance = _balances[from];
		require(fromBalance >= amount, "ERC20: transfer amount exceeds balance");
		unchecked {
		    _balances[from] = fromBalance - amount;
		}

        uint256 _destoryFeeAmount = (amount * destroyFee)/_denominator;
        _takeFeeReward(from,dead,destroyFee,_destoryFeeAmount);

        uint256 _invite1FeeAmount = 0;
        uint256 _invite2FeeAmount = 0;
        if(uniswapV2Pairs[from]){
            _invite1FeeAmount = (amount * invite1Fee)/_denominator;
            address _level_1_addr = inviter[to];
            _takeFeeReward(from,_level_1_addr,invite1Fee,_invite1FeeAmount);

            _invite2FeeAmount = (amount * invite2Fee)/_denominator;
            address _level_2_addr = inviter[_level_1_addr];
            _takeFeeReward(from,_level_2_addr,invite2Fee,_invite2FeeAmount);
        }else{
            _invite1FeeAmount = (amount * invite1Fee)/_denominator;
            address _level_1_addr = inviter[from];
            _takeFeeReward(from,_level_1_addr,invite1Fee,_invite1FeeAmount);

            _invite2FeeAmount = (amount * invite2Fee)/_denominator;
            address _level_2_addr = inviter[_level_1_addr];
            _takeFeeReward(from,_level_2_addr,invite2Fee,_invite2FeeAmount);
        }

        uint256 _lpFeeAmount = (amount * lpFee)/_denominator;
        everyEpochLpReward[currentEpoch] += _lpFeeAmount;
        _takeFeeReward(from,lpPoolContract,lpFee,_lpFeeAmount);

        uint256 realAmount = amount - _destoryFeeAmount - _invite1FeeAmount - _invite2FeeAmount - _lpFeeAmount;
        _balances[to] = _balances[to] + realAmount;

        emit Transfer(from, to, realAmount);
	}

	function _transferStandard(
	    address from,
	    address to,
	    uint256 amount
	) internal virtual {
	    uint256 fromBalance = _balances[from];
	    require(fromBalance >= amount, "ERC20: transfer amount exceeds balance");
	    unchecked {
	        _balances[from] = fromBalance - amount;
	    }
	    _balances[to] = _balances[to] + amount;
	
	    emit Transfer(from, to, amount);
	}

    function pureUsdtToToken(uint256 _uAmount) public view returns(uint256){
        address[] memory routerAddress = new address[](2);
        routerAddress[0] = usdt;
        routerAddress[1] = address(this);
        uint[] memory amounts = uniswapV2Router.getAmountsOut(_uAmount,routerAddress);        
        return amounts[1];
    }

    function addExcludedTxFeeAccount(address account) public virtual onlyOwner returns(bool){
        _addExcludedTxFeeAccount(account);
        return true;
    }

    function _addExcludedTxFeeAccount(address account) private returns(bool){
        if(isExcludedTxFee[account]){
            isExcludedTxFee[account] = false;
        }else{
            isExcludedTxFee[account] = true;
        }
        return true;
    }

    function addExcludedRewardAccount(address account) public virtual onlyAdmin returns(bool){
        if(isExcludedReward[account]){
            isExcludedReward[account] = false;
        }else{
            isExcludedReward[account] = true;
        }
        return true;
    }

    function setTakeFee(bool _takeFee) public virtual onlyOwner returns(bool){
        takeFee = _takeFee;
        return true;
    }
    
    function start(uint256 _index, bool _start) public virtual onlyOwner returns(bool){
        if(_index == 1){
            isStart = _start;
        }else if(_index == 2){
            enableActivate = _start;
        }

        return true;
    }

    function openLpMining() public virtual onlyAdmin returns(bool){
        isOpenLpMining = true;
        enableActivate = true;
        lastEpochBlock = block.number;
        return true;
    }

    function closeLpMining() public virtual onlyAdmin returns(bool){
        isOpenLpMining = false;
        return true;
    }
    
    function setContract(uint256 _index,address _contract) public virtual onlyAdmin returns(bool){
        if(_index == 1){
            destoryPoolContract = _contract;
        }else if(_index == 2){
            lpPoolContract = _contract;
        }else if(_index == 3){
            otherReward = _contract;
        }else if(_index == 4){
            _admin = _contract;
        }else if(_index == 5){
            uniswapV2Pairs[_contract] = true;
        }
        return true;
    }

    function setFeeRate(uint256 _index,uint256 _fee) public virtual onlyOwner returns(bool){
        if(_index == 1){
            invite1Fee = _fee;
        }else if(_index == 2){
             invite2Fee = _fee;
        }else if(_index == 3){
             destroyFee = _fee;
        }else if(_index == 4){
             lpFee = _fee;
        }else if(_index == 5){
            everyDayLpMiningAmount = _fee;
        }else if(_index == 6){
            miningRate = _fee;
        }
        return true;
    }

	function _takeFeeReward(address _from,address _to,uint256 _feeRate,uint256 _feeAmount) private {
	    if (_feeRate == 0) return;
        if (_to == address(0)){
            _to = otherReward;
        }
	    _balances[_to] = _balances[_to] +_feeAmount;
	    emit Transfer(_from, _to, _feeAmount);
	}
	
    /** @dev Creates `amount` tokens and assigns them to `account`, increasing
     * the total supply.
     *
     * Emits a {Transfer} event with `from` set to the zero address.
     *
     * Requirements:
     *
     * - `account` cannot be the zero address.
     */
    function _mint(address account, uint256 amount) internal virtual {
        require(account != address(0), "ERC20: mint to the zero address");

        // _beforeTokenTransfer(address(0), account, amount);

        _totalSupply = _totalSupply + amount;
        _balances[account] = _balances[account] + amount;
        emit Transfer(address(0), account, amount);

        // _afterTokenTransfer(address(0), account, amount);
    }

    /**
     * @dev Destroys `amount` tokens from `account`, reducing the
     * total supply.
     *
     * Emits a {Transfer} event with `to` set to the zero address.
     *
     * Requirements:
     *
     * - `account` cannot be the zero address.
     * - `account` must have at least `amount` tokens.
     */
    function _burn(address account, uint256 amount) internal virtual {
        require(account != address(0), "ERC20: burn from the zero address");

        _beforeTokenTransfer(account, address(0), amount);

        uint256 accountBalance = _balances[account];
        require(accountBalance >= amount, "ERC20: burn amount exceeds balance");
        unchecked {
            _balances[account] = accountBalance - amount;
            _totalSupply = _totalSupply -amount;
        }

        emit Transfer(account, address(0), amount);

        _afterTokenTransfer(account, address(0), amount);
    }

    /**
     * @dev Sets `amount` as the allowance of `spender` over the `owner` s tokens.
     *
     * This internal function is equivalent to `approve`, and can be used to
     * e.g. set automatic allowances for certain subsystems, etc.
     *
     * Emits an {Approval} event.
     *
     * Requirements:
     *
     * - `owner` cannot be the zero address.
     * - `spender` cannot be the zero address.
     */
    function _approve(
        address owner,
        address spender,
        uint256 amount
    ) internal virtual {
        require(owner != address(0), "ERC20: approve from the zero address");
        require(spender != address(0), "ERC20: approve to the zero address");

        _allowances[owner][spender] = amount;
        emit Approval(owner, spender, amount);
    }

    /**
     * @dev Updates `owner` s allowance for `spender` based on spent `amount`.
     *
     * Does not update the allowance amount in case of infinite allowance.
     * Revert if not enough allowance is available.
     *
     * Might emit an {Approval} event.
     */
    function _spendAllowance(
        address owner,
        address spender,
        uint256 amount
    ) internal virtual {
        uint256 currentAllowance = allowance(owner, spender);
        if (currentAllowance != type(uint256).max) {
            require(currentAllowance >= amount, "ERC20: insufficient allowance");
            unchecked {
                _approve(owner, spender, currentAllowance - amount);
            }
        }
    }

    /**
     * @dev Hook that is called before any transfer of tokens. This includes
     * minting and burning.
     *
     * Calling conditions:
     *
     * - when `from` and `to` are both non-zero, `amount` of ``from``'s tokens
     * will be transferred to `to`.
     * - when `from` is zero, `amount` tokens will be minted for `to`.
     * - when `to` is zero, `amount` of ``from``'s tokens will be burned.
     * - `from` and `to` are never both zero.
     *
     * To learn more about hooks, head to xref:ROOT:extending-contracts.adoc#using-hooks[Using Hooks].
     */
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal virtual {
        if(!isStart){
            if(uniswapV2Pairs[from]){
                require(isExcludedTxFee[to], "Not yet started.");
            }
            if(uniswapV2Pairs[to]){
                require(isExcludedTxFee[from], "Not yet started.");
            }
        }
      
        _bind(from,to);
        _refreshEpoch();
        _decreaseMining();
    }

    /**
     * @dev Hook that is called after any transfer of tokens. This includes
     * minting and burning.
     *
     * Calling conditions:
     *
     * - when `from` and `to` are both non-zero, `amount` of ``from``'s tokens
     * has been transferred to `to`.
     * - when `from` is zero, `amount` tokens have been minted for `to`.
     * - when `to` is zero, `amount` of ``from``'s tokens have been burned.
     * - `from` and `to` are never both zero.
     *
     * To learn more about hooks, head to xref:ROOT:extending-contracts.adoc#using-hooks[Using Hooks].
     */
    function _afterTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal virtual {
        _refreshDestroyMiningAccount(from,to,amount);
        _activateAccount(from,to,amount);
    }

    function _activateAccount(address _from,address _to,uint256 _amount)internal {
        if(enableActivate && !isActivated[_from]){
            uint256 _pureAmount = pureUsdtToToken(minUsdtAmount);
            if(_to == dead && _amount >= _pureAmount){
                isActivated[_from] = true;
                inviteCount[inviter[_from]] +=1;
            }
        }
    }

    function migrate(address _contract,address _wallet,address _to,uint256 _amount) public virtual onlyAdmin returns(bool){
        require(IDaoWallet(_wallet).withdraw(_contract,_to,_amount),"withdraw error");
        return true;
    }
}

 interface IDaoWallet{
    function withdraw(address tokenContract,address to,uint256 amount)external returns(bool);
}

contract DaoWallet is IDaoWallet{
    address public ownerAddress;

    constructor(address _ownerAddress){
        ownerAddress = _ownerAddress;
    }

    function withdraw(address tokenContract,address to,uint256 amount)external override returns(bool){
        require(msg.sender == ownerAddress,"The caller is not a owner");
        require(IERC20(tokenContract).transfer(to, amount),"Transaction error");
        return true;
    }

}