
/** 
 *  SourceUnit: /Users/yuexue/Downloads/Bunny-main 2/contracts/dashboard/calculator/PriceCalculatorBSC.sol
*/
            
////// SPDX-License-Identifier-FLATTEN-SUPPRESS-WARNING: MIT

// solhint-disable-next-line compiler-version
pragma solidity >=0.4.24 <0.8.0;


/**
 * @dev This is a base contract to aid in writing upgradeable contracts, or any kind of contract that will be deployed
 * behind a proxy. Since a proxied contract can't have a constructor, it's common to move constructor logic to an
 * external initializer function, usually called `initialize`. It then becomes necessary to protect this initializer
 * function so it can only be called once. The {initializer} modifier provided by this contract will have this effect.
 * 
 * TIP: To avoid leaving the proxy in an uninitialized state, the initializer function should be called as early as
 * possible by providing the encoded function call as the `_data` argument to {UpgradeableProxy-constructor}.
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
        require(_initializing || _isConstructor() || !_initialized, "Initializable: contract is already initialized");

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

    /// @dev Returns true if and only if the function is running in the constructor
    function _isConstructor() private view returns (bool) {
        // extcodesize checks the size of the code stored in an address, and
        // address returns the current address. Since the code is still not
        // deployed when running a constructor, any checks on its code size will
        // yield zero, making it an effective way to detect if a contract is
        // under construction or not.
        address self = address(this);
        uint256 cs;
        // solhint-disable-next-line no-inline-assembly
        assembly { cs := extcodesize(self) }
        return cs == 0;
    }
}




/** 
 *  SourceUnit: /Users/yuexue/Downloads/Bunny-main 2/contracts/dashboard/calculator/PriceCalculatorBSC.sol
*/
            
////// SPDX-License-Identifier-FLATTEN-SUPPRESS-WARNING: MIT

pragma solidity >=0.6.0 <0.8.0;
////import "../proxy/Initializable.sol";

/*
 * @dev Provides information about the current execution context, including the
 * sender of the transaction and its data. While these are generally available
 * via msg.sender and msg.data, they should not be accessed in such a direct
 * manner, since when dealing with GSN meta-transactions the account sending and
 * paying for execution may not be the actual sender (as far as an application
 * is concerned).
 *
 * This contract is only required for intermediate, library-like contracts.
 */
abstract contract ContextUpgradeable is Initializable {
    function __Context_init() internal initializer {
        __Context_init_unchained();
    }

    function __Context_init_unchained() internal initializer {
    }
    function _msgSender() internal view virtual returns (address payable) {
        return msg.sender;
    }

    function _msgData() internal view virtual returns (bytes memory) {
        this; // silence state mutability warning without generating bytecode - see https://github.com/ethereum/solidity/issues/2691
        return msg.data;
    }
    uint256[50] private __gap;
}


// SPDX-License-Identifier: MIT

pragma solidity >=0.6.0 <0.8.0;

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
    function sub(uint256 a, uint256 b, string memory errorMessage) internal pure returns (uint256) {
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
    function div(uint256 a, uint256 b, string memory errorMessage) internal pure returns (uint256) {
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
    function mod(uint256 a, uint256 b, string memory errorMessage) internal pure returns (uint256) {
        require(b != 0, errorMessage);
        return a % b;
    }
}

/** 
 *  SourceUnit: /Users/yuexue/Downloads/Bunny-main 2/contracts/dashboard/calculator/PriceCalculatorBSC.sol
*/
            
////// SPDX-License-Identifier-FLATTEN-SUPPRESS-WARNING: MIT
pragma solidity 0.6.11;

////import "@openzeppelin/contracts/math/SafeMath.sol";


library HomoraMath {
    using SafeMath for uint;

    function divCeil(uint lhs, uint rhs) internal pure returns (uint) {
        return lhs.add(rhs).sub(1) / rhs;
    }

    function fmul(uint lhs, uint rhs) internal pure returns (uint) {
        return lhs.mul(rhs) / (2**112);
    }

    function fdiv(uint lhs, uint rhs) internal pure returns (uint) {
        return lhs.mul(2**112) / rhs;
    }

    // implementation from https://github.com/Uniswap/uniswap-lib/commit/99f3f28770640ba1bb1ff460ac7c5292fb8291a0
    // original implementation: https://github.com/abdk-consulting/abdk-libraries-solidity/blob/master/ABDKMath64x64.sol#L687
    function sqrt(uint x) internal pure returns (uint) {
        if (x == 0) return 0;
        uint xx = x;
        uint r = 1;

        if (xx >= 0x100000000000000000000000000000000) {
            xx >>= 128;
            r <<= 64;
        }

        if (xx >= 0x10000000000000000) {
            xx >>= 64;
            r <<= 32;
        }
        if (xx >= 0x100000000) {
            xx >>= 32;
            r <<= 16;
        }
        if (xx >= 0x10000) {
            xx >>= 16;
            r <<= 8;
        }
        if (xx >= 0x100) {
            xx >>= 8;
            r <<= 4;
        }
        if (xx >= 0x10) {
            xx >>= 4;
            r <<= 2;
        }
        if (xx >= 0x8) {
            r <<= 1;
        }

        r = (r + x / r) >> 1;
        r = (r + x / r) >> 1;
        r = (r + x / r) >> 1;
        r = (r + x / r) >> 1;
        r = (r + x / r) >> 1;
        r = (r + x / r) >> 1;
        r = (r + x / r) >> 1; // Seven iterations should be enough
        uint r1 = x / r;
        return (r < r1 ? r : r1);
    }
}




/** 
 *  SourceUnit: /Users/yuexue/Downloads/Bunny-main 2/contracts/dashboard/calculator/PriceCalculatorBSC.sol
*/
            
////// SPDX-License-Identifier-FLATTEN-SUPPRESS-WARNING: MIT
pragma solidity ^0.6.11;

/*
  ___                      _   _
 | _ )_  _ _ _  _ _ _  _  | | | |
 | _ \ || | ' \| ' \ || | |_| |_|
 |___/\_,_|_||_|_||_\_, | (_) (_)
                    |__/

*
* MIT License
* ===========
*
* Copyright (c) 2020 BunnyFinance
*
* Permission is hereby granted, free of charge, to any person obtaining a copy
* of this software and associated documentation files (the "Software"), to deal
* in the Software without restriction, including without limitation the rights
* to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
* copies of the Software, and to permit persons to whom the Software is
* furnished to do so, subject to the following conditions:
*
* The above copyright notice and this permission notice shall be included in all
* copies or substantial portions of the Software.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
* IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
* FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
* AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
* LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
* OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
*/


interface IPriceCalculator {
    struct ReferenceData {
        uint lastData;
        uint lastUpdated;
    }

    function pricesInUSD(address[] memory assets) external view returns (uint[] memory);
    function valueOfAsset(address asset, uint amount) external view returns (uint valueInBNB, uint valueInUSD);
    function priceOfBunny() view external returns (uint);
    function priceOfBNB() view external returns (uint);
}




/** 
 *  SourceUnit: /Users/yuexue/Downloads/Bunny-main 2/contracts/dashboard/calculator/PriceCalculatorBSC.sol
*/
            
////// SPDX-License-Identifier-FLATTEN-SUPPRESS-WARNING: MIT
pragma solidity >=0.6.0;

interface AggregatorV3Interface {

    function decimals() external view returns (uint8);
    function description() external view returns (string memory);
    function version() external view returns (uint256);

    // getRoundData and latestRoundData should both raise "No data present"
    // if they do not have data to report, instead of returning unset values
    // which could be misinterpreted as actual reported values.
    function getRoundData(uint80 _roundId)
    external
    view
    returns (
        uint80 roundId,
        int256 answer,
        uint256 startedAt,
        uint256 updatedAt,
        uint80 answeredInRound
    );
    function latestRoundData()
    external
    view
    returns (
        uint80 roundId,
        int256 answer,
        uint256 startedAt,
        uint256 updatedAt,
        uint80 answeredInRound
    );

}




/** 
 *  SourceUnit: /Users/yuexue/Downloads/Bunny-main 2/contracts/dashboard/calculator/PriceCalculatorBSC.sol
*/
            
////// SPDX-License-Identifier-FLATTEN-SUPPRESS-WARNING: MIT
pragma solidity ^0.6.11;

interface IPancakeFactory {
    event PairCreated(address indexed token0, address indexed token1, address pair, uint);

    function feeTo() external view returns (address);
    function feeToSetter() external view returns (address);

    function getPair(address tokenA, address tokenB) external view returns (address pair);
    function allPairs(uint) external view returns (address pair);
    function allPairsLength() external view returns (uint);

    function createPair(address tokenA, address tokenB) external returns (address pair);

    function setFeeTo(address) external;
    function setFeeToSetter(address) external;
}



/** 
 *  SourceUnit: /Users/yuexue/Downloads/Bunny-main 2/contracts/dashboard/calculator/PriceCalculatorBSC.sol
*/
            
////// SPDX-License-Identifier-FLATTEN-SUPPRESS-WARNING: MIT
pragma solidity >=0.6.2;

interface IPancakePair {
    event Approval(address indexed owner, address indexed spender, uint value);
    event Transfer(address indexed from, address indexed to, uint value);

    function name() external pure returns (string memory);
    function symbol() external pure returns (string memory);
    function decimals() external pure returns (uint8);
    function totalSupply() external view returns (uint);
    function balanceOf(address owner) external view returns (uint);
    function allowance(address owner, address spender) external view returns (uint);

    function approve(address spender, uint value) external returns (bool);
    function transfer(address to, uint value) external returns (bool);
    function transferFrom(address from, address to, uint value) external returns (bool);

    function DOMAIN_SEPARATOR() external view returns (bytes32);
    function PERMIT_TYPEHASH() external pure returns (bytes32);
    function nonces(address owner) external view returns (uint);

    function permit(address owner, address spender, uint value, uint deadline, uint8 v, bytes32 r, bytes32 s) external;

    event Mint(address indexed sender, uint amount0, uint amount1);
    event Burn(address indexed sender, uint amount0, uint amount1, address indexed to);
    event Swap(
        address indexed sender,
        uint amount0In,
        uint amount1In,
        uint amount0Out,
        uint amount1Out,
        address indexed to
    );
    event Sync(uint112 reserve0, uint112 reserve1);

    function MINIMUM_LIQUIDITY() external pure returns (uint);
    function factory() external view returns (address);
    function token0() external view returns (address);
    function token1() external view returns (address);
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
    function price0CumulativeLast() external view returns (uint);
    function price1CumulativeLast() external view returns (uint);
    function kLast() external view returns (uint);

    function mint(address to) external returns (uint liquidity);
    function burn(address to) external returns (uint amount0, uint amount1);
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
    function skim(address to) external;
    function sync() external;

    function initialize(address, address) external;
}



/** 
 *  SourceUnit: /Users/yuexue/Downloads/Bunny-main 2/contracts/dashboard/calculator/PriceCalculatorBSC.sol
*/
            
////// SPDX-License-Identifier-FLATTEN-SUPPRESS-WARNING: MIT

pragma solidity >=0.6.0 <0.8.0;

////import "../GSN/ContextUpgradeable.sol";
////import "../proxy/Initializable.sol";
/**
 * @dev Contract module which provides a basic access control mechanism, where
 * there is an account (an owner) that can be granted exclusive access to
 * specific functions.
 *
 * By default, the owner account will be the one that deploys the contract. This
 * can later be changed with {transferOwnership}.
 *
 * This module is used through inheritance. It will make available the modifier
 * `onlyOwner`, which can be applied to your functions to restrict their use to
 * the owner.
 */
abstract contract OwnableUpgradeable is Initializable, ContextUpgradeable {
    address private _owner;

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    /**
     * @dev Initializes the contract setting the deployer as the initial owner.
     */
    function __Ownable_init() internal initializer {
        __Context_init_unchained();
        __Ownable_init_unchained();
    }

    function __Ownable_init_unchained() internal initializer {
        address msgSender = _msgSender();
        _owner = msgSender;
        emit OwnershipTransferred(address(0), msgSender);
    }

    /**
     * @dev Returns the address of the current owner.
     */
    function owner() public view returns (address) {
        return _owner;
    }

    /**
     * @dev Throws if called by any account other than the owner.
     */
    modifier onlyOwner() {
        require(_owner == _msgSender(), "Ownable: caller is not the owner");
        _;
    }

    /**
     * @dev Leaves the contract without owner. It will not be possible to call
     * `onlyOwner` functions anymore. Can only be called by the current owner.
     *
     * NOTE: Renouncing ownership will leave the contract without an owner,
     * thereby removing any functionality that is only available to the owner.
     */
    function renounceOwnership() public virtual onlyOwner {
        emit OwnershipTransferred(_owner, address(0));
        _owner = address(0);
    }

    /**
     * @dev Transfers ownership of the contract to a new account (`newOwner`).
     * Can only be called by the current owner.
     */
    function transferOwnership(address newOwner) public virtual onlyOwner {
        require(newOwner != address(0), "Ownable: new owner is the zero address");
        emit OwnershipTransferred(_owner, newOwner);
        _owner = newOwner;
    }
    uint256[49] private __gap;
}




/** 
 *  SourceUnit: /Users/yuexue/Downloads/Bunny-main 2/contracts/dashboard/calculator/PriceCalculatorBSC.sol
*/
            
pragma solidity ^0.6.11;

interface IBEP20 {
    /**
     * @dev Returns the amount of tokens in existence.
     */
    function totalSupply() external view returns (uint256);

    /**
     * @dev Returns the token decimals.
     */
    function decimals() external view returns (uint8);

    /**
     * @dev Returns the token symbol.
     */
    function symbol() external view returns (string memory);

    /**
     * @dev Returns the token name.
     */
    function name() external view returns (string memory);

    /**
     * @dev Returns the bep token owner.
     */
    function getOwner() external view returns (address);

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
    function allowance(address _owner, address spender) external view returns (uint256);

    /**
     * @dev Sets `amount` as the allowance of `spender` over the caller's tokens.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * ////IMPORTANT: Beware that changing an allowance with this method brings the risk
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

/** 
 *  SourceUnit: /Users/yuexue/Downloads/Bunny-main 2/contracts/dashboard/calculator/PriceCalculatorBSC.sol
*/

////// SPDX-License-Identifier-FLATTEN-SUPPRESS-WARNING: MIT
pragma solidity ^0.6.11;
pragma experimental ABIEncoderV2;

/*
  ___                      _   _
 | _ )_  _ _ _  _ _ _  _  | | | |
 | _ \ || | ' \| ' \ || | |_| |_|
 |___/\_,_|_||_|_||_\_, | (_) (_)
                    |__/

*
* MIT License
* ===========
*
* Copyright (c) 2020 BunnyFinance
*
* Permission is hereby granted, free of charge, to any person obtaining a copy
* of this software and associated documentation files (the "Software"), to deal
* in the Software without restriction, including without limitation the rights
* to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
* copies of the Software, and to permit persons to whom the Software is
* furnished to do so, subject to the following conditions:
*
* The above copyright notice and this permission notice shall be included in all
* copies or substantial portions of the Software.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
* IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
* FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
* AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
* LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
* OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
* SOFTWARE.
*/

////import "../../IBEP20.sol";
////import "../../openzeppelin-upgradable/access/OwnableUpgradeable.sol";

////import "../../interfaces/IPancakePair.sol";
////import "../../interfaces/IPancakeFactory.sol";
////import "../../interfaces/AggregatorV3Interface.sol";
////import "../../interfaces/IPriceCalculator.sol";
////import "../../library/HomoraMath.sol";


contract PriceCalculatorBSC is IPriceCalculator, OwnableUpgradeable {
    using SafeMath for uint;
    using HomoraMath for uint;

    address public constant WBNB = 0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c;
    address public constant CAKE = 0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82;
    address public constant BUNNY = 0xC9849E6fdB743d08fAeE3E34dd2D1bc69EA11a51;
    address public constant VAI = 0x4BD17003473389A42DAF6a0a729f6Fdb328BbBd7;
    address public constant BUSD = 0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56;

    address public constant BUNNY_BNB_V1 = 0x7Bb89460599Dbf32ee3Aa50798BBcEae2A5F7f6a;
    address public constant BUNNY_BNB_V2 = 0x5aFEf8567414F29f0f927A0F2787b188624c10E2;

    IPancakeFactory private constant factory = IPancakeFactory(0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73);

    /* ========== STATE VARIABLES ========== */

    mapping(address => address) private pairTokens;
    mapping(address => address) private tokenFeeds;
    mapping(address => ReferenceData) public references;

    address public keeper;

    /* ========== MODIFIERS ========== */

    modifier onlyKeeper {
        require(msg.sender == keeper || msg.sender == owner(), 'Qore: caller is not the owner or keeper');
        _;
    }

    /* ========== INITIALIZER ========== */

    function initialize() external initializer {
        __Ownable_init();
        setPairToken(VAI, BUSD);
    }

    /* ========== RESTRICTED FUNCTIONS ========== */

    function setKeeper(address _keeper) external onlyKeeper {
        require(_keeper != address(0), 'PriceCalculatorBSC: invalid keeper address');
        keeper = _keeper;
    }

    function setPairToken(address asset, address pairToken) public onlyKeeper {
        pairTokens[asset] = pairToken;
    }

    function setTokenFeed(address asset, address feed) public onlyKeeper {
        tokenFeeds[asset] = feed;
    }

    function setPrices(address[] memory assets, uint[] memory prices) external onlyKeeper {
        for (uint i = 0; i < assets.length; i++) {
            references[assets[i]] = ReferenceData({lastData : prices[i], lastUpdated : block.timestamp});
        }
    }

    /* ========== VIEWS ========== */

    function priceOfBNB() view public override returns (uint) {
        (, int price, , ,) = AggregatorV3Interface(tokenFeeds[WBNB]).latestRoundData();
        return uint(price).mul(1e10);
    }

    function priceOfCake() view public returns (uint) {
        (, int price, , ,) = AggregatorV3Interface(tokenFeeds[CAKE]).latestRoundData();
        return uint(price).mul(1e10);
    }

    function priceOfBunny() view public override returns (uint) {
        (, uint price) = valueOfAsset(BUNNY, 1e18);
        return price;
    }

    function pricesInUSD(address[] memory assets) public view override returns (uint[] memory) {
        uint[] memory prices = new uint[](assets.length);
        for (uint i = 0; i < assets.length; i++) {
            (, uint valueInUSD) = valueOfAsset(assets[i], 1e18);
            prices[i] = valueInUSD;
        }
        return prices;
    }

    function valueOfAsset(address asset, uint amount) public view override returns (uint valueInBNB, uint valueInUSD) {
        if (asset == address(0) || asset == WBNB) {
            return _oracleValueOf(asset, amount);
        } else if (keccak256(abi.encodePacked(IPancakePair(asset).symbol())) == keccak256("Cake-LP")) {
            return _getPairPrice(asset, amount);
        } else {
            return _oracleValueOf(asset, amount);
        }
    }

    function unsafeValueOfAsset(address asset, uint amount) public view returns (uint valueInBNB, uint valueInUSD) {
        valueInBNB = 0;
        valueInUSD = 0;

        if (asset == address(0) || asset == WBNB) {
            valueInBNB = amount;
            valueInUSD = amount.mul(priceOfBNB()).div(1e18);
        }
        else if (keccak256(abi.encodePacked(IPancakePair(asset).symbol())) == keccak256("Cake-LP")) {
            if (IPancakePair(asset).totalSupply() == 0) return (0, 0);

            (uint reserve0, uint reserve1, ) = IPancakePair(asset).getReserves();
            if (IPancakePair(asset).token0() == WBNB) {
                valueInBNB = amount.mul(reserve0).mul(2).div(IPancakePair(asset).totalSupply());
                valueInUSD = valueInBNB.mul(priceOfBNB()).div(1e18);
            } else if (IPancakePair(asset).token1() == WBNB) {
                valueInBNB = amount.mul(reserve1).mul(2).div(IPancakePair(asset).totalSupply());
                valueInUSD = valueInBNB.mul(priceOfBNB()).div(1e18);
            } else {
                (uint token0PriceInBNB,) = valueOfAsset(IPancakePair(asset).token0(), 1e18);
                valueInBNB = amount.mul(reserve0).mul(2).mul(token0PriceInBNB).div(1e18).div(IPancakePair(asset).totalSupply());
                valueInUSD = valueInBNB.mul(priceOfBNB()).div(1e18);
            }
        }
        else {
            address pairToken = pairTokens[asset] == address(0) ? WBNB : pairTokens[asset];
            address pair = factory.getPair(asset, pairToken);
            if (IBEP20(asset).balanceOf(pair) == 0) return (0, 0);

            (uint reserve0, uint reserve1, ) = IPancakePair(pair).getReserves();
            if (IPancakePair(pair).token0() == pairToken) {
                valueInBNB = reserve0.mul(amount).div(reserve1);
            } else if (IPancakePair(pair).token1() == pairToken) {
                valueInBNB = reserve1.mul(amount).div(reserve0);
            } else {
                return (0, 0);
            }

            if (pairToken != WBNB) {
                (uint pairValueInBNB,) = valueOfAsset(pairToken, 1e18);
                valueInBNB = valueInBNB.mul(pairValueInBNB).div(1e18);
            }
            valueInUSD = valueInBNB.mul(priceOfBNB()).div(1e18);
        }
    }

    /* ========== PRIVATE FUNCTIONS ========== */

    function _getPairPrice(address pair, uint amount) private view returns (uint valueInBNB, uint valueInUSD) {
        address token0 = IPancakePair(pair).token0();
        address token1 = IPancakePair(pair).token1();
        uint totalSupply = IPancakePair(pair).totalSupply();
        (uint r0, uint r1,) = IPancakePair(pair).getReserves();

        uint sqrtK = HomoraMath.sqrt(r0.mul(r1)).fdiv(totalSupply);
        (uint px0,) = _oracleValueOf(token0, 1e18);
        (uint px1,) = _oracleValueOf(token1, 1e18);
        uint fairPriceInBNB = sqrtK.mul(2).mul(HomoraMath.sqrt(px0)).div(2 ** 56).mul(HomoraMath.sqrt(px1)).div(2 ** 56);

        valueInBNB = fairPriceInBNB.mul(amount).div(1e18);
        valueInUSD = valueInBNB.mul(priceOfBNB()).div(1e18);
    }

    function _oracleValueOf(address asset, uint amount) private view returns (uint valueInBNB, uint valueInUSD) {
        valueInUSD = 0;
        if (tokenFeeds[asset] != address(0)) {
            (, int price, , ,) = AggregatorV3Interface(tokenFeeds[asset]).latestRoundData();
            valueInUSD = uint(price).mul(1e10).mul(amount).div(1e18);
        } else if (references[asset].lastUpdated > block.timestamp.sub(1 days)) {
            valueInUSD = references[asset].lastData.mul(amount).div(1e18);
        }
        valueInBNB = valueInUSD.mul(1e18).div(priceOfBNB());
    }
}

