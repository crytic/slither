/**
 *Submitted for verification at gnosisscan.io on 2022-08-05
*/

// File: openzeppelin-solidity/contracts/token/ERC20/ERC20Basic.sol

pragma solidity ^0.4.24;


/**
 * @title ERC20Basic
 * @dev Simpler version of ERC20 interface
 * See https://github.com/ethereum/EIPs/issues/179
 */
contract ERC20Basic {
  function totalSupply() public view returns (uint256);
  function balanceOf(address _who) public view returns (uint256);
  function transfer(address _to, uint256 _value) public returns (bool);
  event Transfer(address indexed from, address indexed to, uint256 value);
}

// File: openzeppelin-solidity/contracts/math/SafeMath.sol

pragma solidity ^0.4.24;


/**
 * @title SafeMath
 * @dev Math operations with safety checks that throw on error
 */
library SafeMath {

  /**
  * @dev Multiplies two numbers, throws on overflow.
  */
  function mul(uint256 _a, uint256 _b) internal pure returns (uint256 c) {
    // Gas optimization: this is cheaper than asserting 'a' not being zero, but the
    // benefit is lost if 'b' is also tested.
    // See: https://github.com/OpenZeppelin/openzeppelin-solidity/pull/522
    if (_a == 0) {
      return 0;
    }

    c = _a * _b;
    assert(c / _a == _b);
    return c;
  }

  /**
  * @dev Integer division of two numbers, truncating the quotient.
  */
  function div(uint256 _a, uint256 _b) internal pure returns (uint256) {
    // assert(_b > 0); // Solidity automatically throws when dividing by 0
    // uint256 c = _a / _b;
    // assert(_a == _b * c + _a % _b); // There is no case in which this doesn't hold
    return _a / _b;
  }

  /**
  * @dev Subtracts two numbers, throws on overflow (i.e. if subtrahend is greater than minuend).
  */
  function sub(uint256 _a, uint256 _b) internal pure returns (uint256) {
    assert(_b <= _a);
    return _a - _b;
  }

  /**
  * @dev Adds two numbers, throws on overflow.
  */
  function add(uint256 _a, uint256 _b) internal pure returns (uint256 c) {
    c = _a + _b;
    assert(c >= _a);
    return c;
  }
}

// File: openzeppelin-solidity/contracts/token/ERC20/BasicToken.sol

pragma solidity ^0.4.24;




/**
 * @title Basic token
 * @dev Basic version of StandardToken, with no allowances.
 */
contract BasicToken is ERC20Basic {
  using SafeMath for uint256;

  mapping(address => uint256) internal balances;

  uint256 internal totalSupply_;

  /**
  * @dev Total number of tokens in existence
  */
  function totalSupply() public view returns (uint256) {
    return totalSupply_;
  }

  /**
  * @dev Transfer token for a specified address
  * @param _to The address to transfer to.
  * @param _value The amount to be transferred.
  */
  function transfer(address _to, uint256 _value) public returns (bool) {
    require(_value <= balances[msg.sender]);
    require(_to != address(0));

    balances[msg.sender] = balances[msg.sender].sub(_value);
    balances[_to] = balances[_to].add(_value);
    emit Transfer(msg.sender, _to, _value);
    return true;
  }

  /**
  * @dev Gets the balance of the specified address.
  * @param _owner The address to query the the balance of.
  * @return An uint256 representing the amount owned by the passed address.
  */
  function balanceOf(address _owner) public view returns (uint256) {
    return balances[_owner];
  }

}

// File: openzeppelin-solidity/contracts/token/ERC20/BurnableToken.sol

pragma solidity ^0.4.24;



/**
 * @title Burnable Token
 * @dev Token that can be irreversibly burned (destroyed).
 */
contract BurnableToken is BasicToken {

  event Burn(address indexed burner, uint256 value);

  /**
   * @dev Burns a specific amount of tokens.
   * @param _value The amount of token to be burned.
   */
  function burn(uint256 _value) public {
    _burn(msg.sender, _value);
  }

  function _burn(address _who, uint256 _value) internal {
    require(_value <= balances[_who]);
    // no need to require value <= totalSupply, since that would imply the
    // sender's balance is greater than the totalSupply, which *should* be an assertion failure

    balances[_who] = balances[_who].sub(_value);
    totalSupply_ = totalSupply_.sub(_value);
    emit Burn(_who, _value);
    emit Transfer(_who, address(0), _value);
  }
}

// File: openzeppelin-solidity/contracts/token/ERC20/ERC20.sol

pragma solidity ^0.4.24;



/**
 * @title ERC20 interface
 * @dev see https://github.com/ethereum/EIPs/issues/20
 */
contract ERC20 is ERC20Basic {
  function allowance(address _owner, address _spender)
    public view returns (uint256);

  function transferFrom(address _from, address _to, uint256 _value)
    public returns (bool);

  function approve(address _spender, uint256 _value) public returns (bool);
  event Approval(
    address indexed owner,
    address indexed spender,
    uint256 value
  );
}

// File: openzeppelin-solidity/contracts/token/ERC20/StandardToken.sol

pragma solidity ^0.4.24;




/**
 * @title Standard ERC20 token
 *
 * @dev Implementation of the basic standard token.
 * https://github.com/ethereum/EIPs/issues/20
 * Based on code by FirstBlood: https://github.com/Firstbloodio/token/blob/master/smart_contract/FirstBloodToken.sol
 */
contract StandardToken is ERC20, BasicToken {

  mapping (address => mapping (address => uint256)) internal allowed;


  /**
   * @dev Transfer tokens from one address to another
   * @param _from address The address which you want to send tokens from
   * @param _to address The address which you want to transfer to
   * @param _value uint256 the amount of tokens to be transferred
   */
  function transferFrom(
    address _from,
    address _to,
    uint256 _value
  )
    public
    returns (bool)
  {
    require(_value <= balances[_from]);
    require(_value <= allowed[_from][msg.sender]);
    require(_to != address(0));

    balances[_from] = balances[_from].sub(_value);
    balances[_to] = balances[_to].add(_value);
    allowed[_from][msg.sender] = allowed[_from][msg.sender].sub(_value);
    emit Transfer(_from, _to, _value);
    return true;
  }

  /**
   * @dev Approve the passed address to spend the specified amount of tokens on behalf of msg.sender.
   * Beware that changing an allowance with this method brings the risk that someone may use both the old
   * and the new allowance by unfortunate transaction ordering. One possible solution to mitigate this
   * race condition is to first reduce the spender's allowance to 0 and set the desired value afterwards:
   * https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
   * @param _spender The address which will spend the funds.
   * @param _value The amount of tokens to be spent.
   */
  function approve(address _spender, uint256 _value) public returns (bool) {
    allowed[msg.sender][_spender] = _value;
    emit Approval(msg.sender, _spender, _value);
    return true;
  }

  /**
   * @dev Function to check the amount of tokens that an owner allowed to a spender.
   * @param _owner address The address which owns the funds.
   * @param _spender address The address which will spend the funds.
   * @return A uint256 specifying the amount of tokens still available for the spender.
   */
  function allowance(
    address _owner,
    address _spender
   )
    public
    view
    returns (uint256)
  {
    return allowed[_owner][_spender];
  }

  /**
   * @dev Increase the amount of tokens that an owner allowed to a spender.
   * approve should be called when allowed[_spender] == 0. To increment
   * allowed value is better to use this function to avoid 2 calls (and wait until
   * the first transaction is mined)
   * From MonolithDAO Token.sol
   * @param _spender The address which will spend the funds.
   * @param _addedValue The amount of tokens to increase the allowance by.
   */
  function increaseApproval(
    address _spender,
    uint256 _addedValue
  )
    public
    returns (bool)
  {
    allowed[msg.sender][_spender] = (
      allowed[msg.sender][_spender].add(_addedValue));
    emit Approval(msg.sender, _spender, allowed[msg.sender][_spender]);
    return true;
  }

  /**
   * @dev Decrease the amount of tokens that an owner allowed to a spender.
   * approve should be called when allowed[_spender] == 0. To decrement
   * allowed value is better to use this function to avoid 2 calls (and wait until
   * the first transaction is mined)
   * From MonolithDAO Token.sol
   * @param _spender The address which will spend the funds.
   * @param _subtractedValue The amount of tokens to decrease the allowance by.
   */
  function decreaseApproval(
    address _spender,
    uint256 _subtractedValue
  )
    public
    returns (bool)
  {
    uint256 oldValue = allowed[msg.sender][_spender];
    if (_subtractedValue >= oldValue) {
      allowed[msg.sender][_spender] = 0;
    } else {
      allowed[msg.sender][_spender] = oldValue.sub(_subtractedValue);
    }
    emit Approval(msg.sender, _spender, allowed[msg.sender][_spender]);
    return true;
  }

}

// File: openzeppelin-solidity/contracts/ownership/Ownable.sol

pragma solidity ^0.4.24;


/**
 * @title Ownable
 * @dev The Ownable contract has an owner address, and provides basic authorization control
 * functions, this simplifies the implementation of "user permissions".
 */
contract Ownable {
  address public owner;


  event OwnershipRenounced(address indexed previousOwner);
  event OwnershipTransferred(
    address indexed previousOwner,
    address indexed newOwner
  );


  /**
   * @dev The Ownable constructor sets the original `owner` of the contract to the sender
   * account.
   */
  constructor() public {
    owner = msg.sender;
  }

  /**
   * @dev Throws if called by any account other than the owner.
   */
  modifier onlyOwner() {
    require(msg.sender == owner);
    _;
  }

  /**
   * @dev Allows the current owner to relinquish control of the contract.
   * @notice Renouncing to ownership will leave the contract without an owner.
   * It will not be possible to call the functions with the `onlyOwner`
   * modifier anymore.
   */
  function renounceOwnership() public onlyOwner {
    emit OwnershipRenounced(owner);
    owner = address(0);
  }

  /**
   * @dev Allows the current owner to transfer control of the contract to a newOwner.
   * @param _newOwner The address to transfer ownership to.
   */
  function transferOwnership(address _newOwner) public onlyOwner {
    _transferOwnership(_newOwner);
  }

  /**
   * @dev Transfers control of the contract to a newOwner.
   * @param _newOwner The address to transfer ownership to.
   */
  function _transferOwnership(address _newOwner) internal {
    require(_newOwner != address(0));
    emit OwnershipTransferred(owner, _newOwner);
    owner = _newOwner;
  }
}

// File: openzeppelin-solidity/contracts/token/ERC20/MintableToken.sol

pragma solidity ^0.4.24;




/**
 * @title Mintable token
 * @dev Simple ERC20 Token example, with mintable token creation
 * Based on code by TokenMarketNet: https://github.com/TokenMarketNet/ico/blob/master/contracts/MintableToken.sol
 */
contract MintableToken is StandardToken, Ownable {
  event Mint(address indexed to, uint256 amount);
  event MintFinished();

  bool public mintingFinished = false;


  modifier canMint() {
    require(!mintingFinished);
    _;
  }

  modifier hasMintPermission() {
    require(msg.sender == owner);
    _;
  }

  /**
   * @dev Function to mint tokens
   * @param _to The address that will receive the minted tokens.
   * @param _amount The amount of tokens to mint.
   * @return A boolean that indicates if the operation was successful.
   */
  function mint(
    address _to,
    uint256 _amount
  )
    public
    hasMintPermission
    canMint
    returns (bool)
  {
    totalSupply_ = totalSupply_.add(_amount);
    balances[_to] = balances[_to].add(_amount);
    emit Mint(_to, _amount);
    emit Transfer(address(0), _to, _amount);
    return true;
  }

  /**
   * @dev Function to stop minting new tokens.
   * @return True if the operation was successful.
   */
  function finishMinting() public onlyOwner canMint returns (bool) {
    mintingFinished = true;
    emit MintFinished();
    return true;
  }
}

// File: openzeppelin-solidity/contracts/token/ERC20/DetailedERC20.sol

pragma solidity ^0.4.24;



/**
 * @title DetailedERC20 token
 * @dev The decimals are only for visualization purposes.
 * All the operations are done using the smallest and indivisible token unit,
 * just as on Ethereum all the operations are done in wei.
 */
contract DetailedERC20 is ERC20 {
  string public name;
  string public symbol;
  uint8 public decimals;

  constructor(string _name, string _symbol, uint8 _decimals) public {
    name = _name;
    symbol = _symbol;
    decimals = _decimals;
  }
}

// File: openzeppelin-solidity/contracts/AddressUtils.sol

pragma solidity ^0.4.24;


/**
 * Utility library of inline functions on addresses
 */
library AddressUtils {

  /**
   * Returns whether the target address is a contract
   * @dev This function will return false if invoked during the constructor of a contract,
   * as the code is not actually created until after the constructor finishes.
   * @param _addr address to check
   * @return whether the target address is a contract
   */
  function isContract(address _addr) internal view returns (bool) {
    uint256 size;
    // XXX Currently there is no better way to check if there is a contract in an address
    // than to check the size of the code at that address.
    // See https://ethereum.stackexchange.com/a/14016/36603
    // for more details about how this works.
    // TODO Check this again before the Serenity release, because all addresses will be
    // contracts then.
    // solium-disable-next-line security/no-inline-assembly
    assembly { size := extcodesize(_addr) }
    return size > 0;
  }

}

// File: contracts/interfaces/ERC677.sol

pragma solidity 0.4.24;


contract ERC677 is ERC20 {
    event Transfer(address indexed from, address indexed to, uint256 value, bytes data);

    function transferAndCall(address, uint256, bytes) external returns (bool);

    function increaseAllowance(address spender, uint256 addedValue) public returns (bool);
    function decreaseAllowance(address spender, uint256 subtractedValue) public returns (bool);
}

contract LegacyERC20 {
    function transfer(address _spender, uint256 _value) public; // returns (bool);
    function transferFrom(address _owner, address _spender, uint256 _value) public; // returns (bool);
}

// File: contracts/interfaces/IBurnableMintableERC677Token.sol

pragma solidity 0.4.24;


contract IBurnableMintableERC677Token is ERC677 {
    function mint(address _to, uint256 _amount) public returns (bool);
    function burn(uint256 _value) public;
    function claimTokens(address _token, address _to) external;
}

// File: contracts/upgradeable_contracts/Sacrifice.sol

pragma solidity 0.4.24;

contract Sacrifice {
    constructor(address _recipient) public payable {
        selfdestruct(_recipient);
    }
}

// File: contracts/libraries/Address.sol

pragma solidity 0.4.24;


/**
 * @title Address
 * @dev Helper methods for Address type.
 */
library Address {
    /**
    * @dev Try to send native tokens to the address. If it fails, it will force the transfer by creating a selfdestruct contract
    * @param _receiver address that will receive the native tokens
    * @param _value the amount of native tokens to send
    */
    function safeSendValue(address _receiver, uint256 _value) internal {
        if (!_receiver.send(_value)) {
            (new Sacrifice).value(_value)(_receiver);
        }
    }
}

// File: contracts/libraries/SafeERC20.sol

pragma solidity 0.4.24;



/**
 * @title SafeERC20
 * @dev Helper methods for safe token transfers.
 * Functions perform additional checks to be sure that token transfer really happened.
 */
library SafeERC20 {
    using SafeMath for uint256;

    /**
    * @dev Same as ERC20.transfer(address,uint256) but with extra consistency checks.
    * @param _token address of the token contract
    * @param _to address of the receiver
    * @param _value amount of tokens to send
    */
    function safeTransfer(address _token, address _to, uint256 _value) internal {
        LegacyERC20(_token).transfer(_to, _value);
        assembly {
            if returndatasize {
                returndatacopy(0, 0, 32)
                if iszero(mload(0)) {
                    revert(0, 0)
                }
            }
        }
    }

    /**
    * @dev Same as ERC20.transferFrom(address,address,uint256) but with extra consistency checks.
    * @param _token address of the token contract
    * @param _from address of the sender
    * @param _value amount of tokens to send
    */
    function safeTransferFrom(address _token, address _from, uint256 _value) internal {
        LegacyERC20(_token).transferFrom(_from, address(this), _value);
        assembly {
            if returndatasize {
                returndatacopy(0, 0, 32)
                if iszero(mload(0)) {
                    revert(0, 0)
                }
            }
        }
    }
}

// File: contracts/upgradeable_contracts/Claimable.sol

pragma solidity 0.4.24;



/**
 * @title Claimable
 * @dev Implementation of the claiming utils that can be useful for withdrawing accidentally sent tokens that are not used in bridge operations.
 */
contract Claimable {
    using SafeERC20 for address;

    /**
     * Throws if a given address is equal to address(0)
     */
    modifier validAddress(address _to) {
        require(_to != address(0));
        /* solcov ignore next */
        _;
    }

    /**
     * @dev Withdraws the erc20 tokens or native coins from this contract.
     * Caller should additionally check that the claimed token is not a part of bridge operations (i.e. that token != erc20token()).
     * @param _token address of the claimed token or address(0) for native coins.
     * @param _to address of the tokens/coins receiver.
     */
    function claimValues(address _token, address _to) internal validAddress(_to) {
        if (_token == address(0)) {
            claimNativeCoins(_to);
        } else {
            claimErc20Tokens(_token, _to);
        }
    }

    /**
     * @dev Internal function for withdrawing all native coins from the contract.
     * @param _to address of the coins receiver.
     */
    function claimNativeCoins(address _to) internal {
        uint256 value = address(this).balance;
        Address.safeSendValue(_to, value);
    }

    /**
     * @dev Internal function for withdrawing all tokens of ssome particular ERC20 contract from this contract.
     * @param _token address of the claimed ERC20 token.
     * @param _to address of the tokens receiver.
     */
    function claimErc20Tokens(address _token, address _to) internal {
        ERC20Basic token = ERC20Basic(_token);
        uint256 balance = token.balanceOf(this);
        _token.safeTransfer(_to, balance);
    }
}

// File: contracts/ERC677BridgeToken.sol

pragma solidity 0.4.24;







/**
* @title ERC677BridgeToken
* @dev The basic implementation of a bridgeable ERC677-compatible token
*/
contract ERC677BridgeToken is IBurnableMintableERC677Token, DetailedERC20, BurnableToken, MintableToken, Claimable {
    bytes4 internal constant ON_TOKEN_TRANSFER = 0xa4c0ed36; // onTokenTransfer(address,uint256,bytes)

    address internal bridgeContractAddr;

    constructor(string _name, string _symbol, uint8 _decimals) public DetailedERC20(_name, _symbol, _decimals) {
        // solhint-disable-previous-line no-empty-blocks
    }

    function bridgeContract() external view returns (address) {
        return bridgeContractAddr;
    }

    function setBridgeContract(address _bridgeContract) external onlyOwner {
        require(AddressUtils.isContract(_bridgeContract));
        bridgeContractAddr = _bridgeContract;
    }

    modifier validRecipient(address _recipient) {
        require(_recipient != address(0) && _recipient != address(this));
        /* solcov ignore next */
        _;
    }

    function transferAndCall(address _to, uint256 _value, bytes _data) external validRecipient(_to) returns (bool) {
        require(superTransfer(_to, _value));
        emit Transfer(msg.sender, _to, _value, _data);

        if (AddressUtils.isContract(_to)) {
            require(contractFallback(msg.sender, _to, _value, _data));
        }
        return true;
    }

    function getTokenInterfacesVersion() external pure returns (uint64 major, uint64 minor, uint64 patch) {
        return (2, 5, 0);
    }

    function superTransfer(address _to, uint256 _value) internal returns (bool) {
        return super.transfer(_to, _value);
    }

    function transfer(address _to, uint256 _value) public returns (bool) {
        require(superTransfer(_to, _value));
        callAfterTransfer(msg.sender, _to, _value);
        return true;
    }

    function transferFrom(address _from, address _to, uint256 _value) public returns (bool) {
        require(super.transferFrom(_from, _to, _value));
        callAfterTransfer(_from, _to, _value);
        return true;
    }

    /**
     * @dev Internal function that calls onTokenTransfer callback on the receiver after the successful transfer.
     * Since it is not present in the original ERC677 standard, the callback is only called on the bridge contract,
     * in order to simplify UX. In other cases, this token complies with the ERC677/ERC20 standard.
     * @param _from tokens sender address.
     * @param _to tokens receiver address.
     * @param _value amount of sent tokens.
     */
    function callAfterTransfer(address _from, address _to, uint256 _value) internal {
        if (isBridge(_to)) {
            require(contractFallback(_from, _to, _value, new bytes(0)));
        }
    }

    function isBridge(address _address) public view returns (bool) {
        return _address == bridgeContractAddr;
    }

    /**
     * @dev call onTokenTransfer fallback on the token recipient contract
     * @param _from tokens sender
     * @param _to tokens recipient
     * @param _value amount of tokens that was sent
     * @param _data set of extra bytes that can be passed to the recipient
     */
    function contractFallback(address _from, address _to, uint256 _value, bytes _data) private returns (bool) {
        return _to.call(abi.encodeWithSelector(ON_TOKEN_TRANSFER, _from, _value, _data));
    }

    function finishMinting() public returns (bool) {
        revert();
    }

    function renounceOwnership() public onlyOwner {
        revert();
    }

    /**
     * @dev Withdraws the erc20 tokens or native coins from this contract.
     * @param _token address of the claimed token or address(0) for native coins.
     * @param _to address of the tokens/coins receiver.
     */
    function claimTokens(address _token, address _to) external onlyOwner {
        claimValues(_token, _to);
    }

    function increaseAllowance(address spender, uint256 addedValue) public returns (bool) {
        return super.increaseApproval(spender, addedValue);
    }

    function decreaseAllowance(address spender, uint256 subtractedValue) public returns (bool) {
        return super.decreaseApproval(spender, subtractedValue);
    }
}

// File: contracts/PermittableToken.sol

pragma solidity 0.4.24;


contract PermittableToken is ERC677BridgeToken {
    string public constant version = "1";

    // EIP712 niceties
    bytes32 public DOMAIN_SEPARATOR;
    // bytes32 public constant PERMIT_TYPEHASH_LEGACY = keccak256("Permit(address holder,address spender,uint256 nonce,uint256 expiry,bool allowed)");
    bytes32 public constant PERMIT_TYPEHASH_LEGACY = 0xea2aa0a1be11a07ed86d755c93467f4f82362b452371d1ba94d1715123511acb;
    // bytes32 public constant PERMIT_TYPEHASH = keccak256("Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)");
    bytes32 public constant PERMIT_TYPEHASH = 0x6e71edae12b1b97f4d1f60370fef10105fa2faae0126114a169c64845d6126c9;

    mapping(address => uint256) public nonces;
    mapping(address => mapping(address => uint256)) public expirations;

    constructor(string memory _name, string memory _symbol, uint8 _decimals, uint256 _chainId)
        public
        ERC677BridgeToken(_name, _symbol, _decimals)
    {
        require(_chainId != 0);
        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
                keccak256(bytes(_name)),
                keccak256(bytes(version)),
                _chainId,
                address(this)
            )
        );
    }

    /// @dev transferFrom in this contract works in a slightly different form than the generic
    /// transferFrom function. This contract allows for "unlimited approval".
    /// Should the user approve an address for the maximum uint256 value,
    /// then that address will have unlimited approval until told otherwise.
    /// @param _sender The address of the sender.
    /// @param _recipient The address of the recipient.
    /// @param _amount The value to transfer.
    /// @return Success status.
    function transferFrom(address _sender, address _recipient, uint256 _amount) public returns (bool) {
        require(_sender != address(0));
        require(_recipient != address(0));

        balances[_sender] = balances[_sender].sub(_amount);
        balances[_recipient] = balances[_recipient].add(_amount);
        emit Transfer(_sender, _recipient, _amount);

        if (_sender != msg.sender) {
            uint256 allowedAmount = allowance(_sender, msg.sender);

            if (allowedAmount != uint256(-1)) {
                // If allowance is limited, adjust it.
                // In this case `transferFrom` works like the generic
                allowed[_sender][msg.sender] = allowedAmount.sub(_amount);
                emit Approval(_sender, msg.sender, allowed[_sender][msg.sender]);
            } else {
                // If allowance is unlimited by `permit`, `approve`, or `increaseAllowance`
                // function, don't adjust it. But the expiration date must be empty or in the future
                require(expirations[_sender][msg.sender] == 0 || expirations[_sender][msg.sender] >= now);
            }
        } else {
            // If `_sender` is `msg.sender`,
            // the function works just like `transfer()`
        }

        callAfterTransfer(_sender, _recipient, _amount);
        return true;
    }

    /// @dev Approve the passed address to spend the specified amount of tokens on behalf of msg.sender.
    /// @param _to The address which will spend the funds.
    /// @param _value The amount of tokens to be spent.
    function approve(address _to, uint256 _value) public returns (bool result) {
        _approveAndResetExpirations(msg.sender, _to, _value);
        return true;
    }

    /// @dev Atomically increases the allowance granted to spender by the caller.
    /// @param _to The address which will spend the funds.
    /// @param _addedValue The amount of tokens to increase the allowance by.
    function increaseAllowance(address _to, uint256 _addedValue) public returns (bool result) {
        _approveAndResetExpirations(msg.sender, _to, allowed[msg.sender][_to].add(_addedValue));
        return true;
    }

    /// @dev An alias for `transfer` function.
    /// @param _to The address of the recipient.
    /// @param _amount The value to transfer.
    function push(address _to, uint256 _amount) public {
        transferFrom(msg.sender, _to, _amount);
    }

    /// @dev Makes a request to transfer the specified amount
    /// from the specified address to the caller's address.
    /// @param _from The address of the holder.
    /// @param _amount The value to transfer.
    function pull(address _from, uint256 _amount) public {
        transferFrom(_from, msg.sender, _amount);
    }

    /// @dev An alias for `transferFrom` function.
    /// @param _from The address of the sender.
    /// @param _to The address of the recipient.
    /// @param _amount The value to transfer.
    function move(address _from, address _to, uint256 _amount) public {
        transferFrom(_from, _to, _amount);
    }

    /// @dev Allows to spend holder's unlimited amount by the specified spender.
    /// The function can be called by anyone, but requires having allowance parameters
    /// signed by the holder according to EIP712.
    /// @param _holder The holder's address.
    /// @param _spender The spender's address.
    /// @param _nonce The nonce taken from `nonces(_holder)` public getter.
    /// @param _expiry The allowance expiration date (unix timestamp in UTC).
    /// Can be zero for no expiration. Forced to zero if `_allowed` is `false`.
    /// Note that timestamps are not precise, malicious miner/validator can manipulate them to some extend.
    /// Assume that there can be a 900 seconds time delta between the desired timestamp and the actual expiration.
    /// @param _allowed True to enable unlimited allowance for the spender by the holder. False to disable.
    /// @param _v A final byte of signature (ECDSA component).
    /// @param _r The first 32 bytes of signature (ECDSA component).
    /// @param _s The second 32 bytes of signature (ECDSA component).
    function permit(
        address _holder,
        address _spender,
        uint256 _nonce,
        uint256 _expiry,
        bool _allowed,
        uint8 _v,
        bytes32 _r,
        bytes32 _s
    ) external {
        require(_expiry == 0 || now <= _expiry);

        bytes32 digest = _digest(abi.encode(PERMIT_TYPEHASH_LEGACY, _holder, _spender, _nonce, _expiry, _allowed));

        require(_holder == _recover(digest, _v, _r, _s));
        require(_nonce == nonces[_holder]++);

        uint256 amount = _allowed ? uint256(-1) : 0;

        expirations[_holder][_spender] = _allowed ? _expiry : 0;

        _approve(_holder, _spender, amount);
    }

    /** @dev Allows to spend holder's unlimited amount by the specified spender according to EIP2612.
     * The function can be called by anyone, but requires having allowance parameters
     * signed by the holder according to EIP712.
     * @param _holder The holder's address.
     * @param _spender The spender's address.
     * @param _value Allowance value to set as a result of the call.
     * @param _deadline The deadline timestamp to call the permit function. Must be a timestamp in the future.
     * Note that timestamps are not precise, malicious miner/validator can manipulate them to some extend.
     * Assume that there can be a 900 seconds time delta between the desired timestamp and the actual expiration.
     * @param _v A final byte of signature (ECDSA component).
     * @param _r The first 32 bytes of signature (ECDSA component).
     * @param _s The second 32 bytes of signature (ECDSA component).
     */
    function permit(
        address _holder,
        address _spender,
        uint256 _value,
        uint256 _deadline,
        uint8 _v,
        bytes32 _r,
        bytes32 _s
    ) external {
        require(now <= _deadline);

        uint256 nonce = nonces[_holder]++;
        bytes32 digest = _digest(abi.encode(PERMIT_TYPEHASH, _holder, _spender, _value, nonce, _deadline));

        require(_holder == _recover(digest, _v, _r, _s));

        _approveAndResetExpirations(_holder, _spender, _value);
    }

    /**
     * @dev Sets a new allowance value for the given owner and spender addresses.
     * Resets expiration timestamp in case of unlimited approval.
     * @param _owner address tokens holder.
     * @param _spender address of tokens spender.
     * @param _amount amount of approved tokens.
     */
    function _approveAndResetExpirations(address _owner, address _spender, uint256 _amount) internal {
        _approve(_owner, _spender, _amount);

        // it is not necessary to reset _expirations in other cases, since it is only used together with infinite allowance
        if (_amount == uint256(-1)) {
            delete expirations[_owner][_spender];
        }
    }

    /**
     * @dev Internal function for issuing an allowance.
     * @param _owner address of the tokens owner.
     * @param _spender address of the approved tokens spender.
     * @param _amount amount of the approved tokens.
     */
    function _approve(address _owner, address _spender, uint256 _amount) internal {
        require(_owner != address(0), "ERC20: approve from the zero address");
        require(_spender != address(0), "ERC20: approve to the zero address");

        allowed[_owner][_spender] = _amount;
        emit Approval(_owner, _spender, _amount);
    }

    /**
     * @dev Calculates the message digest for encoded EIP712 typed struct.
     * @param _typedStruct encoded payload.
     */
    function _digest(bytes memory _typedStruct) internal view returns (bytes32) {
        return keccak256(abi.encodePacked("\x19\x01", DOMAIN_SEPARATOR, keccak256(_typedStruct)));
    }

    /**
     * @dev Derives the signer address for the given message digest and ECDSA signature params.
     * @param _digest signed message digest.
     * @param _v a final byte of signature (ECDSA component).
     * @param _r the first 32 bytes of the signature (ECDSA component).
     * @param _s the second 32 bytes of the signature (ECDSA component).
     */
    function _recover(bytes32 _digest, uint8 _v, bytes32 _r, bytes32 _s) internal pure returns (address) {
        require(_v == 27 || _v == 28, "ECDSA: invalid signature 'v' value");
        require(
            uint256(_s) <= 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0,
            "ECDSA: invalid signature 's' value"
        );

        address signer = ecrecover(_digest, _v, _r, _s);
        require(signer != address(0), "ECDSA: invalid signature");

        return signer;
    }
}