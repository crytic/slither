/**
 *Submitted for verification at BscScan.com on 2021-09-10
*/

// SPDX-License-Identifier: MIT
pragma solidity 0.5.16;
pragma experimental ABIEncoderV2;

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
contract Context {
  // Empty internal constructor, to prevent people from mistakenly deploying
  // an instance of this contract, which should be used via inheritance.
  constructor () internal { }

  function _msgSender() internal view returns (address payable) {
    return msg.sender;
  }

  function _msgData() internal view returns (bytes memory) {
    this; // silence state mutability warning without generating bytecode - see https://github.com/ethereum/solidity/issues/2691
    return msg.data;
  }
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
   * - The divisor cannot be zero.
   */
  function div(uint256 a, uint256 b, string memory errorMessage) internal pure returns (uint256) {
    // Solidity only automatically asserts when dividing by 0
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
   * - The divisor cannot be zero.
   */
  function mod(uint256 a, uint256 b, string memory errorMessage) internal pure returns (uint256) {
    require(b != 0, errorMessage);
    return a % b;
  }
}

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
contract Ownable is Context {
  address private _owner;

  event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

  /**
   * @dev Initializes the contract setting the deployer as the initial owner.
   */
  constructor () internal {
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
  function renounceOwnership() public onlyOwner {
    emit OwnershipTransferred(_owner, address(0));
    _owner = address(0);
  }

  /**
   * @dev Transfers ownership of the contract to a new account (`newOwner`).
   * Can only be called by the current owner.
   */
  function transferOwnership(address newOwner) public onlyOwner {
    _transferOwnership(newOwner);
  }

  /**
   * @dev Transfers ownership of the contract to a new account (`newOwner`).
   */
  function _transferOwnership(address newOwner) internal {
    require(newOwner != address(0), "Ownable: new owner is the zero address");
    emit OwnershipTransferred(_owner, newOwner);
    _owner = newOwner;
  }
}
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

contract StakeContract is Ownable {
    using SafeMath for uint256;
    uint public stakeTime = 1209600; // 14 days
    uint public minStake = 10;
    uint public panaltyPercent = 10;
    uint public stakeFeePercent = 1;
    uint public percentDecimal = 4; // % two places after the decimal separator    
    IBEP20 public bep20 = IBEP20(0x23d91ECd922Ac08aA6B585035E55DaD551a25866);
    address[] public bep20Profit = [0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56];
    address public takeBep20 = 0x3303003A792386c0528020008F7b2eA3C97A21Ed;
    struct bag {
        uint start;
        uint amount;
        mapping(address => uint) userBalance; // asset => balance
    }
    struct package {
        uint[] bagLength;
        mapping(uint => bag) bags;
    }
    mapping(address => package) packages;
    // EVENT
    event Stake(uint _amount, uint index);
    event Unstake(uint _bagLengthIndex);
    event DepositProfit(address _bep20, uint _amount, address[] users, uint[] _bagIndexs);
    
    function() payable external{}
    
    function getOccupancy(uint _stakeAmount) public view returns (uint) {
        uint bep20Balance = getRemainingToken(bep20);
        if(bep20Balance == 0) return 0;
        return _stakeAmount.mul(10 ** percentDecimal).div(bep20Balance);
    }
    function getBep20Profit() public view returns(address[] memory) {
        return bep20Profit;
    }
    function updateBalance(uint[] memory _amounts, address[] memory users, address _asset, uint[] memory _bagIndexs) internal returns (uint _amount){
        for(uint i = 0; i < users.length; i++) {
            packages[users[i]].bags[_bagIndexs[i]].userBalance[_asset] += _amounts[i];
            _amount += _amounts[i];
        }
    }
    function depositProfit(uint[] memory _amounts, address[] memory users, uint[] memory _bagIndexs) public payable {
        require(users.length > 0, 'users empty');
        uint _amount = updateBalance(_amounts, users, address(0), _bagIndexs);
        require(msg.value >= _amount, 'insufficient-allowance');
        emit DepositProfit(address(0), _amount, users, _bagIndexs);
    }
    function depositProfitBep20(address _bep20pf, uint[] memory _amounts, address[] memory users, uint[] memory _bagIndexs) public {
        require(users.length > 0, 'users empty');
        uint _amount = updateBalance(_amounts, users, address(_bep20pf), _bagIndexs);
        require(IBEP20(_bep20pf).transferFrom(msg.sender, address(this), _amount), 'insufficient-allowance');
        bool _existed;
        for(uint i = 0; i < bep20Profit.length; i++) {
            if(bep20Profit[i] == _bep20pf) _existed = true;
        }
        if(!_existed) bep20Profit.push(_bep20pf);
        emit DepositProfit(_bep20pf, _amount, users, _bagIndexs);
    }
    function removeBagIndex(uint _bagLengthIndex) internal {
        packages[msg.sender].bags[packages[msg.sender].bagLength[_bagLengthIndex]] = bag(0, 0);
        packages[msg.sender].bagLength[_bagLengthIndex] = packages[msg.sender].bagLength[packages[msg.sender].bagLength.length - 1];
        packages[msg.sender].bagLength.length--;
    }
     function rewardBNB(uint _stakeAmount) public view returns(uint _reward) {
        uint bep20Balance = getRemainingToken(bep20);
        uint balance = address(this).balance;
        return balance.mul(_stakeAmount).div(bep20Balance);
    }
    function refundReward(uint index) internal {
        uint BNBBalance = packages[_msgSender()].bags[index].userBalance[address(0)];
        if(BNBBalance > 0) msg.sender.transfer(BNBBalance);
        for(uint i = 0; i < bep20Profit.length; i++) {
            
            uint bep20pfBalance = packages[_msgSender()].bags[index].userBalance[bep20Profit[i]];
            if(bep20pfBalance > 0) {
                IBEP20 bep20pf = IBEP20(bep20Profit[i]);
                bep20pf.transfer(msg.sender, bep20pfBalance);
            }
        }
    }
    function refundToken(uint _bagLengthIndex) internal {
        uint index = packages[msg.sender].bagLength[_bagLengthIndex];
        require(packages[msg.sender].bags[index].amount > 0, 'index is not exist !');
        uint stakeStart = packages[msg.sender].bags[index].start;
        uint stakeAmount = packages[msg.sender].bags[index].amount;
        refundReward(index);
        uint percent = now.sub(stakeStart) < stakeTime ? panaltyPercent : stakeFeePercent;
        
        uint fee = stakeAmount.mul(percent).div(100);
        bep20.transfer(takeBep20, fee);
        bep20.transfer(msg.sender, stakeAmount.sub(fee));
        emit Unstake(index);
    }
    
    function unstake(uint _bagLengthIndex) public {
        refundToken(_bagLengthIndex);
        removeBagIndex(_bagLengthIndex);
    }
    
    function unstakes(uint[] memory indexs) public {
        for(uint i = 0; i < indexs.length; i++) {
            refundToken(indexs[i]);
            packages[msg.sender].bags[packages[msg.sender].bagLength[indexs[i]]] = bag(0, 0);
            packages[msg.sender].bagLength[indexs[i]] = packages[msg.sender].bagLength[packages[msg.sender].bagLength.length - (i+1)];
        }
        packages[msg.sender].bagLength.length -= indexs.length;
        
    }
    function stake(uint _id, uint _amount) public {
        require(_amount >= minStake, 'Amount lessthan min stake !');
        require(bep20.transferFrom(msg.sender, address(this), _amount), 'insufficient-allowance');
        packages[msg.sender].bags[_id] = bag(now, _amount);
        packages[msg.sender].bagLength.push(_id);
        emit Stake(_amount, _id);
    }
    function getStake(address _guy) public view returns(uint[] memory _bagLength) {
        _bagLength = packages[_guy].bagLength; 
    }
    function getStake(address _guy, uint index) public view returns(uint start, uint amount) {
        return (packages[_guy].bags[index].start, packages[_guy].bags[index].amount); 
    }
    function getStakeReward(address _guy, uint index, address asset) public view returns(uint _reward) {
        return packages[_guy].bags[index].userBalance[asset];
    }
    function config(uint _stakeTime, uint _minStake, address _takeBep20, 
    uint _percentDecimal,
    uint _panaltyPercent, uint _stakeFeePercent) public onlyOwner {
        stakeTime = _stakeTime;
        minStake = _minStake;
        takeBep20 = _takeBep20;
        percentDecimal = _percentDecimal;
        panaltyPercent = _panaltyPercent;
        stakeFeePercent = _stakeFeePercent;
    }
    function getRemainingToken(IBEP20 _token) public view returns (uint) {
        return _token.balanceOf(address(this));
    }
    function withdrawBEP20(address _to, IBEP20 _bep20, uint _amount) public onlyOwner {
        _bep20.transfer(_to, _amount);
    }
    function withdraw(address payable _to, uint _amount) public onlyOwner {
        _to.transfer(_amount);
    }
}