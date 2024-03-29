/**
 *Submitted for verification at BscScan.com on 2021-02-28
*/

// SPDX-License-Identifier: MIT

pragma solidity 0.6.11;

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
    function transferFrom(
        address sender,
        address recipient,
        uint256 amount
    ) external returns (bool);

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

/**
 * @dev Wrappers over Solidity's arithmetic operations with added overflow
 * checks.
 *
 * Arithmetic operations in Solidity wrap on overflow. This can easily result
 * in bugs, because programmers usually assume that an overflow raises an
 * error, which is the standard behavior in high level programming languages.
 * `SafeMath` restores this intuition by reverting the transaction when an
 * operation overflows.
 *
 * Using this library instead of the unchecked operations eliminates an entire
 * class of bugs, so it's recommended to use it always.
 */
library SafeMath {
    /**
     * @dev Returns the addition of two unsigned integers, reverting on
     * overflow.
     *
     * Counterpart to Solidity's `+` operator.
     *
     * Requirements:
     *
     * - Addition cannot overflow.
     */
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        uint256 c = a + b;
        require(c >= a, "SafeMath: addition overflow");

        return c;
    }

    /**
     * @dev Returns the subtraction of two unsigned integers, reverting on
     * overflow (when the result is negative).
     *
     * Counterpart to Solidity's `-` operator.
     *
     * Requirements:
     *
     * - Subtraction cannot overflow.
     */
    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        return sub(a, b, "SafeMath: subtraction overflow");
    }

    /**
     * @dev Returns the subtraction of two unsigned integers, reverting with custom message on
     * overflow (when the result is negative).
     *
     * Counterpart to Solidity's `-` operator.
     *
     * Requirements:
     *
     * - Subtraction cannot overflow.
     */
    function sub(
        uint256 a,
        uint256 b,
        string memory errorMessage
    ) internal pure returns (uint256) {
        require(b <= a, errorMessage);
        uint256 c = a - b;

        return c;
    }

    /**
     * @dev Returns the multiplication of two unsigned integers, reverting on
     * overflow.
     *
     * Counterpart to Solidity's `*` operator.
     *
     * Requirements:
     *
     * - Multiplication cannot overflow.
     */
    function mul(uint256 a, uint256 b) internal pure returns (uint256) {
        // Gas optimization: this is cheaper than requiring 'a' not being zero, but the
        // benefit is lost if 'b' is also tested.
        // See: https://github.com/OpenZeppelin/openzeppelin-contracts/pull/522
        if (a == 0) {
            return 0;
        }

        uint256 c = a * b;
        require(c / a == b, "SafeMath: multiplication overflow");

        return c;
    }

    /**
     * @dev Returns the integer division of two unsigned integers. Reverts on
     * division by zero. The result is rounded towards zero.
     *
     * Counterpart to Solidity's `/` operator. Note: this function uses a
     * `revert` opcode (which leaves remaining gas untouched) while Solidity
     * uses an invalid opcode to revert (consuming all remaining gas).
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        return div(a, b, "SafeMath: division by zero");
    }

    /**
     * @dev Returns the integer division of two unsigned integers. Reverts with custom message on
     * division by zero. The result is rounded towards zero.
     *
     * Counterpart to Solidity's `/` operator. Note: this function uses a
     * `revert` opcode (which leaves remaining gas untouched) while Solidity
     * uses an invalid opcode to revert (consuming all remaining gas).
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function div(
        uint256 a,
        uint256 b,
        string memory errorMessage
    ) internal pure returns (uint256) {
        require(b > 0, errorMessage);
        uint256 c = a / b;
        // assert(a == b * c + a % b); // There is no case in which this doesn't hold

        return c;
    }

    /**
     * @dev Returns the remainder of dividing two unsigned integers. (unsigned integer modulo),
     * Reverts when dividing by zero.
     *
     * Counterpart to Solidity's `%` operator. This function uses a `revert`
     * opcode (which leaves remaining gas untouched) while Solidity uses an
     * invalid opcode to revert (consuming all remaining gas).
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function mod(uint256 a, uint256 b) internal pure returns (uint256) {
        return mod(a, b, "SafeMath: modulo by zero");
    }

    /**
     * @dev Returns the remainder of dividing two unsigned integers. (unsigned integer modulo),
     * Reverts with custom message when dividing by zero.
     *
     * Counterpart to Solidity's `%` operator. This function uses a `revert`
     * opcode (which leaves remaining gas untouched) while Solidity uses an
     * invalid opcode to revert (consuming all remaining gas).
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function mod(
        uint256 a,
        uint256 b,
        string memory errorMessage
    ) internal pure returns (uint256) {
        require(b != 0, errorMessage);
        return a % b;
    }
}

/**
 * @dev Collection of functions related to the address type
 */
library Address {
    /**
     * @dev Returns true if `account` is a contract.
     *
     * [IMPORTANT]
     * ====
     * It is unsafe to assume that an address for which this function returns
     * false is an externally-owned account (EOA) and not a contract.
     *
     * Among others, `isContract` will return false for the following
     * types of addresses:
     *
     *  - an externally-owned account
     *  - a contract in construction
     *  - an address where a contract will be created
     *  - an address where a contract lived, but was destroyed
     * ====
     */
    function isContract(address account) internal view returns (bool) {
        // This method relies in extcodesize, which returns 0 for contracts in
        // construction, since the code is only stored at the end of the
        // constructor execution.

        uint256 size;
        // solhint-disable-next-line no-inline-assembly
        assembly {
            size := extcodesize(account)
        }
        return size > 0;
    }

    /**
     * @dev Replacement for Solidity's `transfer`: sends `amount` wei to
     * `recipient`, forwarding all available gas and reverting on errors.
     *
     * https://eips.ethereum.org/EIPS/eip-1884[EIP1884] increases the gas cost
     * of certain opcodes, possibly making contracts go over the 2300 gas limit
     * imposed by `transfer`, making them unable to receive funds via
     * `transfer`. {sendValue} removes this limitation.
     *
     * https://diligence.consensys.net/posts/2019/09/stop-using-soliditys-transfer-now/[Learn more].
     *
     * IMPORTANT: because control is transferred to `recipient`, care must be
     * taken to not create reentrancy vulnerabilities. Consider using
     * {ReentrancyGuard} or the
     * https://solidity.readthedocs.io/en/v0.5.11/security-considerations.html#use-the-checks-effects-interactions-pattern[checks-effects-interactions pattern].
     */
    function sendValue(address payable recipient, uint256 amount) internal {
        require(address(this).balance >= amount, "Address: insufficient balance");

        // solhint-disable-next-line avoid-low-level-calls, avoid-call-value
        (bool success, ) = recipient.call{value: amount}("");
        require(success, "Address: unable to send value, recipient may have reverted");
    }

    /**
     * @dev Performs a Solidity function call using a low level `call`. A
     * plain`call` is an unsafe replacement for a function call: use this
     * function instead.
     *
     * If `target` reverts with a revert reason, it is bubbled up by this
     * function (like regular Solidity function calls).
     *
     * Returns the raw returned data. To convert to the expected return value,
     * use https://solidity.readthedocs.io/en/latest/units-and-global-variables.html?highlight=abi.decode#abi-encoding-and-decoding-functions[`abi.decode`].
     *
     * Requirements:
     *
     * - `target` must be a contract.
     * - calling `target` with `data` must not revert.
     *
     * _Available since v3.1._
     */
    function functionCall(address target, bytes memory data) internal returns (bytes memory) {
        return functionCall(target, data, "Address: low-level call failed");
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`], but with
     * `errorMessage` as a fallback revert reason when `target` reverts.
     *
     * _Available since v3.1._
     */
    function functionCall(
        address target,
        bytes memory data,
        string memory errorMessage
    ) internal returns (bytes memory) {
        return _functionCallWithValue(target, data, 0, errorMessage);
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`],
     * but also transferring `value` wei to `target`.
     *
     * Requirements:
     *
     * - the calling contract must have an ETH balance of at least `value`.
     * - the called Solidity function must be `payable`.
     *
     * _Available since v3.1._
     */
    function functionCallWithValue(
        address target,
        bytes memory data,
        uint256 value
    ) internal returns (bytes memory) {
        return functionCallWithValue(target, data, value, "Address: low-level call with value failed");
    }

    /**
     * @dev Same as {xref-Address-functionCallWithValue-address-bytes-uint256-}[`functionCallWithValue`], but
     * with `errorMessage` as a fallback revert reason when `target` reverts.
     *
     * _Available since v3.1._
     */
    function functionCallWithValue(
        address target,
        bytes memory data,
        uint256 value,
        string memory errorMessage
    ) internal returns (bytes memory) {
        require(address(this).balance >= value, "Address: insufficient balance for call");
        return _functionCallWithValue(target, data, value, errorMessage);
    }

    function _functionCallWithValue(
        address target,
        bytes memory data,
        uint256 weiValue,
        string memory errorMessage
    ) private returns (bytes memory) {
        require(isContract(target), "Address: call to non-contract");

        // solhint-disable-next-line avoid-low-level-calls
        (bool success, bytes memory returndata) = target.call{value: weiValue}(data);
        if (success) {
            return returndata;
        } else {
            // Look for revert reason and bubble it up if present
            if (returndata.length > 0) {
                // The easiest way to bubble the revert reason is using memory via assembly

                // solhint-disable-next-line no-inline-assembly
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

/**
 * @title SafeERC20
 * @dev Wrappers around ERC20 operations that throw on failure (when the token
 * contract returns false). Tokens that return no value (and instead revert or
 * throw on failure) are also supported, non-reverting calls are assumed to be
 * successful.
 * To use this library you can add a `using SafeERC20 for IERC20;` statement to your contract,
 * which allows you to call the safe operations as `token.safeTransfer(...)`, etc.
 */
library SafeERC20 {
    using SafeMath for uint256;
    using Address for address;

    function safeTransfer(
        IERC20 token,
        address to,
        uint256 value
    ) internal {
        _callOptionalReturn(token, abi.encodeWithSelector(token.transfer.selector, to, value));
    }

    function safeTransferFrom(
        IERC20 token,
        address from,
        address to,
        uint256 value
    ) internal {
        _callOptionalReturn(token, abi.encodeWithSelector(token.transferFrom.selector, from, to, value));
    }

    /**
     * @dev Deprecated. This function has issues similar to the ones found in
     * {IERC20-approve}, and its usage is discouraged.
     *
     * Whenever possible, use {safeIncreaseAllowance} and
     * {safeDecreaseAllowance} instead.
     */
    function safeApprove(
        IERC20 token,
        address spender,
        uint256 value
    ) internal {
        // safeApprove should only be called when setting an initial allowance,
        // or when resetting it to zero. To increase and decrease it, use
        // 'safeIncreaseAllowance' and 'safeDecreaseAllowance'
        // solhint-disable-next-line max-line-length
        require((value == 0) || (token.allowance(address(this), spender) == 0), "SafeERC20: approve from non-zero to non-zero allowance");
        _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, value));
    }

    function safeIncreaseAllowance(
        IERC20 token,
        address spender,
        uint256 value
    ) internal {
        uint256 newAllowance = token.allowance(address(this), spender).add(value);
        _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, newAllowance));
    }

    function safeDecreaseAllowance(
        IERC20 token,
        address spender,
        uint256 value
    ) internal {
        uint256 newAllowance = token.allowance(address(this), spender).sub(value, "SafeERC20: decreased allowance below zero");
        _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, newAllowance));
    }

    /**
     * @dev Imitates a Solidity high-level call (i.e. a regular function call to a contract), relaxing the requirement
     * on the return value: the return value is optional (but if data is returned, it must not be false).
     * @param token The token targeted by the call.
     * @param data The call data (encoded using abi.encode or one of its variants).
     */
    function _callOptionalReturn(IERC20 token, bytes memory data) private {
        // We need to perform a low level call here, to bypass Solidity's return data size checking mechanism, since
        // we're implementing it ourselves. We use {Address.functionCall} to perform this call, which verifies that
        // the target address contains contract code and also asserts for success in the low-level call.

        bytes memory returndata = address(token).functionCall(data, "SafeERC20: low-level call failed");
        if (returndata.length > 0) {
            // Return data is optional
            // solhint-disable-next-line max-line-length
            require(abi.decode(returndata, (bool)), "SafeERC20: ERC20 operation did not succeed");
        }
    }
}

interface IUniswapV2Router {
    function factory() external pure returns (address);

    function WETH() external pure returns (address);

    function addLiquidity(
        address tokenA,
        address tokenB,
        uint256 amountADesired,
        uint256 amountBDesired,
        uint256 amountAMin,
        uint256 amountBMin,
        address to,
        uint256 deadline
    )
        external
        returns (
            uint256 amountA,
            uint256 amountB,
            uint256 liquidity
        );

    function addLiquidityETH(
        address token,
        uint256 amountTokenDesired,
        uint256 amountTokenMin,
        uint256 amountETHMin,
        address to,
        uint256 deadline
    )
        external
        payable
        returns (
            uint256 amountToken,
            uint256 amountETH,
            uint256 liquidity
        );

    function removeLiquidity(
        address tokenA,
        address tokenB,
        uint256 liquidity,
        uint256 amountAMin,
        uint256 amountBMin,
        address to,
        uint256 deadline
    ) external returns (uint256 amountA, uint256 amountB);

    function removeLiquidityETH(
        address token,
        uint256 liquidity,
        uint256 amountTokenMin,
        uint256 amountETHMin,
        address to,
        uint256 deadline
    ) external returns (uint256 amountToken, uint256 amountETH);

    function removeLiquidityWithPermit(
        address tokenA,
        address tokenB,
        uint256 liquidity,
        uint256 amountAMin,
        uint256 amountBMin,
        address to,
        uint256 deadline,
        bool approveMax,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external returns (uint256 amountA, uint256 amountB);

    function removeLiquidityETHWithPermit(
        address token,
        uint256 liquidity,
        uint256 amountTokenMin,
        uint256 amountETHMin,
        address to,
        uint256 deadline,
        bool approveMax,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external returns (uint256 amountToken, uint256 amountETH);

    function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external returns (uint256[] memory amounts);

    function swapTokensForExactTokens(
        uint256 amountOut,
        uint256 amountInMax,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external returns (uint256[] memory amounts);

    function swapExactETHForTokens(
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external payable returns (uint256[] memory amounts);

    function swapTokensForExactETH(
        uint256 amountOut,
        uint256 amountInMax,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external returns (uint256[] memory amounts);

    function swapExactTokensForETH(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external returns (uint256[] memory amounts);

    function swapETHForExactTokens(
        uint256 amountOut,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external payable returns (uint256[] memory amounts);

    function quote(
        uint256 amountA,
        uint256 reserveA,
        uint256 reserveB
    ) external pure returns (uint256 amountB);

    function getAmountOut(
        uint256 amountIn,
        uint256 reserveIn,
        uint256 reserveOut
    ) external pure returns (uint256 amountOut);

    function getAmountIn(
        uint256 amountOut,
        uint256 reserveIn,
        uint256 reserveOut
    ) external pure returns (uint256 amountIn);

    function getAmountsOut(uint256 amountIn, address[] calldata path) external view returns (uint256[] memory amounts);

    function getAmountsIn(uint256 amountOut, address[] calldata path) external view returns (uint256[] memory amounts);

    function removeLiquidityETHSupportingFeeOnTransferTokens(
        address token,
        uint256 liquidity,
        uint256 amountTokenMin,
        uint256 amountETHMin,
        address to,
        uint256 deadline
    ) external returns (uint256 amountETH);

    function removeLiquidityETHWithPermitSupportingFeeOnTransferTokens(
        address token,
        uint256 liquidity,
        uint256 amountTokenMin,
        uint256 amountETHMin,
        address to,
        uint256 deadline,
        bool approveMax,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external returns (uint256 amountETH);

    function swapExactTokensForTokensSupportingFeeOnTransferTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external;

    function swapExactETHForTokensSupportingFeeOnTransferTokens(
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external payable;

    function swapExactTokensForETHSupportingFeeOnTransferTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external;
}

interface IValueLiquidRouter {
    function swapExactTokensForTokens(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external returns (uint256[] memory amounts);

    function addLiquidity(
        address pair,
        address tokenA,
        address tokenB,
        uint256 amountADesired,
        uint256 amountBDesired,
        uint256 amountAMin,
        uint256 amountBMin,
        address to,
        uint256 deadline
    )
        external
        returns (
            uint256 amountA,
            uint256 amountB,
            uint256 liquidity
        );

    function removeLiquidity(
        address pair,
        address tokenA,
        address tokenB,
        uint256 liquidity,
        uint256 amountAMin,
        uint256 amountBMin,
        address to,
        uint256 deadline
    ) external returns (uint256 amountA, uint256 amountB);
}

interface IBPool is IERC20 {
    function version() external view returns (uint256);

    function swapExactAmountIn(
        address,
        uint256,
        address,
        uint256,
        uint256
    ) external returns (uint256, uint256);

    function swapExactAmountOut(
        address,
        uint256,
        address,
        uint256,
        uint256
    ) external returns (uint256, uint256);

    function calcInGivenOut(
        uint256,
        uint256,
        uint256,
        uint256,
        uint256,
        uint256
    ) external pure returns (uint256);

    function calcOutGivenIn(
        uint256,
        uint256,
        uint256,
        uint256,
        uint256,
        uint256
    ) external pure returns (uint256);

    function getDenormalizedWeight(address) external view returns (uint256);

    function swapFee() external view returns (uint256);

    function setSwapFee(uint256 _swapFee) external;

    function bind(
        address token,
        uint256 balance,
        uint256 denorm
    ) external;

    function rebind(
        address token,
        uint256 balance,
        uint256 denorm
    ) external;

    function finalize(
        uint256 _swapFee,
        uint256 _initPoolSupply,
        address[] calldata _bindTokens,
        uint256[] calldata _bindDenorms
    ) external;

    function setPublicSwap(bool _publicSwap) external;

    function setController(address _controller) external;

    function setExchangeProxy(address _exchangeProxy) external;

    function getFinalTokens() external view returns (address[] memory tokens);

    function getTotalDenormalizedWeight() external view returns (uint256);

    function getBalance(address token) external view returns (uint256);

    function joinPool(uint256 poolAmountOut, uint256[] calldata maxAmountsIn) external;

    function joinPoolFor(
        address account,
        uint256 rewardAmountOut,
        uint256[] calldata maxAmountsIn
    ) external;

    function joinswapPoolAmountOut(
        address tokenIn,
        uint256 poolAmountOut,
        uint256 maxAmountIn
    ) external returns (uint256 tokenAmountIn);

    function exitPool(uint256 poolAmountIn, uint256[] calldata minAmountsOut) external;

    function exitswapPoolAmountIn(
        address tokenOut,
        uint256 poolAmountIn,
        uint256 minAmountOut
    ) external returns (uint256 tokenAmountOut);

    function exitswapExternAmountOut(
        address tokenOut,
        uint256 tokenAmountOut,
        uint256 maxPoolAmountIn
    ) external returns (uint256 poolAmountIn);

    function joinswapExternAmountIn(
        address tokenIn,
        uint256 tokenAmountIn,
        uint256 minPoolAmountOut
    ) external returns (uint256 poolAmountOut);

    function finalizeRewardFundInfo(address _rewardFund, uint256 _unstakingFrozenTime) external;

    function addRewardPool(
        IERC20 _rewardToken,
        uint256 _startBlock,
        uint256 _endRewardBlock,
        uint256 _rewardPerBlock,
        uint256 _lockRewardPercent,
        uint256 _startVestingBlock,
        uint256 _endVestingBlock
    ) external;

    function isBound(address t) external view returns (bool);

    function getSpotPrice(address tokenIn, address tokenOut) external view returns (uint256 spotPrice);
}

interface IBoardroom {
    function balanceOf(address _director) external view returns (uint256);

    function earned(address _director) external view returns (uint256);

    function canWithdraw(address _director) external view returns (bool);

    function canClaimReward(address _director) external view returns (bool);

    function epoch() external view returns (uint256);

    function nextEpochPoint() external view returns (uint256);

    function getDollarPrice() external view returns (uint256);

    function setOperator(address _operator) external;

    function setLockUp(uint256 _withdrawLockupEpochs, uint256 _rewardLockupEpochs) external;

    function stake(uint256 _amount) external;

    function withdraw(uint256 _amount) external;

    function exit() external;

    function claimReward() external;

    function allocateSeigniorage(uint256 _amount) external;

    function governanceRecoverUnsupported(
        address _token,
        uint256 _amount,
        address _to
    ) external;
}

interface IShare {
    function unclaimedTreasuryFund() external view returns (uint256 _pending);

    function claimRewards() external;
}

interface ITreasury {
    function epoch() external view returns (uint256);

    function nextEpochPoint() external view returns (uint256);

    function getDollarPrice() external view returns (uint256);

    function buyBonds(uint256 amount, uint256 targetPrice) external;

    function redeemBonds(uint256 amount, uint256 targetPrice) external;
}

interface IOracle {
    function update() external;

    function consult(address _token, uint256 _amountIn) external view returns (uint144 amountOut);

    function twap(address _token, uint256 _amountIn) external view returns (uint144 _amountOut);
}

interface IShareRewardPool {
    function deposit(uint256 _pid, uint256 _amount) external;

    function withdraw(uint256 _pid, uint256 _amount) external;

    function pendingShare(uint256 _pid, address _user) external view returns (uint256);

    function userInfo(uint256 _pid, address _user) external view returns (uint256 amount, uint256 rewardDebt);
}

interface IPancakeswapPool {
    function deposit(uint256 _pid, uint256 _amount) external;

    function withdraw(uint256 _pid, uint256 _amount) external;

    function pendingCake(uint256 _pid, address _user) external view returns (uint256);

    function pendingReward(uint256 _pid, address _user) external view returns (uint256);

    function userInfo(uint256 _pid, address _user) external view returns (uint256 amount, uint256 rewardDebt);
}

/**
 * @dev This contract will collect vesting Shares, stake to the Boardroom and rebalance BDO, BUSD, WBNB according to DAO.
 */
contract CommunityFund {
    using SafeERC20 for IERC20;
    using SafeMath for uint256;

    /* ========== STATE VARIABLES ========== */

    // governance
    address public operator;

    // flags
    bool public initialized = false;
    bool public publicAllowed; // set to true to allow public to call rebalance()

    // price
    uint256 public dollarPriceToSell; // to rebalance when expansion
    uint256 public dollarPriceToBuy; // to rebalance when contraction

    address public dollar = address(0x190b589cf9Fb8DDEabBFeae36a813FFb2A702454);
    address public bond = address(0x9586b02B09bd68A7cD4aa9167a61B78F43092063);
    address public share = address(0x0d9319565be7f53CeFE84Ad201Be3f40feAE2740);

    address public busd = address(0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56);
    address public wbnb = address(0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c);

    address public boardroom = address(0x9D39cd20901c88030032073Fb014AaF79D84d2C5);

    // Pancakeswap
    IUniswapV2Router public pancakeRouter = IUniswapV2Router(0x05fF2B0DB69458A0750badebc4f9e13aDd608C7F);
    mapping(address => mapping(address => address[])) public uniswapPaths;

    // DAO parameters - https://docs.basisdollar.fi/DAO
    uint256[] public expansionPercent;
    uint256[] public contractionPercent;

    /* =================== Added variables (need to keep orders for proxy to work) =================== */
    address public strategist;
    address public dollarOracle = address(0xfAB911c54f7CF3ffFdE0482d2267a751D87B5B20);
    address public treasury = address(0x15A90e6157a870CD335AF03c6df776d0B1ebf94F);

    mapping(address => uint256) public maxAmountToTrade; // BDO, BUSD, WBNB

    address public shareRewardPool = address(0x948dB1713D4392EC04C86189070557C5A8566766);
    mapping(address => uint256) public shareRewardPoolId; // [BUSD, WBNB] -> [Pool_id]: 0, 2
    mapping(address => address) public lpPairAddress; // [BUSD, WBNB] -> [LP]: 0xc5b0d73A7c0E4eaF66baBf7eE16A2096447f7aD6, 0x74690f829fec83ea424ee1F1654041b2491A7bE9

    address public pancakeFarmingPool = address(0x73feaa1eE314F8c655E354234017bE2193C9E24E);
    uint256 public pancakeFarmingPoolId = 66;
    address public pancakeFarmingPoolLpPairAddress = address(0x74690f829fec83ea424ee1F1654041b2491A7bE9); // BDO/WBNB
    address public cake = address(0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82); // CAKE (pancakePool farming token)

    address public kebabFarmingPool = address(0x76FCeffFcf5325c6156cA89639b17464ea833ECd);
    uint256 public kebabFarmingPoolId = 2;
    address public kebabFarmingPoolLpPairAddress = address(0x1B96B92314C44b159149f7E0303511fB2Fc4774f); // BUSD/WBNB
    address public kebab = address(0x7979F6C54ebA05E18Ded44C4F986F49a5De551c2); // KEBAB (kebabPool farming token)

    IValueLiquidRouter public vswapRouter = IValueLiquidRouter(0xb7e19a1188776f32E8C2B790D9ca578F2896Da7C); // vSwapRouter
    address public vswapFarmingPool = address(0xd56339F80586c08B7a4E3a68678d16D37237Bd96);
    uint256 public vswapFarmingPoolId = 1;
    address public vswapFarmingPoolLpPairAddress = address(0x522361C3aa0d81D1726Fa7d40aA14505d0e097C9); // BUSD/WBNB
    address public vbswap = address(0x4f0ed527e8A95ecAA132Af214dFd41F30b361600); // vBSWAP (vSwap farming token)
    address public vbswapToWbnbPair = address(0x8DD39f0a49160cDa5ef1E2a2fA7396EEc7DA8267); // vBSWAP/WBNB 50-50

    /* ========== EVENTS ========== */

    event Initialized(address indexed executor, uint256 at);
    event SwapToken(address inputToken, address outputToken, uint256 amount);
    event BoughtBonds(uint256 amount);
    event RedeemedBonds(uint256 amount);
    event ExecuteTransaction(address indexed target, uint256 value, string signature, bytes data);

    /* ========== Modifiers =============== */

    modifier onlyOperator() {
        require(operator == msg.sender, "!operator");
        _;
    }

    modifier onlyStrategist() {
        require(strategist == msg.sender || operator == msg.sender, "!strategist");
        _;
    }

    modifier notInitialized() {
        require(!initialized, "initialized");
        _;
    }

    modifier checkPublicAllow() {
        require(publicAllowed || msg.sender == operator, "!operator nor !publicAllowed");
        _;
    }

    /* ========== GOVERNANCE ========== */

    function initialize(
        address _dollar,
        address _bond,
        address _share,
        address _busd,
        address _wbnb,
        address _boardroom,
        IUniswapV2Router _pancakeRouter
    ) public notInitialized {
        dollar = _dollar;
        bond = _bond;
        share = _share;
        busd = _busd;
        wbnb = _wbnb;
        boardroom = _boardroom;
        pancakeRouter = _pancakeRouter;
        dollarPriceToSell = 1500 finney; // $1.5
        dollarPriceToBuy = 800 finney; // $0.8
        expansionPercent = [3000, 6800, 200]; // dollar (30%), BUSD (68%), WBNB (2%) during expansion period
        contractionPercent = [8800, 1160, 40]; // dollar (88%), BUSD (11.6%), WBNB (0.4%) during contraction period
        publicAllowed = true;
        initialized = true;
        operator = msg.sender;
        emit Initialized(msg.sender, block.number);
    }

    function setOperator(address _operator) external onlyOperator {
        operator = _operator;
    }

    function setStrategist(address _strategist) external onlyOperator {
        strategist = _strategist;
    }

    function setTreasury(address _treasury) external onlyOperator {
        treasury = _treasury;
    }

    function setShareRewardPool(address _shareRewardPool) external onlyOperator {
        shareRewardPool = _shareRewardPool;
    }

    function setShareRewardPoolId(address _tokenB, uint256 _pid) external onlyStrategist {
        shareRewardPoolId[_tokenB] = _pid;
    }

    function setLpPairAddress(address _tokenB, address _lpAdd) external onlyStrategist {
        lpPairAddress[_tokenB] = _lpAdd;
    }

    function setVswapFarmingPool(
        IValueLiquidRouter _vswapRouter,
        address _vswapFarmingPool,
        uint256 _vswapFarmingPoolId,
        address _vswapFarmingPoolLpPairAddress,
        address _vbswap,
        address _vbswapToWbnbPair
    ) external onlyOperator {
        vswapRouter = _vswapRouter;
        vswapFarmingPool = _vswapFarmingPool;
        vswapFarmingPoolId = _vswapFarmingPoolId;
        vswapFarmingPoolLpPairAddress = _vswapFarmingPoolLpPairAddress;
        vbswap = _vbswap;
        vbswapToWbnbPair = _vbswapToWbnbPair;
    }

    function setDollarOracle(address _dollarOracle) external onlyOperator {
        dollarOracle = _dollarOracle;
    }

    function setPublicAllowed(bool _publicAllowed) external onlyStrategist {
        publicAllowed = _publicAllowed;
    }

    function setExpansionPercent(
        uint256 _dollarPercent,
        uint256 _busdPercent,
        uint256 _wbnbPercent
    ) external onlyStrategist {
        require(_dollarPercent.add(_busdPercent).add(_wbnbPercent) == 10000, "!100%");
        expansionPercent[0] = _dollarPercent;
        expansionPercent[1] = _busdPercent;
        expansionPercent[2] = _wbnbPercent;
    }

    function setContractionPercent(
        uint256 _dollarPercent,
        uint256 _busdPercent,
        uint256 _wbnbPercent
    ) external onlyStrategist {
        require(_dollarPercent.add(_busdPercent).add(_wbnbPercent) == 10000, "!100%");
        contractionPercent[0] = _dollarPercent;
        contractionPercent[1] = _busdPercent;
        contractionPercent[2] = _wbnbPercent;
    }

    function setMaxAmountToTrade(
        uint256 _dollarAmount,
        uint256 _busdAmount,
        uint256 _wbnbAmount
    ) external onlyStrategist {
        maxAmountToTrade[dollar] = _dollarAmount;
        maxAmountToTrade[busd] = _busdAmount;
        maxAmountToTrade[wbnb] = _wbnbAmount;
    }

    function setDollarPriceToSell(uint256 _dollarPriceToSell) external onlyStrategist {
        require(_dollarPriceToSell >= 950 finney && _dollarPriceToSell <= 2000 finney, "out of range"); // [$0.95, $2.00]
        dollarPriceToSell = _dollarPriceToSell;
    }

    function setDollarPriceToBuy(uint256 _dollarPriceToBuy) external onlyStrategist {
        require(_dollarPriceToBuy >= 500 finney && _dollarPriceToBuy <= 1050 finney, "out of range"); // [$0.50, $1.05]
        dollarPriceToBuy = _dollarPriceToBuy;
    }

    function setUnirouterPath(
        address _input,
        address _output,
        address[] memory _path
    ) external onlyStrategist {
        uniswapPaths[_input][_output] = _path;
    }

    function withdrawShare(uint256 _amount) external onlyStrategist {
        IBoardroom(boardroom).withdraw(_amount);
    }

    function exitBoardroom() external onlyStrategist {
        IBoardroom(boardroom).exit();
    }

    function grandFund(
        address _token,
        uint256 _amount,
        address _to
    ) external onlyOperator {
        IERC20(_token).transfer(_to, _amount);
    }

    /* ========== VIEW FUNCTIONS ========== */

    function earned() public view returns (uint256) {
        return IBoardroom(boardroom).earned(address(this));
    }

    function tokenBalances()
        public
        view
        returns (
            uint256 _dollarBal,
            uint256 _busdBal,
            uint256 _wbnbBal,
            uint256 _totalBal
        )
    {
        _dollarBal = IERC20(dollar).balanceOf(address(this));
        _busdBal = IERC20(busd).balanceOf(address(this));
        _wbnbBal = IERC20(wbnb).balanceOf(address(this));
        _totalBal = _dollarBal.add(_busdBal).add(_wbnbBal);
    }

    function tokenPercents()
        public
        view
        returns (
            uint256 _dollarPercent,
            uint256 _busdPercent,
            uint256 _wbnbPercent
        )
    {
        (uint256 _dollarBal, uint256 _busdBal, uint256 _wbnbBal, uint256 _totalBal) = tokenBalances();
        if (_totalBal > 0) {
            _dollarPercent = _dollarBal.mul(10000).div(_totalBal);
            _busdPercent = _busdBal.mul(10000).div(_totalBal);
            _wbnbPercent = _wbnbBal.mul(10000).div(_totalBal);
        }
    }

    function getDollarPrice() public view returns (uint256 dollarPrice) {
        try IOracle(dollarOracle).consult(dollar, 1e18) returns (uint144 price) {
            return uint256(price);
        } catch {
            revert("failed to consult price");
        }
    }

    function getDollarUpdatedPrice() public view returns (uint256 _dollarPrice) {
        try IOracle(dollarOracle).twap(dollar, 1e18) returns (uint144 price) {
            return uint256(price);
        } catch {
            revert("failed to consult price");
        }
    }

    /* ========== MUTATIVE FUNCTIONS ========== */

    function collectShareRewards() public checkPublicAllow {
        if (IShare(share).unclaimedTreasuryFund() > 0) {
            IShare(share).claimRewards();
        }
    }

    function claimAndRestake() public checkPublicAllow {
        if (IBoardroom(boardroom).canClaimReward(address(this))) {
            // only restake more if at this epoch we could claim pending dollar rewards
            if (earned() > 0) {
                IBoardroom(boardroom).claimReward();
            }
            uint256 _shareBal = IERC20(share).balanceOf(address(this));
            if (_shareBal > 0) {
                IERC20(share).safeIncreaseAllowance(boardroom, _shareBal);
                IBoardroom(boardroom).stake(_shareBal);
            }
        }
    }

    function rebalance() public checkPublicAllow {
        (uint256 _dollarBal, uint256 _busdBal, uint256 _wbnbBal, uint256 _totalBal) = tokenBalances();
        if (_totalBal > 0) {
            uint256 _dollarPercent = _dollarBal.mul(10000).div(_totalBal);
            uint256 _busdPercent = _busdBal.mul(10000).div(_totalBal);
            uint256 _wbnbPercent = _wbnbBal.mul(10000).div(_totalBal);
            uint256 _dollarPrice = getDollarUpdatedPrice();
            if (_dollarPrice >= dollarPriceToSell) {
                // expansion: sell BDO
                if (_dollarPercent > expansionPercent[0]) {
                    uint256 _sellingBdo = _dollarBal.mul(_dollarPercent.sub(expansionPercent[0])).div(10000);
                    if (_busdPercent >= expansionPercent[1]) {
                        // enough BUSD
                        if (_wbnbPercent < expansionPercent[2]) {
                            // short of WBNB: buy WBNB
                            _swapToken(dollar, wbnb, _sellingBdo);
                        } else {
                            if (_busdPercent.sub(expansionPercent[1]) <= _wbnbPercent.sub(expansionPercent[2])) {
                                // has more WBNB than BUSD: buy BUSD
                                _swapToken(dollar, busd, _sellingBdo);
                            } else {
                                // has more BUSD than WBNB: buy WBNB
                                _swapToken(dollar, wbnb, _sellingBdo);
                            }
                        }
                    } else {
                        // short of BUSD
                        if (_wbnbPercent >= expansionPercent[2]) {
                            // enough WBNB: buy BUSD
                            _swapToken(dollar, busd, _sellingBdo);
                        } else {
                            // short of WBNB
                            uint256 _sellingBdoToBusd = _sellingBdo.mul(80).div(100); // 80% to BUSD
                            _swapToken(dollar, busd, _sellingBdoToBusd);
                            _swapToken(dollar, wbnb, _sellingBdo.sub(_sellingBdoToBusd));
                        }
                    }
                }
            } else if (_dollarPrice <= dollarPriceToBuy && (msg.sender == operator || msg.sender == strategist)) {
                // contraction: buy BDO
                if (_busdPercent >= contractionPercent[1]) {
                    // enough BUSD
                    if (_wbnbPercent <= contractionPercent[2]) {
                        // short of WBNB: sell BUSD
                        uint256 _sellingBUSD = _busdBal.mul(_busdPercent.sub(contractionPercent[1])).div(10000);
                        _swapToken(busd, dollar, _sellingBUSD);
                    } else {
                        if (_busdPercent.sub(contractionPercent[1]) > _wbnbPercent.sub(contractionPercent[2])) {
                            // has more BUSD than WBNB: sell BUSD
                            uint256 _sellingBUSD = _busdBal.mul(_busdPercent.sub(contractionPercent[1])).div(10000);
                            _swapToken(busd, dollar, _sellingBUSD);
                        } else {
                            // has more WBNB than BUSD: sell WBNB
                            uint256 _sellingWBNB = _wbnbBal.mul(_wbnbPercent.sub(contractionPercent[2])).div(10000);
                            _swapToken(wbnb, dollar, _sellingWBNB);
                        }
                    }
                } else {
                    // short of BUSD
                    if (_wbnbPercent > contractionPercent[2]) {
                        // enough WBNB: sell WBNB
                        uint256 _sellingWBNB = _wbnbBal.mul(_wbnbPercent.sub(contractionPercent[2])).div(10000);
                        _swapToken(wbnb, dollar, _sellingWBNB);
                    }
                }
            }
        }
    }

    function workForDaoFund() external checkPublicAllow {
        collectShareRewards();
        claimAllRewardFromSharePool();
        claimAndRestake();
        rebalance();
    }

    function buyBonds(uint256 _dollarAmount) external onlyStrategist {
        uint256 _dollarPrice = ITreasury(treasury).getDollarPrice();
        ITreasury(treasury).buyBonds(_dollarAmount, _dollarPrice);
        emit BoughtBonds(_dollarAmount);
    }

    function redeemBonds(uint256 _bondAmount) external onlyStrategist {
        uint256 _dollarPrice = ITreasury(treasury).getDollarPrice();
        ITreasury(treasury).redeemBonds(_bondAmount, _dollarPrice);
        emit RedeemedBonds(_bondAmount);
    }

    function forceSell(address _buyingToken, uint256 _dollarAmount) external onlyStrategist {
        require(getDollarUpdatedPrice() >= dollarPriceToBuy, "price is too low to sell");
        _swapToken(dollar, _buyingToken, _dollarAmount);
    }

    function forceBuy(address _sellingToken, uint256 _sellingAmount) external onlyStrategist {
        require(getDollarUpdatedPrice() <= dollarPriceToSell, "price is too high to buy");
        _swapToken(_sellingToken, dollar, _sellingAmount);
    }

    function trimNonCoreToken(address _sellingToken) public onlyStrategist {
        require(_sellingToken != dollar && _sellingToken != bond && _sellingToken != share && _sellingToken != busd && _sellingToken != wbnb, "core");
        uint256 _bal = IERC20(_sellingToken).balanceOf(address(this));
        if (_sellingToken != vbswap && _bal > 0) {
            _swapToken(_sellingToken, dollar, _bal);
        }
    }

    function _swapToken(
        address _inputToken,
        address _outputToken,
        uint256 _amount
    ) internal {
        if (_amount == 0) return;
        uint256 _maxAmount = maxAmountToTrade[_inputToken];
        if (_maxAmount > 0 && _maxAmount < _amount) {
            _amount = _maxAmount;
        }
        address[] memory _path = uniswapPaths[_inputToken][_outputToken];
        if (_path.length == 0) {
            _path = new address[](2);
            _path[0] = _inputToken;
            _path[1] = _outputToken;
        }
        IERC20(_inputToken).safeIncreaseAllowance(address(pancakeRouter), _amount);
        pancakeRouter.swapExactTokensForTokens(_amount, 1, _path, address(this), now.add(1800));
    }

    function _addLiquidity(address _tokenB, uint256 _amountADesired) internal {
        // tokenA is always BDO
        _addLiquidity2(dollar, _tokenB, _amountADesired, IERC20(_tokenB).balanceOf(address(this)));
    }

    function _removeLiquidity(
        address _lpAdd,
        address _tokenB,
        uint256 _liquidity
    ) internal {
        // tokenA is always BDO
        _removeLiquidity2(_lpAdd, dollar, _tokenB, _liquidity);
    }

    function _addLiquidity2(
        address _tokenA,
        address _tokenB,
        uint256 _amountADesired,
        uint256 _amountBDesired
    ) internal {
        IERC20(_tokenA).safeIncreaseAllowance(address(pancakeRouter), _amountADesired);
        IERC20(_tokenB).safeIncreaseAllowance(address(pancakeRouter), _amountBDesired);
        // addLiquidity(tokenA, tokenB, amountADesired, amountBDesired, amountAMin, amountBMin, to, deadline)
        pancakeRouter.addLiquidity(_tokenA, _tokenB, _amountADesired, _amountBDesired, 0, 0, address(this), now.add(1800));
    }

    function _removeLiquidity2(
        address _lpAdd,
        address _tokenA,
        address _tokenB,
        uint256 _liquidity
    ) internal {
        IERC20(_lpAdd).safeIncreaseAllowance(address(pancakeRouter), _liquidity);
        // removeLiquidity(tokenA, tokenB, liquidity, amountAMin, amountBMin, to, deadline)
        pancakeRouter.removeLiquidity(_tokenA, _tokenB, _liquidity, 1, 1, address(this), now.add(1800));
    }

    /* ========== PROVIDE LP AND STAKE TO SHARE POOL ========== */

    function depositToSharePool(address _tokenB, uint256 _dollarAmount) external onlyStrategist {
        address _lpAdd = lpPairAddress[_tokenB];
        uint256 _before = IERC20(_lpAdd).balanceOf(address(this));
        _addLiquidity(_tokenB, _dollarAmount);
        uint256 _after = IERC20(_lpAdd).balanceOf(address(this));
        uint256 _lpBal = _after.sub(_before);
        require(_lpBal > 0, "!_lpBal");
        address _shareRewardPool = shareRewardPool;
        uint256 _pid = shareRewardPoolId[_tokenB];
        IERC20(_lpAdd).safeIncreaseAllowance(_shareRewardPool, _lpBal);
        IShareRewardPool(_shareRewardPool).deposit(_pid, _lpBal);
    }

    function withdrawFromSharePool(address _tokenB, uint256 _lpAmount) public onlyStrategist {
        address _lpAdd = lpPairAddress[_tokenB];
        address _shareRewardPool = shareRewardPool;
        uint256 _pid = shareRewardPoolId[_tokenB];
        IShareRewardPool(_shareRewardPool).withdraw(_pid, _lpAmount);
        _removeLiquidity(_lpAdd, _tokenB, _lpAmount);
    }

    function exitSharePool(address _tokenB) public onlyStrategist {
        (uint256 _stakedAmount, ) = IShareRewardPool(shareRewardPool).userInfo(shareRewardPoolId[_tokenB], address(this));
        withdrawFromSharePool(_tokenB, _stakedAmount);
    }

    function exitAllSharePool() external {
        if (stakeAmountFromSharePool(busd) > 0) exitSharePool(busd);
        if (stakeAmountFromSharePool(wbnb) > 0) exitSharePool(wbnb);
    }

    function claimRewardFromSharePool(address _tokenB) public {
        uint256 _pid = shareRewardPoolId[_tokenB];
        IShareRewardPool(shareRewardPool).withdraw(_pid, 0);
    }

    function claimAllRewardFromSharePool() public {
        if (pendingFromSharePool(busd) > 0) claimRewardFromSharePool(busd);
        if (pendingFromSharePool(wbnb) > 0) claimRewardFromSharePool(wbnb);
    }

    function pendingFromSharePool(address _tokenB) public view returns (uint256) {
        return IShareRewardPool(shareRewardPool).pendingShare(shareRewardPoolId[_tokenB], address(this));
    }

    function pendingAllFromSharePool() public view returns (uint256) {
        return pendingFromSharePool(busd).add(pendingFromSharePool(wbnb));
    }

    function stakeAmountFromSharePool(address _tokenB) public view returns (uint256 _stakedAmount) {
        (_stakedAmount, ) = IShareRewardPool(shareRewardPool).userInfo(shareRewardPoolId[_tokenB], address(this));
    }

    function stakeAmountAllFromSharePool() public view returns (uint256 _bnbPoolStakedAmount, uint256 _wbnbPoolStakedAmount) {
        _bnbPoolStakedAmount = stakeAmountFromSharePool(busd);
        _wbnbPoolStakedAmount = stakeAmountFromSharePool(wbnb);
    }

    /* ========== FARM PANCAKESWAP POOL: STAKE BDO/BUSD EARN CAKE ========== */

    function depositToPancakePool(uint256 _dollarAmount) external onlyStrategist {
        address _lpAdd = pancakeFarmingPoolLpPairAddress;
        uint256 _before = IERC20(_lpAdd).balanceOf(address(this));
        _addLiquidity(wbnb, _dollarAmount);
        uint256 _after = IERC20(_lpAdd).balanceOf(address(this));
        uint256 _lpBal = _after.sub(_before);
        require(_lpBal > 0, "!_lpBal");
        address _pancakeFarmingPool = pancakeFarmingPool;
        IERC20(_lpAdd).safeIncreaseAllowance(_pancakeFarmingPool, _lpBal);
        IPancakeswapPool(_pancakeFarmingPool).deposit(pancakeFarmingPoolId, _lpBal);
    }

    function withdrawFromPancakePool(uint256 _lpAmount) public onlyStrategist {
        IPancakeswapPool(pancakeFarmingPool).withdraw(pancakeFarmingPoolId, _lpAmount);
        _removeLiquidity(pancakeFarmingPoolLpPairAddress, wbnb, _lpAmount);
    }

    function exitPancakePool() public onlyStrategist {
        (uint256 _stakedAmount, ) = IPancakeswapPool(pancakeFarmingPool).userInfo(pancakeFarmingPoolId, address(this));
        withdrawFromPancakePool(_stakedAmount);
        uint256 _bal = IERC20(cake).balanceOf(address(this));
        if (_bal > 0) {
            trimNonCoreToken(cake);
        }
    }

    function claimAndReinvestFromPancakePool() public {
        IPancakeswapPool(pancakeFarmingPool).withdraw(pancakeFarmingPoolId, 0);
        uint256 _cakeBal = IERC20(cake).balanceOf(address(this));
        if (_cakeBal > 0) {
            uint256 _wbnbBef = IERC20(wbnb).balanceOf(address(this));
            _swapToken(cake, wbnb, _cakeBal);
            uint256 _wbnbAft = IERC20(wbnb).balanceOf(address(this));
            uint256 _boughtWbnb = _wbnbAft.sub(_wbnbBef);
            if (_boughtWbnb >= 2) {
                uint256 _dollarBef = IERC20(dollar).balanceOf(address(this));
                _swapToken(wbnb, dollar, _boughtWbnb.div(2));
                uint256 _dollarAft = IERC20(dollar).balanceOf(address(this));
                uint256 _boughtDollar = _dollarAft.sub(_dollarBef);
                _addLiquidity(wbnb, _boughtDollar);
            }
        }
        address _lpAdd = pancakeFarmingPoolLpPairAddress;
        uint256 _lpBal = IERC20(_lpAdd).balanceOf(address(this));
        if (_lpBal > 0) {
            address _pancakeFarmingPool = pancakeFarmingPool;
            IERC20(_lpAdd).safeIncreaseAllowance(_pancakeFarmingPool, _lpBal);
            IPancakeswapPool(_pancakeFarmingPool).deposit(pancakeFarmingPoolId, _lpBal);
        }
    }

    function pendingFromPancakePool() public view returns (uint256) {
        return IPancakeswapPool(pancakeFarmingPool).pendingCake(pancakeFarmingPoolId, address(this));
    }

    function stakeAmountFromPancakePool() public view returns (uint256 _stakedAmount) {
        (_stakedAmount, ) = IPancakeswapPool(pancakeFarmingPool).userInfo(pancakeFarmingPoolId, address(this));
    }

    /* ========== FARM VSWAP POOL: STAKE BUSD/WBNB EARN VBSWAP ========== */

    function depositToVswapPool(uint256 _busdAmount, uint256 _wbnbAmount) external onlyStrategist {
        address _lpAdd = vswapFarmingPoolLpPairAddress;
        _vswapAddLiquidity(_lpAdd, busd, wbnb, _busdAmount, _wbnbAmount);
        uint256 _lpBal = IERC20(_lpAdd).balanceOf(address(this));
        require(_lpBal > 0, "!_lpBal");
        address _vswapFarmingPool = vswapFarmingPool;
        IERC20(_lpAdd).safeIncreaseAllowance(_vswapFarmingPool, _lpBal);
        IPancakeswapPool(_vswapFarmingPool).deposit(vswapFarmingPoolId, _lpBal);
    }

    function withdrawFromVswapPool(uint256 _lpAmount) public onlyStrategist {
        IPancakeswapPool(vswapFarmingPool).withdraw(vswapFarmingPoolId, _lpAmount);
        _vswapRemoveLiquidity(vswapFarmingPoolLpPairAddress, busd, wbnb, _lpAmount);
    }

    function exitVswapPool() public onlyStrategist {
        (uint256 _stakedAmount, ) = IPancakeswapPool(vswapFarmingPool).userInfo(vswapFarmingPoolId, address(this));
        withdrawFromVswapPool(_stakedAmount);
    }

    function claimAndBuyBackBDOFromVswapPool() public {
        IPancakeswapPool(vswapFarmingPool).withdraw(vswapFarmingPoolId, 0);
        uint256 _vbswapBal = IERC20(vbswap).balanceOf(address(this));
        if (_vbswapBal > 0) {
            uint256 _wbnbBef = IERC20(wbnb).balanceOf(address(this));
            _vswapSwapToken(vbswapToWbnbPair, vbswap, wbnb, _vbswapBal);
            uint256 _wbnbAft = IERC20(wbnb).balanceOf(address(this));
            uint256 _boughtWbnb = _wbnbAft.sub(_wbnbBef);
            if (_boughtWbnb >= 2) {
                _swapToken(wbnb, dollar, _boughtWbnb);
            }
        }
    }

    function pendingFromVswapPool() public view returns (uint256) {
        return IPancakeswapPool(vswapFarmingPool).pendingReward(vswapFarmingPoolId, address(this));
    }

    function stakeAmountFromVswapPool() public view returns (uint256 _stakedAmount) {
        (_stakedAmount, ) = IPancakeswapPool(vswapFarmingPool).userInfo(vswapFarmingPoolId, address(this));
    }

    function _vswapSwapToken(
        address _pair,
        address _inputToken,
        address _outputToken,
        uint256 _amount
    ) internal {
        IERC20(_inputToken).safeIncreaseAllowance(address(vswapRouter), _amount);
        address[] memory _paths = new address[](1);
        _paths[0] = _pair;
        vswapRouter.swapExactTokensForTokens(_inputToken, _outputToken, _amount, 1, _paths, address(this), now.add(1800));
    }

    function _vswapAddLiquidity(
        address _pair,
        address _tokenA,
        address _tokenB,
        uint256 _amountADesired,
        uint256 _amountBDesired
    ) internal {
        IERC20(_tokenA).safeIncreaseAllowance(address(vswapRouter), _amountADesired);
        IERC20(_tokenB).safeIncreaseAllowance(address(vswapRouter), _amountBDesired);
        vswapRouter.addLiquidity(_pair, _tokenA, _tokenB, _amountADesired, _amountBDesired, 0, 0, address(this), now.add(1800));
    }

    function _vswapRemoveLiquidity(
        address _pair,
        address _tokenA,
        address _tokenB,
        uint256 _liquidity
    ) internal {
        IERC20(_pair).safeIncreaseAllowance(address(vswapRouter), _liquidity);
        vswapRouter.removeLiquidity(_pair, _tokenA, _tokenB, _liquidity, 1, 1, address(this), now.add(1800));
    }

    /* ========== EMERGENCY ========== */

    function executeTransaction(
        address target,
        uint256 value,
        string memory signature,
        bytes memory data
    ) public onlyOperator returns (bytes memory) {
        bytes memory callData;

        if (bytes(signature).length == 0) {
            callData = data;
        } else {
            callData = abi.encodePacked(bytes4(keccak256(bytes(signature))), data);
        }

        // solium-disable-next-line security/no-call-value
        (bool success, bytes memory returnData) = target.call{value: value}(callData);
        require(success, string("CommunityFund::executeTransaction: Transaction execution reverted."));

        emit ExecuteTransaction(target, value, signature, data);

        return returnData;
    }

    receive() external payable {}
}