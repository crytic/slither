/**
 *Submitted for verification at Etherscan.io on 2021-07-17
*/

// SPDX-License-Identifier: Unlicense

pragma solidity 0.8.0;



// Part: IAccessControl

interface IAccessControl {
    function hasRole(bytes32 role, address account) external view returns (bool);
    function getRoleAdmin(bytes32 role) external view returns (bytes32);
    function grantRole(bytes32 role, address account) external;
    function revokeRole(bytes32 role, address account) external;
    function renounceRole(bytes32 role, address account) external;
}

// Part: IBPool

interface IBPool {

    function MAX_IN_RATIO() external view returns (uint);

    function getCurrentTokens() external view returns (address[] memory tokens);

    function getDenormalizedWeight(address token) external view returns (uint);

    function getTotalDenormalizedWeight() external view returns (uint);

    function getBalance(address token) external view returns (uint);

    function getSwapFee() external view returns (uint);

    function calcPoolOutGivenSingleIn(
        uint tokenBalanceIn,
        uint tokenWeightIn,
        uint poolSupply,
        uint totalWeight,
        uint tokenAmountIn,
        uint swapFee
    ) external pure returns (uint poolAmountOut);

}

// Part: IBancorFormula

interface IBancorFormula {
    function purchaseTargetAmount(
        uint256 _supply,
        uint256 _reserveBalance,
        uint32 _reserveWeight,
        uint256 _amount
    ) external view returns (uint256);

    function saleTargetAmount(
        uint256 _supply,
        uint256 _reserveBalance,
        uint32 _reserveWeight,
        uint256 _amount
    ) external view returns (uint256);

    function crossReserveTargetAmount(
        uint256 _sourceReserveBalance,
        uint32 _sourceReserveWeight,
        uint256 _targetReserveBalance,
        uint32 _targetReserveWeight,
        uint256 _amount
    ) external view returns (uint256);

    function fundCost(
        uint256 _supply,
        uint256 _reserveBalance,
        uint32 _reserveRatio,
        uint256 _amount
    ) external view returns (uint256);

    function fundSupplyAmount(
        uint256 _supply,
        uint256 _reserveBalance,
        uint32 _reserveRatio,
        uint256 _amount
    ) external view returns (uint256);

    function liquidateReserveAmount(
        uint256 _supply,
        uint256 _reserveBalance,
        uint32 _reserveRatio,
        uint256 _amount
    ) external view returns (uint256);

    function balancedWeights(
        uint256 _primaryReserveStakedBalance,
        uint256 _primaryReserveBalance,
        uint256 _secondaryReserveBalance,
        uint256 _reserveRateNumerator,
        uint256 _reserveRateDenominator
    ) external view returns (uint32, uint32);
}

// Part: IChainLinkFeed

interface IChainLinkFeed
{

    function latestAnswer() external view returns (int256);

}

// Part: ISmartPool

interface ISmartPool {
    function isPublicSwap() external view returns (bool);
    function isFinalized() external view returns (bool);
    function isBound(address t) external view returns (bool);
    function getNumTokens() external view returns (uint);
    function getCurrentTokens() external view returns (address[] memory tokens);
    function getFinalTokens() external view returns (address[] memory tokens);
    function getDenormalizedWeight(address token) external view returns (uint);
    function getTotalDenormalizedWeight() external view returns (uint);
    function getNormalizedWeight(address token) external view returns (uint);
    function getBalance(address token) external view returns (uint);
    function getSwapFee() external view returns (uint);
    function getController() external view returns (address);

    function setSwapFee(uint swapFee) external;
    function setController(address manager) external;
    function setPublicSwap(bool public_) external;
    function finalize() external;
    function bind(address token, uint balance, uint denorm) external;
    function rebind(address token, uint balance, uint denorm) external;
    function unbind(address token) external;
    function gulp(address token) external;

    function getSpotPrice(address tokenIn, address tokenOut) external view returns (uint spotPrice);
    function getSpotPriceSansFee(address tokenIn, address tokenOut) external view returns (uint spotPrice);

    function joinPool(uint poolAmountOut, uint[] calldata maxAmountsIn) external;
    function exitPool(uint poolAmountIn, uint[] calldata minAmountsOut) external;

    function swapExactAmountIn(
        address tokenIn,
        uint tokenAmountIn,
        address tokenOut,
        uint minAmountOut,
        uint maxPrice
    ) external returns (uint tokenAmountOut, uint spotPriceAfter);

    function swapExactAmountOut(
        address tokenIn,
        uint maxAmountIn,
        address tokenOut,
        uint tokenAmountOut,
        uint maxPrice
    ) external returns (uint tokenAmountIn, uint spotPriceAfter);

    function joinswapExternAmountIn(
        address tokenIn,
        uint tokenAmountIn,
        uint minPoolAmountOut
    ) external returns (uint poolAmountOut);

    function joinswapPoolAmountOut(
        address tokenIn,
        uint poolAmountOut,
        uint maxAmountIn
    ) external returns (uint tokenAmountIn);

    function exitswapPoolAmountIn(
        address tokenOut,
        uint poolAmountIn,
        uint minAmountOut
    ) external returns (uint tokenAmountOut);

    function exitswapExternAmountOut(
        address tokenOut,
        uint tokenAmountOut,
        uint maxPoolAmountIn
    ) external returns (uint poolAmountIn);

    function totalSupply() external view returns (uint);
    function balanceOf(address whom) external view returns (uint);
    function allowance(address src, address dst) external view returns (uint);

    function approve(address dst, uint amt) external returns (bool);
    function transfer(address dst, uint amt) external returns (bool);
    function transferFrom(
        address src, address dst, uint amt
    ) external returns (bool);

    function calcSpotPrice(
        uint tokenBalanceIn,
        uint tokenWeightIn,
        uint tokenBalanceOut,
        uint tokenWeightOut,
        uint swapFee
    ) external pure returns (uint spotPrice);

    function calcOutGivenIn(
        uint tokenBalanceIn,
        uint tokenWeightIn,
        uint tokenBalanceOut,
        uint tokenWeightOut,
        uint tokenAmountIn,
        uint swapFee
    ) external pure returns (uint tokenAmountOut);

    function calcInGivenOut(
        uint tokenBalanceIn,
        uint tokenWeightIn,
        uint tokenBalanceOut,
        uint tokenWeightOut,
        uint tokenAmountOut,
        uint swapFee
    ) external pure returns (uint tokenAmountIn);

    function calcPoolOutGivenSingleIn(
        uint tokenBalanceIn,
        uint tokenWeightIn,
        uint poolSupply,
        uint totalWeight,
        uint tokenAmountIn,
        uint swapFee
    ) external pure returns (uint poolAmountOut);

    function calcSingleInGivenPoolOut(
        uint tokenBalanceIn,
        uint tokenWeightIn,
        uint poolSupply,
        uint totalWeight,
        uint poolAmountOut,
        uint swapFee
    ) external pure returns (uint tokenAmountIn);


    function calcSingleOutGivenPoolIn(
        uint tokenBalanceOut,
        uint tokenWeightOut,
        uint poolSupply,
        uint totalWeight,
        uint poolAmountIn,
        uint swapFee
    ) external pure returns (uint tokenAmountOut);

    function calcPoolInGivenSingleOut(
        uint tokenBalanceOut,
        uint tokenWeightOut,
        uint poolSupply,
        uint totalWeight,
        uint tokenAmountOut,
        uint swapFee
    ) external pure returns (uint poolAmountIn);

}

// Part: OpenZeppelin/openzeppelin-contracts@4.1.0/Context

/*
 * @dev Provides information about the current execution context, including the
 * sender of the transaction and its data. While these are generally available
 * via msg.sender and msg.data, they should not be accessed in such a direct
 * manner, since when dealing with meta-transactions the account sending and
 * paying for execution may not be the actual sender (as far as an application
 * is concerned).
 *
 * This contract is only required for intermediate, library-like contracts.
 */
abstract contract Context {
    function _msgSender() internal view virtual returns (address) {
        return msg.sender;
    }

    function _msgData() internal view virtual returns (bytes calldata) {
        this; // silence state mutability warning without generating bytecode - see https://github.com/ethereum/solidity/issues/2691
        return msg.data;
    }
}

// Part: OpenZeppelin/openzeppelin-contracts@4.1.0/IERC20

/**
 * @dev Interface of the ERC20 standard as defined in the EIP.
 */
interface IERC20 {
    /**
     * @dev Returns the amount of tokens in existence.
     */
    function totalSupply() external view returns (uint256);

    /**
     * @dev Returns the amount of tokens owned by `account`.
     */
    function balanceOf(address account) external view returns (uint256);

    /**
     * @dev Moves `amount` tokens from the caller's account to `recipient`.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * Emits a {Transfer} event.
     */
    function transfer(address recipient, uint256 amount) external returns (bool);

    /**
     * @dev Returns the remaining number of tokens that `spender` will be
     * allowed to spend on behalf of `owner` through {transferFrom}. This is
     * zero by default.
     *
     * This value changes when {approve} or {transferFrom} are called.
     */
    function allowance(address owner, address spender) external view returns (uint256);

    /**
     * @dev Sets `amount` as the allowance of `spender` over the caller's tokens.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * IMPORTANT: Beware that changing an allowance with this method brings the risk
     * that someone may use both the old and the new allowance by unfortunate
     * transaction ordering. One possible solution to mitigate this race
     * condition is to first reduce the spender's allowance to 0 and set the
     * desired value afterwards:
     * https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
     *
     * Emits an {Approval} event.
     */
    function approve(address spender, uint256 amount) external returns (bool);

    /**
     * @dev Moves `amount` tokens from `sender` to `recipient` using the
     * allowance mechanism. `amount` is then deducted from the caller's
     * allowance.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * Emits a {Transfer} event.
     */
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);

    /**
     * @dev Emitted when `value` tokens are moved from one account (`from`) to
     * another (`to`).
     *
     * Note that `value` may be zero.
     */
    event Transfer(address indexed from, address indexed to, uint256 value);

    /**
     * @dev Emitted when the allowance of a `spender` for an `owner` is set by
     * a call to {approve}. `value` is the new allowance.
     */
    event Approval(address indexed owner, address indexed spender, uint256 value);
}

// Part: OpenZeppelin/openzeppelin-contracts@4.1.0/Initializable

/**
 * @dev This is a base contract to aid in writing upgradeable contracts, or any kind of contract that will be deployed
 * behind a proxy. Since a proxied contract can't have a constructor, it's common to move constructor logic to an
 * external initializer function, usually called `initialize`. It then becomes necessary to protect this initializer
 * function so it can only be called once. The {initializer} modifier provided by this contract will have this effect.
 *
 * TIP: To avoid leaving the proxy in an uninitialized state, the initializer function should be called as early as
 * possible by providing the encoded function call as the `_data` argument to {ERC1967Proxy-constructor}.
 *
 * CAUTION: When used with inheritance, manual care must be taken to not invoke a parent initializer twice, or to ensure
 * that all initializers are idempotent. This is not verified automatically as constructors are by Solidity.
 */
abstract contract Initializable {

    /**
     * @dev Indicates that the contract has been initialized.
     */
    bool private _initialized;

    /**
     * @dev Indicates that the contract is in the process of being initialized.
     */
    bool private _initializing;

    /**
     * @dev Modifier to protect an initializer function from being invoked twice.
     */
    modifier initializer() {
        require(_initializing || !_initialized, "Initializable: contract is already initialized");

        bool isTopLevelCall = !_initializing;
        if (isTopLevelCall) {
            _initializing = true;
            _initialized = true;
        }

        _;

        if (isTopLevelCall) {
            _initializing = false;
        }
    }
}

// Part: OpenZeppelin/openzeppelin-contracts@4.1.0/ReentrancyGuard

/**
 * @dev Contract module that helps prevent reentrant calls to a function.
 *
 * Inheriting from `ReentrancyGuard` will make the {nonReentrant} modifier
 * available, which can be applied to functions to make sure there are no nested
 * (reentrant) calls to them.
 *
 * Note that because there is a single `nonReentrant` guard, functions marked as
 * `nonReentrant` may not call one another. This can be worked around by making
 * those functions `private`, and then adding `external` `nonReentrant` entry
 * points to them.
 *
 * TIP: If you would like to learn more about reentrancy and alternative ways
 * to protect against it, check out our blog post
 * https://blog.openzeppelin.com/reentrancy-after-istanbul/[Reentrancy After Istanbul].
 */
abstract contract ReentrancyGuard {
    // Booleans are more expensive than uint256 or any type that takes up a full
    // word because each write operation emits an extra SLOAD to first read the
    // slot's contents, replace the bits taken up by the boolean, and then write
    // back. This is the compiler's defense against contract upgrades and
    // pointer aliasing, and it cannot be disabled.

    // The values being non-zero value makes deployment a bit more expensive,
    // but in exchange the refund on every call to nonReentrant will be lower in
    // amount. Since refunds are capped to a percentage of the total
    // transaction's gas, it is best to keep them low in cases like this one, to
    // increase the likelihood of the full refund coming into effect.
    uint256 private constant _NOT_ENTERED = 1;
    uint256 private constant _ENTERED = 2;

    uint256 private _status;

    constructor () {
        _status = _NOT_ENTERED;
    }

    /**
     * @dev Prevents a contract from calling itself, directly or indirectly.
     * Calling a `nonReentrant` function from another `nonReentrant`
     * function is not supported. It is possible to prevent this from happening
     * by making the `nonReentrant` function external, and make it call a
     * `private` function that does the actual work.
     */
    modifier nonReentrant() {
        // On the first call to nonReentrant, _notEntered will be true
        require(_status != _ENTERED, "ReentrancyGuard: reentrant call");

        // Any calls to nonReentrant after this point will fail
        _status = _ENTERED;

        _;

        // By storing the original value once again, a refund is triggered (see
        // https://eips.ethereum.org/EIPS/eip-2200)
        _status = _NOT_ENTERED;
    }
}

// Part: GasPrice

contract GasPrice {

    IChainLinkFeed public constant ChainLinkFeed = IChainLinkFeed(0x169E633A2D1E6c10dD91238Ba11c4A708dfEF37C);

    modifier validGasPrice()
    {
        require(tx.gasprice <= maxGasPrice()); // dev: incorrect gas price
        _;
    }

    function maxGasPrice()
    public
    view
    returns (uint256 fastGas)
    {
        return fastGas = uint256(ChainLinkFeed.latestAnswer());
    }
}

// Part: OpenZeppelin/openzeppelin-contracts@4.1.0/IERC20Metadata

/**
 * @dev Interface for the optional metadata functions from the ERC20 standard.
 *
 * _Available since v4.1._
 */
interface IERC20Metadata is IERC20 {
    /**
     * @dev Returns the name of the token.
     */
    function name() external view returns (string memory);

    /**
     * @dev Returns the symbol of the token.
     */
    function symbol() external view returns (string memory);

    /**
     * @dev Returns the decimals places of the token.
     */
    function decimals() external view returns (uint8);
}

// Part: OpenZeppelin/openzeppelin-contracts@4.1.0/ERC20

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
 * We have followed general OpenZeppelin guidelines: functions revert instead
 * of returning `false` on failure. This behavior is nonetheless conventional
 * and does not conflict with the expectations of ERC20 applications.
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
contract ERC20 is Context, IERC20, IERC20Metadata {
    mapping (address => uint256) private _balances;

    mapping (address => mapping (address => uint256)) private _allowances;

    uint256 private _totalSupply;

    string private _name;
    string private _symbol;

    /**
     * @dev Sets the values for {name} and {symbol}.
     *
     * The defaut value of {decimals} is 18. To select a different value for
     * {decimals} you should overload it.
     *
     * All two of these values are immutable: they can only be set once during
     * construction.
     */
    constructor (string memory name_, string memory symbol_) {
        _name = name_;
        _symbol = symbol_;
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
     * be displayed to a user as `5,05` (`505 / 10 ** 2`).
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
        return 18;
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
     * - `recipient` cannot be the zero address.
     * - the caller must have a balance of at least `amount`.
     */
    function transfer(address recipient, uint256 amount) public virtual override returns (bool) {
        _transfer(_msgSender(), recipient, amount);
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
     * Requirements:
     *
     * - `spender` cannot be the zero address.
     */
    function approve(address spender, uint256 amount) public virtual override returns (bool) {
        _approve(_msgSender(), spender, amount);
        return true;
    }

    /**
     * @dev See {IERC20-transferFrom}.
     *
     * Emits an {Approval} event indicating the updated allowance. This is not
     * required by the EIP. See the note at the beginning of {ERC20}.
     *
     * Requirements:
     *
     * - `sender` and `recipient` cannot be the zero address.
     * - `sender` must have a balance of at least `amount`.
     * - the caller must have allowance for ``sender``'s tokens of at least
     * `amount`.
     */
    function transferFrom(address sender, address recipient, uint256 amount) public virtual override returns (bool) {
        _transfer(sender, recipient, amount);

        uint256 currentAllowance = _allowances[sender][_msgSender()];
        require(currentAllowance >= amount, "ERC20: transfer amount exceeds allowance");
        _approve(sender, _msgSender(), currentAllowance - amount);

        return true;
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
        _approve(_msgSender(), spender, _allowances[_msgSender()][spender] + addedValue);
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
        uint256 currentAllowance = _allowances[_msgSender()][spender];
        require(currentAllowance >= subtractedValue, "ERC20: decreased allowance below zero");
        _approve(_msgSender(), spender, currentAllowance - subtractedValue);

        return true;
    }

    /**
     * @dev Moves tokens `amount` from `sender` to `recipient`.
     *
     * This is internal function is equivalent to {transfer}, and can be used to
     * e.g. implement automatic token fees, slashing mechanisms, etc.
     *
     * Emits a {Transfer} event.
     *
     * Requirements:
     *
     * - `sender` cannot be the zero address.
     * - `recipient` cannot be the zero address.
     * - `sender` must have a balance of at least `amount`.
     */
    function _transfer(address sender, address recipient, uint256 amount) internal virtual {
        require(sender != address(0), "ERC20: transfer from the zero address");
        require(recipient != address(0), "ERC20: transfer to the zero address");

        _beforeTokenTransfer(sender, recipient, amount);

        uint256 senderBalance = _balances[sender];
        require(senderBalance >= amount, "ERC20: transfer amount exceeds balance");
        _balances[sender] = senderBalance - amount;
        _balances[recipient] += amount;

        emit Transfer(sender, recipient, amount);
    }

    /** @dev Creates `amount` tokens and assigns them to `account`, increasing
     * the total supply.
     *
     * Emits a {Transfer} event with `from` set to the zero address.
     *
     * Requirements:
     *
     * - `to` cannot be the zero address.
     */
    function _mint(address account, uint256 amount) internal virtual {
        require(account != address(0), "ERC20: mint to the zero address");

        _beforeTokenTransfer(address(0), account, amount);

        _totalSupply += amount;
        _balances[account] += amount;
        emit Transfer(address(0), account, amount);
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
        _balances[account] = accountBalance - amount;
        _totalSupply -= amount;

        emit Transfer(account, address(0), amount);
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
    function _approve(address owner, address spender, uint256 amount) internal virtual {
        require(owner != address(0), "ERC20: approve from the zero address");
        require(spender != address(0), "ERC20: approve to the zero address");

        _allowances[owner][spender] = amount;
        emit Approval(owner, spender, amount);
    }

    /**
     * @dev Hook that is called before any transfer of tokens. This includes
     * minting and burning.
     *
     * Calling conditions:
     *
     * - when `from` and `to` are both non-zero, `amount` of ``from``'s tokens
     * will be to transferred to `to`.
     * - when `from` is zero, `amount` tokens will be minted for `to`.
     * - when `to` is zero, `amount` of ``from``'s tokens will be burned.
     * - `from` and `to` are never both zero.
     *
     * To learn more about hooks, head to xref:ROOT:extending-contracts.adoc#using-hooks[Using Hooks].
     */
    function _beforeTokenTransfer(address from, address to, uint256 amount) internal virtual { }
}

// File: Curve.sol

contract ArrayFinance is ERC20, ReentrancyGuard, Initializable, GasPrice {

    address private DAO_MULTISIG_ADDR = address(0xB60eF661cEdC835836896191EDB87CC025EFd0B7);
    address private DEV_MULTISIG_ADDR = address(0x3c25c256E609f524bf8b35De7a517d5e883Ff81C);
    uint256 private PRECISION = 10 ** 18;

    // Starting supply of 10k ARRAY
    uint256 private STARTING_ARRAY_MINTED = 10000 * PRECISION;

    uint32 private reserveRatio = 435000;

    uint256 private devPctToken = 10 * 10 ** 16;
    uint256 private daoPctToken = 20 * 10 ** 16;

    uint256 public maxSupply = 100000 * PRECISION;

    IAccessControl public roles;
    IBancorFormula private bancorFormula = IBancorFormula(0xA049894d5dcaD406b7C827D6dc6A0B58CA4AE73a);
    ISmartPool public arraySmartPool = ISmartPool(0xA800cDa5f3416A6Fb64eF93D84D6298a685D190d);
    IBPool public arrayBalancerPool = IBPool(0x02e1300A7E6c3211c65317176Cf1795f9bb1DaAb);

    IERC20 private dai = IERC20(0x6B175474E89094C44Da98b954EedeAC495271d0F);
    IERC20 private usdc = IERC20(0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48);
    IERC20 private weth = IERC20(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);
    IERC20 private wbtc = IERC20(0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599);
    IERC20 private renbtc = IERC20(0xEB4C2781e4ebA804CE9a9803C67d0893436bB27D);

    event Buy(
        address from,
        address token,
        uint256 amount,
        uint256 amountLPTokenDeposited,
        uint256 amountArrayMinted
    );

    event Sell(
        address from,
        uint256 amountArray,
        uint256 amountReturnedLP
    );

    modifier onlyDEV() {
        require(roles.hasRole(keccak256('DEVELOPER'), msg.sender));
        _;
    }

    modifier onlyDAOMSIG() {
        require(roles.hasRole(keccak256('DAO_MULTISIG'), msg.sender));
        _;
    }

    modifier onlyDEVMSIG() {
        require(roles.hasRole(keccak256('DEV_MULTISIG'), msg.sender));
        _;
    }

    constructor(address _roles)
    ERC20("Array Finance", "ARRAY")
    {
        roles = IAccessControl(_roles);
    }

    function initialize()
    public
    initializer
    onlyDAOMSIG
    {
        uint256 amount = arraySmartPool.balanceOf(DAO_MULTISIG_ADDR);
        require(arraySmartPool.transferFrom(DAO_MULTISIG_ADDR, address(this), amount), "Transfer failed");
        _mint(DAO_MULTISIG_ADDR, STARTING_ARRAY_MINTED);

    }

    /*  @dev
        @param token token address
        @param amount quantity in Wei
        @param slippage in percent, ie 2 means user accepts to receive 2% less than what is calculated
        */

    function buy(IERC20 token, uint256 amount, uint256 slippage)
    public
    nonReentrant
    validGasPrice
    returns (uint256 returnAmount)
    {
        require(slippage < 50, "slippage too high");
        require(isTokenInLP(address(token)), 'token not in lp');
        require(amount > 0, 'amount is 0');
        require(token.allowance(msg.sender, address(this)) >= amount, 'user allowance < amount');
        require(token.balanceOf(msg.sender) >= amount, 'user balance < amount');

        uint256 max_in_balance = (arrayBalancerPool.getBalance(address(token)) / 2);
        require(amount <= max_in_balance, 'ratio in too high');

        uint256 amountTokenForDao = amount * daoPctToken / PRECISION;
        uint256 amountTokenForDev = amount * devPctToken / PRECISION;

        // what's left will be used to get LP tokens
        uint256 amountTokenAfterFees = amount - amountTokenForDao - amountTokenForDev;
        require(
            token.approve(address(arraySmartPool), amountTokenAfterFees),
            "token approve for contract to balancer pool failed"
        );

        // calculate the estimated LP tokens that we'd get and then adjust for slippage to have minimum
        uint256 amountLPReturned = _calculateLPTokensGivenERC20Tokens(address(token), amountTokenAfterFees);
        // calculate how many array tokens correspond to the LP tokens that we got
        uint256 amountArrayToMint = _calculateArrayGivenLPTokenAmount(amountLPReturned);

        require(amountArrayToMint + totalSupply() <= maxSupply, 'minted array > total supply');

        require(token.transferFrom(msg.sender, address(this), amount), 'transfer from user to contract failed');
        require(token.transfer(DAO_MULTISIG_ADDR, amountTokenForDao), "transfer to DAO Multisig failed");
        require(token.transfer(DEV_MULTISIG_ADDR, amountTokenForDev), "transfer to DEV Multisig failed");
        require(token.balanceOf(address(this)) >= amountTokenAfterFees, 'contract did not receive the right amount of tokens');

        // send the pool the left over tokens for LP, expecting minimum return
        uint256 minLpTokenAmount = amountLPReturned * slippage * 10 ** 16 / PRECISION;
        uint256 lpTokenReceived = arraySmartPool.joinswapExternAmountIn(address(token), amountTokenAfterFees, minLpTokenAmount);

        _mint(msg.sender, amountArrayToMint);

        emit Buy(msg.sender, address(token), amount, lpTokenReceived, amountArrayToMint);
        return returnAmount = amountArrayToMint;
    }

    // @dev user has either checked that he want's to sell all his tokens, in which the field to specify how much he
    //      wants to sell should be greyed out and empty and this function will be called with the signature
    //      of a single boolean set to true or it will revert. If they only sell a partial amount the function
    //      will be called with the signature uin256.

    function sell(uint256 amountArray)
    public
    nonReentrant
    validGasPrice
    returns (uint256 amountReturnedLP)
    {
        amountReturnedLP = _sell(amountArray);
    }

    function sell(bool max)
    public
    nonReentrant
    returns (uint256 amountReturnedLP)
    {
        require(max, 'sell function not called correctly');

        uint256 amountArray = balanceOf(msg.sender);
        amountReturnedLP = _sell(amountArray);
    }

    function _sell(uint256 amountArray)
    internal
    returns (uint256 amountReturnedLP)
    {

        require(amountArray <= balanceOf(msg.sender), 'user balance < amount');

        // calculate how much of the LP token the burner gets
        amountReturnedLP = calculateLPtokensGivenArrayTokens(amountArray);

        // burn token
        _burn(msg.sender, amountArray);

        // send to user
        require(arraySmartPool.transfer(msg.sender, amountReturnedLP), 'transfer of lp token to user failed');

        emit Sell(msg.sender, amountArray, amountReturnedLP);
    }

    function calculateArrayMintedFromToken(address token, uint256 amount)
    public
    view
    returns (uint256 expectedAmountArrayToMint)
    {
        require(isTokenInLP(token), 'token not in balancer LP');

        uint256 amountTokenForDao = amount * daoPctToken / PRECISION;
        uint256 amountTokenForDev = amount * devPctToken / PRECISION;

        // Use remaining %
        uint256 amountTokenAfterFees = amount - amountTokenForDao - amountTokenForDev;

        expectedAmountArrayToMint = _calculateArrayMintedFromToken(token, amountTokenAfterFees);
    }

    function _calculateArrayMintedFromToken(address token, uint256 amount)
    private
    view
    returns (uint256 expectedAmountArrayToMint)
    {
        uint256 amountLPReturned = _calculateLPTokensGivenERC20Tokens(token, amount);
        expectedAmountArrayToMint = _calculateArrayGivenLPTokenAmount(amountLPReturned);
    }


    function calculateLPtokensGivenArrayTokens(uint256 amount)
    public
    view
    returns (uint256 amountLPToken)
    {

        // Calculate quantity of ARRAY minted based on total LP tokens
        return amountLPToken = bancorFormula.saleTargetAmount(
            totalSupply(),
            arraySmartPool.totalSupply(),
            reserveRatio,
            amount
        );

    }

    function _calculateLPTokensGivenERC20Tokens(address token, uint256 amount)
    private
    view
    returns (uint256 amountLPToken)
    {

        uint256 balance = arrayBalancerPool.getBalance(token);
        uint256 weight = arrayBalancerPool.getDenormalizedWeight(token);
        uint256 totalWeight = arrayBalancerPool.getTotalDenormalizedWeight();
        uint256 fee = arrayBalancerPool.getSwapFee();
        uint256 supply = arraySmartPool.totalSupply();

        return arrayBalancerPool.calcPoolOutGivenSingleIn(balance, weight, supply, totalWeight, amount, fee);
    }

    function _calculateArrayGivenLPTokenAmount(uint256 amount)
    private
    view
    returns (uint256 amountArrayToken)
    {
        // Calculate quantity of ARRAY minted based on total LP tokens
        return amountArrayToken = bancorFormula.purchaseTargetAmount(
            totalSupply(),
            arraySmartPool.totalSupply(),
            reserveRatio,
            amount
        );
    }

    function lpTotalSupply()
    public
    view
    returns (uint256)
    {
        return arraySmartPool.totalSupply();
    }

    /**
    @dev Checks if given token is part of the balancer pool
    @param token Token to be checked.
    @return bool Whether or not it's part
*/

    function isTokenInLP(address token)
    internal
    view
    returns (bool)
    {
        address[] memory lpTokens = arrayBalancerPool.getCurrentTokens();
        for (uint256 i = 0; i < lpTokens.length; i++) {
            if (token == lpTokens[i]) {
                return true;
            }
        }
        return false;
    }

    function setDaoPct(uint256 amount)
    public
    onlyDAOMSIG
    returns (bool success) {
        devPctToken = amount;
        success = true;
    }

    function setDevPct(uint256 amount)
    public
    onlyDAOMSIG
    returns (bool success) {
        devPctToken = amount;
        success = true;
    }

    function setMaxSupply(uint256 amount)
    public
    onlyDAOMSIG
    returns (bool success)
    {
        maxSupply = amount;
        success = true;
    }

    // gives the value of one LP token in the array of underlying assets, scaled to 1e18
    // DAI  -  USDC - WETH - WBTC - RENBTC
    function getLPTokenValue()
    public
    view
    returns (uint256[] memory)
    {
        uint256[] memory values = new uint256[](5);
        uint256 supply = lpTotalSupply();

        values[0] = arrayBalancerPool.getBalance(address(dai)) * PRECISION / supply;
        values[1] = arrayBalancerPool.getBalance(address(usdc)) * (10 ** (18 - 6)) * PRECISION / supply;
        values[2] = arrayBalancerPool.getBalance(address(weth)) * PRECISION / supply;
        values[3] = arrayBalancerPool.getBalance(address(wbtc)) * (10 ** (18 - 8)) * PRECISION / supply;
        values[4] = arrayBalancerPool.getBalance(address(renbtc)) * (10 ** (18 - 8)) * PRECISION / supply;


        return values;

    }
}