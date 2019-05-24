pragma solidity ^0.4.18;

// File: contracts/EtherDeltaI.sol

contract EtherDeltaI {

  uint public feeMake; //percentage times (1 ether)
  uint public feeTake; //percentage times (1 ether)

  mapping (address => mapping (address => uint)) public tokens; //mapping of token addresses to mapping of account balances (token=0 means Ether)
  mapping (address => mapping (bytes32 => bool)) public orders; //mapping of user accounts to mapping of order hashes to booleans (true = submitted by user, equivalent to offchain signature)
  mapping (address => mapping (bytes32 => uint)) public orderFills; //mapping of user accounts to mapping of order hashes to uints (amount of order that has been filled)

  function deposit() payable;

  function withdraw(uint amount);

  function depositToken(address token, uint amount);

  function withdrawToken(address token, uint amount);

  function balanceOf(address token, address user) constant returns (uint);

  function order(address tokenGet, uint amountGet, address tokenGive, uint amountGive, uint expires, uint nonce);

  function trade(address tokenGet, uint amountGet, address tokenGive, uint amountGive, uint expires, uint nonce, address user, uint8 v, bytes32 r, bytes32 s, uint amount);

  function testTrade(address tokenGet, uint amountGet, address tokenGive, uint amountGive, uint expires, uint nonce, address user, uint8 v, bytes32 r, bytes32 s, uint amount, address sender) constant returns(bool);

  function availableVolume(address tokenGet, uint amountGet, address tokenGive, uint amountGive, uint expires, uint nonce, address user, uint8 v, bytes32 r, bytes32 s) constant returns(uint);

  function amountFilled(address tokenGet, uint amountGet, address tokenGive, uint amountGive, uint expires, uint nonce, address user, uint8 v, bytes32 r, bytes32 s) constant returns(uint);

  function cancelOrder(address tokenGet, uint amountGet, address tokenGive, uint amountGive, uint expires, uint nonce, uint8 v, bytes32 r, bytes32 s);

}

// File: contracts/KindMath.sol

/**
 * @title KindMath
 * @dev Math operations with safety checks that fail
 */
library KindMath {
  function mul(uint256 a, uint256 b) internal pure returns (uint256) {
    uint256 c = a * b;
    require(a == 0 || c / a == b);
    return c;
  }

  function div(uint256 a, uint256 b) internal pure returns (uint256) {
    // assert(b > 0); // Solidity automatically throws when dividing by 0
    uint256 c = a / b;
    // assert(a == b * c + a % b); // There is no case in which this doesn't hold
    return c;
  }

  function sub(uint256 a, uint256 b) internal pure returns (uint256) {
    require(b <= a);
    return a - b;
  }

  function add(uint256 a, uint256 b) internal pure returns (uint256) {
    uint256 c = a + b;
    require(c >= a);
    return c;
  }
}

// File: contracts/KeyValueStorage.sol

contract KeyValueStorage {

  mapping(address => mapping(bytes32 => uint256)) _uintStorage;
  mapping(address => mapping(bytes32 => address)) _addressStorage;
  mapping(address => mapping(bytes32 => bool)) _boolStorage;
  mapping(address => mapping(bytes32 => bytes32)) _bytes32Storage;

  /**** Get Methods ***********/

  function getAddress(bytes32 key) public view returns (address) {
      return _addressStorage[msg.sender][key];
  }

  function getUint(bytes32 key) public view returns (uint) {
      return _uintStorage[msg.sender][key];
  }

  function getBool(bytes32 key) public view returns (bool) {
      return _boolStorage[msg.sender][key];
  }

  function getBytes32(bytes32 key) public view returns (bytes32) {
      return _bytes32Storage[msg.sender][key];
  }

  /**** Set Methods ***********/

  function setAddress(bytes32 key, address value) public {
      _addressStorage[msg.sender][key] = value;
  }

  function setUint(bytes32 key, uint value) public {
      _uintStorage[msg.sender][key] = value;
  }

  function setBool(bytes32 key, bool value) public {
      _boolStorage[msg.sender][key] = value;
  }

  function setBytes32(bytes32 key, bytes32 value) public {
      _bytes32Storage[msg.sender][key] = value;
  }

  /**** Delete Methods ***********/

  function deleteAddress(bytes32 key) public {
      delete _addressStorage[msg.sender][key];
  }

  function deleteUint(bytes32 key) public {
      delete _uintStorage[msg.sender][key];
  }

  function deleteBool(bytes32 key) public {
      delete _boolStorage[msg.sender][key];
  }

  function deleteBytes32(bytes32 key) public {
      delete _bytes32Storage[msg.sender][key];
  }

}

// File: contracts/StorageStateful.sol

contract StorageStateful {
  KeyValueStorage public keyValueStorage;
}

// File: contracts/StorageConsumer.sol

contract StorageConsumer is StorageStateful {
  function StorageConsumer(address _storageAddress) public {
    require(_storageAddress != address(0));
    keyValueStorage = KeyValueStorage(_storageAddress);
  }
}

// File: contracts/TokenI.sol

contract Token {
  /// @return total amount of tokens
  function totalSupply() public returns (uint256);

  /// @param _owner The address from which the balance will be retrieved
  /// @return The balance
  function balanceOf(address _owner) public returns (uint256);

  /// @notice send `_value` token to `_to` from `msg.sender`
  /// @param _to The address of the recipient
  /// @param _value The amount of token to be transferred
  /// @return Whether the transfer was successful or not
  function transfer(address _to, uint256 _value) public returns (bool);

  /// @notice send `_value` token to `_to` from `_from` on the condition it is approved by `_from`
  /// @param _from The address of the sender
  /// @param _to The address of the recipient
  /// @param _value The amount of token to be transferred
  /// @return Whether the transfer was successful or not
  function transferFrom(address _from, address _to, uint256 _value) public returns (bool);

  /// @notice `msg.sender` approves `_addr` to spend `_value` tokens
  /// @param _spender The address of the account able to transfer the tokens
  /// @param _value The amount of wei to be approved for transfer
  /// @return Whether the approval was successful or not
  function approve(address _spender, uint256 _value) public returns (bool);

  /// @param _owner The address of the account owning tokens
  /// @param _spender The address of the account able to transfer the tokens
  /// @return Amount of remaining tokens allowed to spent
  function allowance(address _owner, address _spender) public returns (uint256);

  event Transfer(address indexed _from, address indexed _to, uint256 _value);
  event Approval(address indexed _owner, address indexed _spender, uint256 _value);

  uint256 public decimals;
  string public name;
}

// File: contracts/EnclavesDEXProxy.sol

contract EnclavesDEXProxy is StorageConsumer {
  using KindMath for uint256;

  address public admin; //the admin address
  address public feeAccount; //the account that will receive fees

  struct EtherDeltaInfo {
    uint256 feeMake;
    uint256 feeTake;
  }

  EtherDeltaInfo public etherDeltaInfo;

  uint256 public feeTake; //percentage times 1 ether
  uint256 public feeAmountThreshold; //gasPrice amount under which no fees are charged

  address public etherDelta;

  bool public useEIP712 = true;
  bytes32 public tradeABIHash;
  bytes32 public withdrawABIHash;

  bool freezeTrading;
  bool depositTokenLock;

  mapping (address => mapping (uint256 => bool)) nonceCheck;

  mapping (address => mapping (address => uint256)) public tokens; //mapping of token addresses to mapping of account balances (token=0 means Ether)
  mapping (address => mapping (bytes32 => bool)) public orders; //mapping of user accounts to mapping of order hashes to booleans (true = submitted by user, equivalent to offchain signature)
  mapping (address => mapping (bytes32 => uint256)) public orderFills; //mapping of user accounts to mapping of order hashes to uints (amount of order that has been filled)

  address internal implementation;
  address public proposedImplementation;
  uint256 public proposedTimestamp;

  event Upgraded(address _implementation);
  event UpgradedProposed(address _proposedImplementation, uint256 _proposedTimestamp);

  modifier onlyAdmin {
    require(msg.sender == admin);
    _;
  }

  function EnclavesDEXProxy(address _storageAddress, address _implementation, address _admin, address _feeAccount, uint256 _feeTake, uint256 _feeAmountThreshold, address _etherDelta, bytes32 _tradeABIHash, bytes32 _withdrawABIHash) public
    StorageConsumer(_storageAddress)
  {
    require(_implementation != address(0));
    implementation = _implementation;
    admin = _admin;
    feeAccount = _feeAccount;
    feeTake = _feeTake;
    feeAmountThreshold = _feeAmountThreshold;
    etherDelta = _etherDelta;
    tradeABIHash = _tradeABIHash;
    withdrawABIHash = _withdrawABIHash;
    etherDeltaInfo.feeMake = EtherDeltaI(etherDelta).feeMake();
    etherDeltaInfo.feeTake = EtherDeltaI(etherDelta).feeTake();
  }

  function getImplementation() public view returns(address) {
    return implementation;
  }

  function proposeUpgrade(address _proposedImplementation) public onlyAdmin {
    require(implementation != _proposedImplementation);
    require(_proposedImplementation != address(0));
    proposedImplementation = _proposedImplementation;
    proposedTimestamp = now + 2 weeks;
    UpgradedProposed(proposedImplementation, now);
  }

  function upgrade() public onlyAdmin {
    require(proposedImplementation != address(0));
    require(proposedTimestamp < now);
    implementation = proposedImplementation;
    Upgraded(implementation);
  }

  function () payable public {
    bytes memory data = msg.data;
    address impl = getImplementation();

    assembly {
      let result := delegatecall(gas, impl, add(data, 0x20), mload(data), 0, 0)
      let size := returndatasize
      let ptr := mload(0x40)
      returndatacopy(ptr, 0, size)
      switch result
      case 0 { revert(ptr, size) }
      default { return(ptr, size) }
    }
  }

}