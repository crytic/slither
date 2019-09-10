pragma solidity ^0.4.17;

contract Cofounded {
  mapping (address => uint) public cofounderIndices;
  address[] public cofounders;


  /// @dev restrict execution to one of original cofounder addresses
  modifier restricted () {
    uint cofounderIndex = cofounderIndices[msg.sender];
    require(msg.sender == cofounders[cofounderIndex]);
    _;
  }

  /// @notice creates the Cofounded contract instance
  /// @dev adds up to cofounders.
  ///      also adds  the deployment address as a cofounder
  function Cofounded (address[] contractCofounders) public {
    cofounders.push(msg.sender);
    
    for (uint8 x = 0; x < contractCofounders.length; x++) {
      address cofounder = contractCofounders[x];

      bool isValidUniqueCofounder =
        cofounder != address(0) &&
        cofounder != msg.sender &&
        cofounderIndices[cofounder] == 0;

            
      // NOTE: solidity as of 0.4.20 does not have an
      // undefined or null-like value
      // thusly mappings return the default value of the value type
      // for an unregistered key value
      // an address which doesn't exist will return 0
      // which is actually the index of the address of the first
      // cofounder
      if (isValidUniqueCofounder) {
        uint256 cofounderIndex = cofounders.push(cofounder) - 1;
        cofounderIndices[cofounder] = cofounderIndex;
      }
    }
  }

  /// @dev get count of cofounders
  function getCofounderCount () public constant returns (uint256) {
    return cofounders.length;
  }

  /// @dev get list of cofounders
  function getCofounders () public constant returns (address[]) {
    return cofounders;
  }
}

interface ERC20 {

  // Required methods
  function transfer (address to, uint256 value) public returns (bool success);
  function transferFrom (address from, address to, uint256 value) public returns (bool success);
  function approve (address spender, uint256 value) public returns (bool success);
  function allowance (address owner, address spender) public constant returns (uint256 remaining);
  function balanceOf (address owner) public constant returns (uint256 balance);
  // Events
  event Transfer (address indexed from, address indexed to, uint256 value);
  event Approval (address indexed owner, address indexed spender, uint256 value);
}


/// @title Interface for contracts conforming to ERC-165: Pseudo-Introspection, or standard interface detection
/// @author Mish Ochu
interface ERC165 {
  /// @dev true iff the interface is supported
  function supportsInterface(bytes4 interfaceID) external constant returns (bool);
}
contract InterfaceSignatureConstants {
  bytes4 constant InterfaceSignature_ERC165 =
    bytes4(keccak256('supportsInterface(bytes4)'));

  bytes4 constant InterfaceSignature_ERC20 =
    bytes4(keccak256('totalSupply()')) ^
    bytes4(keccak256('balanceOf(address)')) ^
    bytes4(keccak256('transfer(address,uint256)')) ^
    bytes4(keccak256('transferFrom(address,address,uint256)')) ^
    bytes4(keccak256('approve(address,uint256)')) ^
    bytes4(keccak256('allowance(address,address)'));

  bytes4 constant InterfaceSignature_ERC20_PlusOptions = 
    bytes4(keccak256('name()')) ^
    bytes4(keccak256('symbol()')) ^
    bytes4(keccak256('decimals()')) ^
    bytes4(keccak256('totalSupply()')) ^
    bytes4(keccak256('balanceOf(address)')) ^
    bytes4(keccak256('transfer(address,uint256)')) ^
    bytes4(keccak256('transferFrom(address,address,uint256)')) ^
    bytes4(keccak256('approve(address,uint256)')) ^
    bytes4(keccak256('allowance(address,address)'));
}

/// @title an original cofounder based ERC-20 compliant token
/// @author Mish Ochu
/// @dev Ref: https://github.com/ethereum/EIPs/issues/721
//http://solidity.readthedocs.io/en/develop/contracts.html#arguments-for-base-constructors
contract OriginalToken is Cofounded, ERC20, ERC165, InterfaceSignatureConstants {
    bool private hasExecutedCofounderDistribution;
    struct Allowance {
      uint256 amount;
      bool    hasBeenPartiallyWithdrawn;
    }

    //***** Apparently Optional *****/
    /// @dev returns the name of the token
    string public constant name = 'Original Crypto Coin';
    /// @dev returns the symbol of the token (e.g. 'OCC')
    string public constant symbol = 'OCC';
    /// @dev returns the number of decimals the tokens use
    uint8 public constant decimals = 18;
    //**********/

    /// @dev  returns the total token supply
    /// @note implemented as a state variable with an automatic (compiler provided) getter
    ///       instead of a constant (view/readonly) function.
    uint256 public totalSupply = 100000000000000000000000000000;

    mapping (address => uint256) public balances;
    // TODO: determine if the gas cost for handling the race condition
    //       (outlined here: https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729)
    //       is cheaper this way (or this way: https://github.com/Giveth/minime/blob/master/contracts/MiniMeToken.sol#L221-L225)
    mapping (address => mapping (address => Allowance)) public allowances;

  /// @dev creates the token
  /// NOTE  passes tokenCofounders to base contract
  /// see   Cofounded
  function OriginalToken (address[] tokenCofounders,
                          uint256 cofounderDistribution) Cofounded(tokenCofounders) public { 

    if (hasExecutedCofounderDistribution ||
        cofounderDistribution == 0 || 
        totalSupply < cofounderDistribution) revert();

    hasExecutedCofounderDistribution = true;
    uint256 initialSupply = totalSupply;

    // divvy up initial token supply accross cofounders
    // TODO: ensure each cofounder gets an equal base distribution

    for (uint8 x = 0; x < cofounders.length; x++) {
      address cofounder = cofounders[x];

      initialSupply -= cofounderDistribution;
      // there should be some left over for the airdrop campaign
      // otherwise don't create this contract
      if (initialSupply < cofounderDistribution) revert();
      balances[cofounder] = cofounderDistribution;
    }

    balances[msg.sender] += initialSupply;
  }

  function transfer (address to, uint256 value) public returns (bool) {
    return transferBalance (msg.sender, to, value);
  }

  function transferFrom (address from, address to, uint256 value) public returns (bool success) {
    Allowance storage allowance = allowances[from][msg.sender];
    if (allowance.amount < value) revert();

    allowance.hasBeenPartiallyWithdrawn = true;
    allowance.amount -= value;

    if (allowance.amount == 0) {
      delete allowances[from][msg.sender];
    }

    return transferBalance(from, to, value);
  }

  event ApprovalDenied (address indexed owner, address indexed spender);

  // TODO: test with an unintialized Allowance struct
  function approve (address spender, uint256 value) public returns (bool success) {
    Allowance storage allowance = allowances[msg.sender][spender];

    if (value == 0) {
      delete allowances[msg.sender][spender];
      Approval(msg.sender, spender, value);
      return true;
    }

    if (allowance.hasBeenPartiallyWithdrawn) {
      delete allowances[msg.sender][spender];
      ApprovalDenied(msg.sender, spender);
      return false;
    } else {
      allowance.amount = value;
      Approval(msg.sender, spender, value);
    }

    return true;
  }

  // TODO: compare gas cost estimations between this and https://github.com/ConsenSys/Tokens/blob/master/contracts/eip20/EIP20.sol#L39-L45
  function transferBalance (address from, address to, uint256 value) private returns (bool) {
    // don't burn these tokens
    if (to == address(0) || from == to) revert();
    // match spec and emit events on 0 value
    if (value == 0) {
      Transfer(msg.sender, to, value);
      return true;
    }

    uint256 senderBalance = balances[from];
    uint256 receiverBalance = balances[to];
    if (senderBalance < value) revert();
    senderBalance -= value;
    receiverBalance += value;
    // overflow check (altough one could use https://github.com/OpenZeppelin/zeppelin-solidity/blob/master/contracts/math/SafeMath.sol)
    if (receiverBalance < value) revert();

    balances[from] = senderBalance;
    balances[to] = receiverBalance;

    Transfer(from, to, value);
    return true;
  }

 
  // TODO: test with an unintialized Allowance struct
  function allowance (address owner, address spender) public constant returns (uint256 remaining) {
    return allowances[owner][spender].amount;
  }

  function balanceOf (address owner) public constant returns (uint256 balance) {
    return balances[owner];
  }

  function supportsInterface (bytes4 interfaceID) external constant returns (bool) {
    return ((interfaceID == InterfaceSignature_ERC165) ||
            (interfaceID == InterfaceSignature_ERC20)  ||
            (interfaceID == InterfaceSignature_ERC20_PlusOptions));
  }
}