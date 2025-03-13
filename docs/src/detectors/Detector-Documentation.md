# Public Detectors

List of public detectors

## Storage ABIEncoderV2 Array

### Configuration

- Check: `abiencoderv2-array`
- Severity: `High`
- Confidence: `High`

### Description

`solc` versions `0.4.7`-`0.5.9` contain a [compiler bug](https://blog.ethereum.org/2019/06/25/solidity-storage-array-bugs) leading to incorrect ABI encoder usage.

### Exploit Scenario:

```solidity
contract A {
    uint[2][3] bad_arr = [[1, 2], [3, 4], [5, 6]];

    /* Array of arrays passed to abi.encode is vulnerable */
    function bad() public {
        bytes memory b = abi.encode(bad_arr);
    }
}
```

`abi.encode(bad_arr)` in a call to `bad()` will incorrectly encode the array as `[[1, 2], [2, 3], [3, 4]]` and lead to unintended behavior.

### Recommendation

Use a compiler >= `0.5.10`.

## Arbitrary `from` in transferFrom

### Configuration

- Check: `arbitrary-send-erc20`
- Severity: `High`
- Confidence: `High`

### Description

Detect when `msg.sender` is not used as `from` in transferFrom.

### Exploit Scenario:

```solidity
    function a(address from, address to, uint256 amount) public {
        erc20.transferFrom(from, to, am);
    }
```

Alice approves this contract to spend her ERC20 tokens. Bob can call `a` and specify Alice's address as the `from` parameter in `transferFrom`, allowing him to transfer Alice's tokens to himself.

### Recommendation

Use `msg.sender` as `from` in transferFrom.

## Modifying storage array by value

### Configuration

- Check: `array-by-reference`
- Severity: `High`
- Confidence: `High`

### Description

Detect arrays passed to a function that expects reference to a storage array

### Exploit Scenario:

```solidity
contract Memory {
    uint[1] public x; // storage

    function f() public {
        f1(x); // update x
        f2(x); // do not update x
    }

    function f1(uint[1] storage arr) internal { // by reference
        arr[0] = 1;
    }

    function f2(uint[1] arr) internal { // by value
        arr[0] = 2;
    }
}
```

Bob calls `f()`. Bob assumes that at the end of the call `x[0]` is 2, but it is 1.
As a result, Bob's usage of the contract is incorrect.

### Recommendation

Ensure the correct usage of `memory` and `storage` in the function parameters. Make all the locations explicit.

## ABI encodePacked Collision

### Configuration

- Check: `encode-packed-collision`
- Severity: `High`
- Confidence: `High`

### Description

Detect collision due to dynamic type usages in `abi.encodePacked`

### Exploit Scenario:

```solidity
contract Sign {
    function get_hash_for_signature(string name, string doc) external returns(bytes32) {
        return keccak256(abi.encodePacked(name, doc));
    }
}
```

Bob calls `get_hash_for_signature` with (`bob`, `This is the content`). The hash returned is used as an ID.
Eve creates a collision with the ID using (`bo`, `bThis is the content`) and compromises the system.

### Recommendation

Do not use more than one dynamic type in `abi.encodePacked()`
(see the [Solidity documentation](https://solidity.readthedocs.io/en/v0.5.10/abi-spec.html?highlight=abi.encodePacked#non-standard-packed-modeDynamic)).
Use `abi.encode()`, preferably.

## Incorrect shift in assembly.

### Configuration

- Check: `incorrect-shift`
- Severity: `High`
- Confidence: `High`

### Description

Detect if the values in a shift operation are reversed

### Exploit Scenario:

```solidity
contract C {
    function f() internal returns (uint a) {
        assembly {
            a := shr(a, 8)
        }
    }
}
```

The shift statement will right-shift the constant 8 by `a` bits

### Recommendation

Swap the order of parameters.

## Multiple constructor schemes

### Configuration

- Check: `multiple-constructors`
- Severity: `High`
- Confidence: `High`

### Description

Detect multiple constructor definitions in the same contract (using new and old schemes).

### Exploit Scenario:

```solidity
contract A {
    uint x;
    constructor() public {
        x = 0;
    }
    function A() public {
        x = 1;
    }

    function test() public returns(uint) {
        return x;
    }
}
```

In Solidity [0.4.22](https://github.com/ethereum/solidity/releases/tag/v0.4.23), a contract with both constructor schemes will compile. The first constructor will take precedence over the second, which may be unintended.

### Recommendation

Only declare one constructor, preferably using the new scheme `constructor(...)` instead of `function <contractName>(...)`.

## Name reused

### Configuration

- Check: `name-reused`
- Severity: `High`
- Confidence: `High`

### Description

If a codebase has two contracts the similar names, the compilation artifacts
will not contain one of the contracts with the duplicate name.

### Exploit Scenario:

Bob's `truffle` codebase has two contracts named `ERC20`.
When `truffle compile` runs, only one of the two contracts will generate artifacts in `build/contracts`.
As a result, the second contract cannot be analyzed.

### Recommendation

Rename the contract.

## Protected Variables

### Configuration

- Check: `protected-vars`
- Severity: `High`
- Confidence: `High`

### Description

Detect unprotected variable that are marked protected

### Exploit Scenario:

```solidity
contract Buggy{

    /// @custom:security write-protection="onlyOwner()"
    address owner;

    function set_protected() public onlyOwner(){
        owner = msg.sender;
    }

    function set_not_protected() public{
        owner = msg.sender;
    }
}
```

`owner` must be always written by function using `onlyOwner` (`write-protection="onlyOwner()"`), however anyone can call `set_not_protected`.

### Recommendation

Add access controls to the vulnerable function

## Public mappings with nested variables

### Configuration

- Check: `public-mappings-nested`
- Severity: `High`
- Confidence: `High`

### Description

Prior to Solidity 0.5, a public mapping with nested structures returned [incorrect values](https://github.com/ethereum/solidity/issues/5520).

### Exploit Scenario:

Bob interacts with a contract that has a public mapping with nested structures. The values returned by the mapping are incorrect, breaking Bob's usage

### Recommendation

Do not use public mapping with nested structures.

## Right-to-Left-Override character

### Configuration

- Check: `rtlo`
- Severity: `High`
- Confidence: `High`

### Description

An attacker can manipulate the logic of the contract by using a right-to-left-override character (`U+202E)`.

### Exploit Scenario:

```solidity
contract Token
{

    address payable o; // owner
    mapping(address => uint) tokens;

    function withdraw() external returns(uint)
    {
        uint amount = tokens[msg.sender];
        address payable d = msg.sender;
        tokens[msg.sender] = 0;
        _withdraw(/*owner‮/*noitanitsed*/ d, o/*‭
		        /*value */, amount);
    }

    function _withdraw(address payable fee_receiver, address payable destination, uint value) internal
    {
		fee_receiver.transfer(1);
		destination.transfer(value);
    }
}
```

`Token` uses the right-to-left-override character when calling `_withdraw`. As a result, the fee is incorrectly sent to `msg.sender`, and the token balance is sent to the owner.

### Recommendation

Special control characters must not be allowed.

## State variable shadowing

### Configuration

- Check: `shadowing-state`
- Severity: `High`
- Confidence: `High`

### Description

Detection of state variables shadowed.

### Exploit Scenario:

```solidity
contract BaseContract{
    address owner;

    modifier isOwner(){
        require(owner == msg.sender);
        _;
    }

}

contract DerivedContract is BaseContract{
    address owner;

    constructor(){
        owner = msg.sender;
    }

    function withdraw() isOwner() external{
        msg.sender.transfer(this.balance);
    }
}
```

`owner` of `BaseContract` is never assigned and the modifier `isOwner` does not work.

### Recommendation

Remove the state variable shadowing.

## Suicidal

### Configuration

- Check: `suicidal`
- Severity: `High`
- Confidence: `High`

### Description

Unprotected call to a function executing `selfdestruct`/`suicide`.

### Exploit Scenario:

```solidity
contract Suicidal{
    function kill() public{
        selfdestruct(msg.sender);
    }
}
```

Bob calls `kill` and destructs the contract.

### Recommendation

Protect access to all sensitive functions.

## Uninitialized state variables

### Configuration

- Check: `uninitialized-state`
- Severity: `High`
- Confidence: `High`

### Description

Uninitialized state variables.

### Exploit Scenario:

```solidity
contract Uninitialized{
    address destination;

    function transfer() payable public{
        destination.transfer(msg.value);
    }
}
```

Bob calls `transfer`. As a result, the Ether are sent to the address `0x0` and are lost.

### Recommendation

Initialize all the variables. If a variable is meant to be initialized to zero, explicitly set it to zero to improve code readability.

## Uninitialized storage variables

### Configuration

- Check: `uninitialized-storage`
- Severity: `High`
- Confidence: `High`

### Description

An uninitialized storage variable will act as a reference to the first state variable, and can override a critical variable.

### Exploit Scenario:

```solidity
contract Uninitialized{
    address owner = msg.sender;

    struct St{
        uint a;
    }

    function func() {
        St st;
        st.a = 0x0;
    }
}
```

Bob calls `func`. As a result, `owner` is overridden to `0`.

### Recommendation

Initialize all storage variables.

## Unprotected upgradeable contract

### Configuration

- Check: `unprotected-upgrade`
- Severity: `High`
- Confidence: `High`

### Description

Detects logic contract that can be destructed.

### Exploit Scenario:

```solidity
contract Buggy is Initializable{
    address payable owner;

    function initialize() external initializer{
        require(owner == address(0));
        owner = msg.sender;
    }
    function kill() external{
        require(msg.sender == owner);
        selfdestruct(owner);
    }
}
```

Buggy is an upgradeable contract. Anyone can call initialize on the logic contract, and destruct the contract.

### Recommendation

Add a constructor to ensure `initialize` cannot be called on the logic contract.

## Arbitrary `from` in transferFrom used with permit

### Configuration

- Check: `arbitrary-send-erc20-permit`
- Severity: `High`
- Confidence: `Medium`

### Description

Detect when `msg.sender` is not used as `from` in transferFrom and permit is used.

### Exploit Scenario:

```solidity
    function bad(address from, uint256 value, uint256 deadline, uint8 v, bytes32 r, bytes32 s, address to) public {
        erc20.permit(from, address(this), value, deadline, v, r, s);
        erc20.transferFrom(from, to, value);
    }
```

If an ERC20 token does not implement permit and has a fallback function e.g. WETH, transferFrom allows an attacker to transfer all tokens approved for this contract.

### Recommendation

Ensure that the underlying ERC20 token correctly implements a permit function.

## Functions that send Ether to arbitrary destinations

### Configuration

- Check: `arbitrary-send-eth`
- Severity: `High`
- Confidence: `Medium`

### Description

Unprotected call to a function sending Ether to an arbitrary address.

### Exploit Scenario:

```solidity
contract ArbitrarySendEth{
    address destination;
    function setDestination(){
        destination = msg.sender;
    }

    function withdraw() public{
        destination.transfer(this.balance);
    }
}
```

Bob calls `setDestination` and `withdraw`. As a result he withdraws the contract's balance.

### Recommendation

Ensure that an arbitrary user cannot withdraw unauthorized funds.

## Array Length Assignment

### Configuration

- Check: `controlled-array-length`
- Severity: `High`
- Confidence: `Medium`

### Description

Detects the direct assignment of an array's length.

### Exploit Scenario:

```solidity
contract A {
	uint[] testArray; // dynamic size array

	function f(uint usersCount) public {
		// ...
		testArray.length = usersCount;
		// ...
	}

	function g(uint userIndex, uint val) public {
		// ...
		testArray[userIndex] = val;
		// ...
	}
}
```

Contract storage/state-variables are indexed by a 256-bit integer.
The user can set the array length to `2**256-1` in order to index all storage slots.
In the example above, one could call the function `f` to set the array length, then call the function `g` to control any storage slot desired.
Note that storage slots here are indexed via a hash of the indexers; nonetheless, all storage will still be accessible and could be controlled by the attacker.

### Recommendation

Do not allow array lengths to be set directly set; instead, opt to add values as needed.
Otherwise, thoroughly review the contract to ensure a user-controlled variable cannot reach an array length assignment.

## Controlled Delegatecall

### Configuration

- Check: `controlled-delegatecall`
- Severity: `High`
- Confidence: `Medium`

### Description

`Delegatecall` or `callcode` to an address controlled by the user.

### Exploit Scenario:

```solidity
contract Delegatecall{
    function delegate(address to, bytes data){
        to.delegatecall(data);
    }
}
```

Bob calls `delegate` and delegates the execution to his malicious contract. As a result, Bob withdraws the funds of the contract and destructs it.

### Recommendation

Avoid using `delegatecall`. Use only trusted destinations.

## Payable functions using `delegatecall` inside a loop

### Configuration

- Check: `delegatecall-loop`
- Severity: `High`
- Confidence: `Medium`

### Description

Detect the use of `delegatecall` inside a loop in a payable function.

### Exploit Scenario:

```solidity
contract DelegatecallInLoop{

    mapping (address => uint256) balances;

    function bad(address[] memory receivers) public payable {
        for (uint256 i = 0; i < receivers.length; i++) {
            address(this).delegatecall(abi.encodeWithSignature("addBalance(address)", receivers[i]));
        }
    }

    function addBalance(address a) public payable {
        balances[a] += msg.value;
    }

}
```

When calling `bad` the same `msg.value` amount will be accredited multiple times.

### Recommendation

Carefully check that the function called by `delegatecall` is not payable/doesn't use `msg.value`.

## Incorrect exponentiation

### Configuration

- Check: `incorrect-exp`
- Severity: `High`
- Confidence: `Medium`

### Description

Detect use of bitwise `xor ^` instead of exponential `**`

### Exploit Scenario:

```solidity
contract Bug{
    uint UINT_MAX = 2^256 - 1;
    ...
}
```

Alice deploys a contract in which `UINT_MAX` incorrectly uses `^` operator instead of `**` for exponentiation

### Recommendation

Use the correct operator `**` for exponentiation.

## Incorrect return in assembly

### Configuration

- Check: `incorrect-return`
- Severity: `High`
- Confidence: `Medium`

### Description

Detect if `return` in an assembly block halts unexpectedly the execution.

### Exploit Scenario:

```solidity
contract C {
    function f() internal returns (uint a, uint b) {
        assembly {
            return (5, 6)
        }
    }

    function g() returns (bool){
        f();
        return true;
    }
}
```

The return statement in `f` will cause execution in `g` to halt.
The function will return 6 bytes starting from offset 5, instead of returning a boolean.

### Recommendation

Use the `leave` statement.

## `msg.value` inside a loop

### Configuration

- Check: `msg-value-loop`
- Severity: `High`
- Confidence: `Medium`

### Description

Detect the use of `msg.value` inside a loop.

### Exploit Scenario:

```solidity
contract MsgValueInLoop{

    mapping (address => uint256) balances;

    function bad(address[] memory receivers) public payable {
        for (uint256 i=0; i < receivers.length; i++) {
            balances[receivers[i]] += msg.value;
        }
    }

}
```

### Recommendation

Provide an explicit array of amounts alongside the receivers array, and check that the sum of all amounts matches `msg.value`.

## Reentrancy vulnerabilities

### Configuration

- Check: `reentrancy-eth`
- Severity: `High`
- Confidence: `Medium`

### Description

Detection of the [reentrancy bug](https://github.com/trailofbits/not-so-smart-contracts/tree/master/reentrancy).
Do not report reentrancies that don't involve Ether (see `reentrancy-no-eth`)

### Exploit Scenario:

```solidity
    function withdrawBalance(){
        // send userBalance[msg.sender] Ether to msg.sender
        // if msg.sender is a contract, it will call its fallback function
        if( ! (msg.sender.call.value(userBalance[msg.sender])() ) ){
            throw;
        }
        userBalance[msg.sender] = 0;
    }
```

Bob uses the re-entrancy bug to call `withdrawBalance` two times, and withdraw more than its initial deposit to the contract.

### Recommendation

Apply the [`check-effects-interactions pattern`](http://solidity.readthedocs.io/en/v0.4.21/security-considerations.html#re-entrancy).

## Return instead of leave in assembly

### Configuration

- Check: `return-leave`
- Severity: `High`
- Confidence: `Medium`

### Description

Detect if a `return` is used where a `leave` should be used.

### Exploit Scenario:

```solidity
contract C {
    function f() internal returns (uint a, uint b) {
        assembly {
            return (5, 6)
        }
    }

}
```

The function will halt the execution, instead of returning a two uint.

### Recommendation

Use the `leave` statement.

## Storage Signed Integer Array

### Configuration

- Check: `storage-array`
- Severity: `High`
- Confidence: `Medium`

### Description

`solc` versions `0.4.7`-`0.5.9` contain [a compiler bug](https://blog.ethereum.org/2019/06/25/solidity-storage-array-bugs)
leading to incorrect values in signed integer arrays.

### Exploit Scenario:

```solidity
contract A {
	int[3] ether_balances; // storage signed integer array
	function bad0() private {
		// ...
		ether_balances = [-1, -1, -1];
		// ...
	}
}
```

`bad0()` uses a (storage-allocated) signed integer array state variable to store the ether balances of three accounts.  
`-1` is supposed to indicate uninitialized values but the Solidity bug makes these as `1`, which could be exploited by the accounts.

### Recommendation

Use a compiler version >= `0.5.10`.

## Unchecked transfer

### Configuration

- Check: `unchecked-transfer`
- Severity: `High`
- Confidence: `Medium`

### Description

The return value of an external transfer/transferFrom call is not checked

### Exploit Scenario:

```solidity
contract Token {
    function transferFrom(address _from, address _to, uint256 _value) public returns (bool success);
}
contract MyBank{
    mapping(address => uint) balances;
    Token token;
    function deposit(uint amount) public{
        token.transferFrom(msg.sender, address(this), amount);
        balances[msg.sender] += amount;
    }
}
```

Several tokens do not revert in case of failure and return false. If one of these tokens is used in `MyBank`, `deposit` will not revert if the transfer fails, and an attacker can call `deposit` for free..

### Recommendation

Use `SafeERC20`, or ensure that the transfer/transferFrom return value is checked.

## Weak PRNG

### Configuration

- Check: `weak-prng`
- Severity: `High`
- Confidence: `Medium`

### Description

Weak PRNG due to a modulo on `block.timestamp`, `now` or `blockhash`. These can be influenced by miners to some extent so they should be avoided.

### Exploit Scenario:

```solidity
contract Game {

    uint reward_determining_number;

    function guessing() external{
      reward_determining_number = uint256(block.blockhash(10000)) % 10;
    }
}
```

Eve is a miner. Eve calls `guessing` and re-orders the block containing the transaction.
As a result, Eve wins the game.

### Recommendation

Do not use `block.timestamp`, `now` or `blockhash` as a source of randomness

## Codex

### Configuration

- Check: `codex`
- Severity: `High`
- Confidence: `Low`

### Description

Use [codex](https://openai.com/blog/openai-codex/) to find vulnerabilities

### Exploit Scenario:

N/A

### Recommendation

Review codex's message.

## Domain separator collision

### Configuration

- Check: `domain-separator-collision`
- Severity: `Medium`
- Confidence: `High`

### Description

An ERC20 token has a function whose signature collides with EIP-2612's DOMAIN_SEPARATOR(), causing unanticipated behavior for contracts using `permit` functionality.

### Exploit Scenario:

```solidity
contract Contract{
    function some_collisions() external() {}
}
```

`some_collision` clashes with EIP-2612's DOMAIN_SEPARATOR() and will interfere with contract's using `permit`.

### Recommendation

Remove or rename the function that collides with DOMAIN_SEPARATOR().

## Dangerous enum conversion

### Configuration

- Check: `enum-conversion`
- Severity: `Medium`
- Confidence: `High`

### Description

Detect out-of-range `enum` conversion (`solc` < `0.4.5`).

### Exploit Scenario:

```solidity
    pragma solidity 0.4.2;
    contract Test{

    enum E{a}

    function bug(uint a) public returns(E){
        return E(a);
    }
}
```

Attackers can trigger unexpected behaviour by calling `bug(1)`.

### Recommendation

Use a recent compiler version. If `solc` <`0.4.5` is required, check the `enum` conversion range.

## Incorrect erc20 interface

### Configuration

- Check: `erc20-interface`
- Severity: `Medium`
- Confidence: `High`

### Description

Incorrect return values for `ERC20` functions. A contract compiled with Solidity > 0.4.22 interacting with these functions will fail to execute them, as the return value is missing.

### Exploit Scenario:

```solidity
contract Token{
    function transfer(address to, uint value) external;
    //...
}
```

`Token.transfer` does not return a boolean. Bob deploys the token. Alice creates a contract that interacts with it but assumes a correct `ERC20` interface implementation. Alice's contract is unable to interact with Bob's contract.

### Recommendation

Set the appropriate return values and types for the defined `ERC20` functions.

## Incorrect erc721 interface

### Configuration

- Check: `erc721-interface`
- Severity: `Medium`
- Confidence: `High`

### Description

Incorrect return values for `ERC721` functions. A contract compiled with solidity > 0.4.22 interacting with these functions will fail to execute them, as the return value is missing.

### Exploit Scenario:

```solidity
contract Token{
    function ownerOf(uint256 _tokenId) external view returns (bool);
    //...
}
```

`Token.ownerOf` does not return an address like `ERC721` expects. Bob deploys the token. Alice creates a contract that interacts with it but assumes a correct `ERC721` interface implementation. Alice's contract is unable to interact with Bob's contract.

### Recommendation

Set the appropriate return values and vtypes for the defined `ERC721` functions.

## Dangerous strict equalities

### Configuration

- Check: `incorrect-equality`
- Severity: `Medium`
- Confidence: `High`

### Description

Use of strict equalities that can be easily manipulated by an attacker.

### Exploit Scenario:

```solidity
contract Crowdsale{
    function fund_reached() public returns(bool){
        return this.balance == 100 ether;
    }
```

`Crowdsale` relies on `fund_reached` to know when to stop the sale of tokens.
`Crowdsale` reaches 100 Ether. Bob sends 0.1 Ether. As a result, `fund_reached` is always false and the `crowdsale` never ends.

### Recommendation

Don't use strict equality to determine if an account has enough Ether or tokens.

## Contracts that lock Ether

### Configuration

- Check: `locked-ether`
- Severity: `Medium`
- Confidence: `High`

### Description

Contract with a `payable` function, but without a withdrawal capacity.

### Exploit Scenario:

```solidity
pragma solidity 0.4.24;
contract Locked{
    function receive() payable public{
    }
}
```

Every Ether sent to `Locked` will be lost.

### Recommendation

Remove the payable attribute or add a withdraw function.

## Deletion on mapping containing a structure

### Configuration

- Check: `mapping-deletion`
- Severity: `Medium`
- Confidence: `High`

### Description

A deletion in a structure containing a mapping will not delete the mapping (see the [Solidity documentation](https://solidity.readthedocs.io/en/latest/types.html##delete)). The remaining data may be used to compromise the contract.

### Exploit Scenario:

```solidity
    struct BalancesStruct{
        address owner;
        mapping(address => uint) balances;
    }
    mapping(address => BalancesStruct) public stackBalance;

    function remove() internal{
         delete stackBalance[msg.sender];
    }
```

`remove` deletes an item of `stackBalance`.
The mapping `balances` is never deleted, so `remove` does not work as intended.

### Recommendation

Use a lock mechanism instead of a deletion to disable structure containing a mapping.

## Pyth deprecated functions

### Configuration

- Check: `pyth-deprecated-functions`
- Severity: `Medium`
- Confidence: `High`

### Description

Detect when a Pyth deprecated function is used

### Exploit Scenario:

```solidity
import "@pythnetwork/pyth-sdk-solidity/IPyth.sol";
import "@pythnetwork/pyth-sdk-solidity/PythStructs.sol";

contract C {

    IPyth pyth;

    constructor(IPyth _pyth) {
        pyth = _pyth;
    }

    function A(bytes32 priceId) public {
        PythStructs.Price memory price = pyth.getPrice(priceId);
        ...
    }
}
```

The function `A` uses the deprecated `getPrice` Pyth function.

### Recommendation

Do not use deprecated Pyth functions. Visit https://api-reference.pyth.network/.

## Pyth unchecked confidence level

### Configuration

- Check: `pyth-unchecked-confidence`
- Severity: `Medium`
- Confidence: `High`

### Description

Detect when the confidence level of a Pyth price is not checked

### Exploit Scenario:

```solidity
import "@pythnetwork/pyth-sdk-solidity/IPyth.sol";
import "@pythnetwork/pyth-sdk-solidity/PythStructs.sol";

contract C {
    IPyth pyth;

    constructor(IPyth _pyth) {
        pyth = _pyth;
    }

    function bad(bytes32 id, uint256 age) public {
        PythStructs.Price memory price = pyth.getEmaPriceNoOlderThan(id, age);
        // Use price
    }
}
```

The function `A` uses the price without checking its confidence level.

### Recommendation

Check the confidence level of a Pyth price. Visit https://docs.pyth.network/price-feeds/best-practices#confidence-intervals for more information.

## Pyth unchecked publishTime

### Configuration

- Check: `pyth-unchecked-publishtime`
- Severity: `Medium`
- Confidence: `High`

### Description

Detect when the publishTime of a Pyth price is not checked

### Exploit Scenario:

```solidity
import "@pythnetwork/pyth-sdk-solidity/IPyth.sol";
import "@pythnetwork/pyth-sdk-solidity/PythStructs.sol";

contract C {
    IPyth pyth;

    constructor(IPyth _pyth) {
        pyth = _pyth;
    }

    function bad(bytes32 id) public {
        PythStructs.Price memory price = pyth.getEmaPriceUnsafe(id);
        // Use price
    }
}
```

The function `A` uses the price without checking its `publishTime` coming from the `getEmaPriceUnsafe` function.

### Recommendation

Check the publishTime of a Pyth price.

## State variable shadowing from abstract contracts

### Configuration

- Check: `shadowing-abstract`
- Severity: `Medium`
- Confidence: `High`

### Description

Detection of state variables shadowed from abstract contracts.

### Exploit Scenario:

```solidity
contract BaseContract{
    address owner;
}

contract DerivedContract is BaseContract{
    address owner;
}
```

`owner` of `BaseContract` is shadowed in `DerivedContract`.

### Recommendation

Remove the state variable shadowing.

## Tautological compare

### Configuration

- Check: `tautological-compare`
- Severity: `Medium`
- Confidence: `High`

### Description

A variable compared to itself is probably an error as it will always return `true` for `==`, `>=`, `<=` and always `false` for `<`, `>` and `!=`.

### Exploit Scenario:

```solidity
    function check(uint a) external returns(bool){
        return (a >= a);
    }
```

`check` always return true.

### Recommendation

Remove comparison or compare to different value.

## Tautology or contradiction

### Configuration

- Check: `tautology`
- Severity: `Medium`
- Confidence: `High`

### Description

Detects expressions that are tautologies or contradictions.

### Exploit Scenario:

```solidity
contract A {
	function f(uint x) public {
		// ...
        if (x >= 0) { // bad -- always true
           // ...
        }
		// ...
	}

	function g(uint8 y) public returns (bool) {
		// ...
        return (y < 512); // bad!
		// ...
	}
}
```

`x` is a `uint256`, so `x >= 0` will be always true.
`y` is a `uint8`, so `y <512` will be always true.

### Recommendation

Fix the incorrect comparison by changing the value type or the comparison.

## Write after write

### Configuration

- Check: `write-after-write`
- Severity: `Medium`
- Confidence: `High`

### Description

Detects variables that are written but never read and written again.

### Exploit Scenario:

    ```solidity
    contract Buggy{
        function my_func() external initializer{
            // ...
            a = b;
            a = c;
            // ..
        }
    }
    ```
    `a` is first asigned to `b`, and then to `c`. As a result the first write does nothing.

### Recommendation

Fix or remove the writes.

## Misuse of a Boolean constant

### Configuration

- Check: `boolean-cst`
- Severity: `Medium`
- Confidence: `Medium`

### Description

Detects the misuse of a Boolean constant.

### Exploit Scenario:

```solidity
contract A {
	function f(uint x) public {
		// ...
        if (false) { // bad!
           // ...
        }
		// ...
	}

	function g(bool b) public returns (bool) {
		// ...
        return (b || true); // bad!
		// ...
	}
}
```

Boolean constants in code have only a few legitimate uses.
Other uses (in complex expressions, as conditionals) indicate either an error or, most likely, the persistence of faulty code.

### Recommendation

Verify and simplify the condition.

## Chronicle unchecked price

### Configuration

- Check: `chronicle-unchecked-price`
- Severity: `Medium`
- Confidence: `Medium`

### Description

Chronicle oracle is used and the price returned is not checked to be valid. For more information https://docs.chroniclelabs.org/Resources/FAQ/Oracles#how-do-i-check-if-an-oracle-becomes-inactive-gets-deprecated.

### Exploit Scenario:

```solidity
contract C {
    IChronicle chronicle;

    constructor(address a) {
        chronicle = IChronicle(a);
    }

    function bad() public {
        uint256 price = chronicle.read();
    }
```

The `bad` function gets the price from Chronicle by calling the read function however it does not check if the price is valid.

### Recommendation

Validate that the price returned by the oracle is valid.

## Constant functions using assembly code

### Configuration

- Check: `constant-function-asm`
- Severity: `Medium`
- Confidence: `Medium`

### Description

Functions declared as `constant`/`pure`/`view` using assembly code.

`constant`/`pure`/`view` was not enforced prior to Solidity 0.5.
Starting from Solidity 0.5, a call to a `constant`/`pure`/`view` function uses the `STATICCALL` opcode, which reverts in case of state modification.

As a result, a call to an [incorrectly labeled function may trap a contract compiled with Solidity 0.5](https://solidity.readthedocs.io/en/develop/050-breaking-changes.html#interoperability-with-older-contracts).

### Exploit Scenario:

```solidity
contract Constant{
    uint counter;
    function get() public view returns(uint){
       counter = counter +1;
       return counter
    }
}
```

`Constant` was deployed with Solidity 0.4.25. Bob writes a smart contract that interacts with `Constant` in Solidity 0.5.0.
All the calls to `get` revert, breaking Bob's smart contract execution.

### Recommendation

Ensure the attributes of contracts compiled prior to Solidity 0.5.0 are correct.

## Constant functions changing the state

### Configuration

- Check: `constant-function-state`
- Severity: `Medium`
- Confidence: `Medium`

### Description

Functions declared as `constant`/`pure`/`view` change the state.

`constant`/`pure`/`view` was not enforced prior to Solidity 0.5.
Starting from Solidity 0.5, a call to a `constant`/`pure`/`view` function uses the `STATICCALL` opcode, which reverts in case of state modification.

As a result, a call to an [incorrectly labeled function may trap a contract compiled with Solidity 0.5](https://solidity.readthedocs.io/en/develop/050-breaking-changes.html#interoperability-with-older-contracts).

### Exploit Scenario:

```solidity
contract Constant{
    uint counter;
    function get() public view returns(uint){
       counter = counter +1;
       return counter
    }
}
```

`Constant` was deployed with Solidity 0.4.25. Bob writes a smart contract that interacts with `Constant` in Solidity 0.5.0.
All the calls to `get` revert, breaking Bob's smart contract execution.

### Recommendation

Ensure that attributes of contracts compiled prior to Solidity 0.5.0 are correct.

## Divide before multiply

### Configuration

- Check: `divide-before-multiply`
- Severity: `Medium`
- Confidence: `Medium`

### Description

Solidity's integer division truncates. Thus, performing division before multiplication can lead to precision loss.

### Exploit Scenario:

```solidity
contract A {
	function f(uint n) public {
        coins = (oldSupply / n) * interest;
    }
}
```

If `n` is greater than `oldSupply`, `coins` will be zero. For example, with `oldSupply = 5; n = 10, interest = 2`, coins will be zero.  
If `(oldSupply * interest / n)` was used, `coins` would have been `1`.  
In general, it's usually a good idea to re-arrange arithmetic to perform multiplication before division, unless the limit of a smaller type makes this dangerous.

### Recommendation

Consider ordering multiplication before division.

## Gelato unprotected randomness

### Configuration

- Check: `gelato-unprotected-randomness`
- Severity: `Medium`
- Confidence: `Medium`

### Description

Detect calls to `_requestRandomness` within an unprotected function.

### Exploit Scenario:

```solidity
contract C is GelatoVRFConsumerBase {
    function _fulfillRandomness(
        uint256 randomness,
        uint256,
        bytes memory extraData
    ) internal override {
        // Do something with the random number
    }

    function bad() public {
        _requestRandomness(abi.encode(msg.sender));
    }
}
```

The function `bad` is uprotected and requests randomness.

### Recommendation

Function that request randomness should be allowed only to authorized users.

## Out-of-order retryable transactions

### Configuration

- Check: `out-of-order-retryable`
- Severity: `Medium`
- Confidence: `Medium`

### Description

Out-of-order retryable transactions

### Exploit Scenario:

```solidity
contract L1 {
    function doStuffOnL2() external {
        // Retryable A
        IInbox(inbox).createRetryableTicket({
            to: l2contract,
            l2CallValue: 0,
            maxSubmissionCost: maxSubmissionCost,
            excessFeeRefundAddress: msg.sender,
            callValueRefundAddress: msg.sender,
            gasLimit: gasLimit,
            maxFeePerGas: maxFeePerGas,
            data: abi.encodeCall(l2contract.claim_rewards, ())
        });
        // Retryable B
        IInbox(inbox).createRetryableTicket({
            to: l2contract,
            l2CallValue: 0,
            maxSubmissionCost: maxSubmissionCost,
            excessFeeRefundAddress: msg.sender,
            callValueRefundAddress: msg.sender,
            gasLimit: gas,
            maxFeePerGas: maxFeePerGas,
            data: abi.encodeCall(l2contract.unstake, ())
        });
    }
}

contract L2 {
    function claim_rewards() public {
        // rewards is computed based on balance and staking period
        uint unclaimed_rewards = _compute_and_update_rewards();
        token.safeTransfer(msg.sender, unclaimed_rewards);
    }

    // Call claim_rewards before unstaking, otherwise you lose your rewards
    function unstake() public {
        _free_rewards(); // clean up rewards related variables
        balance = balance[msg.sender];
        balance[msg.sender] = 0;
        staked_token.safeTransfer(msg.sender, balance);
    }
}
```

Bob calls `doStuffOnL2` but the first retryable ticket calling `claim_rewards` fails. The second retryable ticket calling `unstake` is executed successfully. As a result, Bob loses his rewards.

### Recommendation

Do not rely on the order or successful execution of retryable tickets.

## Reentrancy vulnerabilities

### Configuration

- Check: `reentrancy-no-eth`
- Severity: `Medium`
- Confidence: `Medium`

### Description

Detection of the [reentrancy bug](https://github.com/trailofbits/not-so-smart-contracts/tree/master/reentrancy).
Do not report reentrancies that involve Ether (see `reentrancy-eth`).

### Exploit Scenario:

```solidity
    function bug(){
        require(not_called);
        if( ! (msg.sender.call() ) ){
            throw;
        }
        not_called = False;
    }
```

### Recommendation

Apply the [`check-effects-interactions` pattern](http://solidity.readthedocs.io/en/v0.4.21/security-considerations.html#re-entrancy).

## Reused base constructors

### Configuration

- Check: `reused-constructor`
- Severity: `Medium`
- Confidence: `Medium`

### Description

Detects if the same base constructor is called with arguments from two different locations in the same inheritance hierarchy.

### Exploit Scenario:

```solidity
pragma solidity ^0.4.0;

contract A{
    uint num = 5;
    constructor(uint x) public{
        num += x;
    }
}

contract B is A{
    constructor() A(2) public { /* ... */ }
}

contract C is A {
    constructor() A(3) public { /* ... */ }
}

contract D is B, C {
    constructor() public { /* ... */ }
}

contract E is B {
    constructor() A(1) public { /* ... */ }
}
```

The constructor of `A` is called multiple times in `D` and `E`:

- `D` inherits from `B` and `C`, both of which construct `A`.
- `E` only inherits from `B`, but `B` and `E` construct `A`.
  .

### Recommendation

Remove the duplicate constructor call.

## Dangerous usage of `tx.origin`

### Configuration

- Check: `tx-origin`
- Severity: `Medium`
- Confidence: `Medium`

### Description

`tx.origin`-based protection can be abused by a malicious contract if a legitimate user interacts with the malicious contract.

### Exploit Scenario:

```solidity
contract TxOrigin {
    address owner = msg.sender;

    function bug() {
        require(tx.origin == owner);
    }
```

Bob is the owner of `TxOrigin`. Bob calls Eve's contract. Eve's contract calls `TxOrigin` and bypasses the `tx.origin` protection.

### Recommendation

Do not use `tx.origin` for authorization.

## Unchecked low-level calls

### Configuration

- Check: `unchecked-lowlevel`
- Severity: `Medium`
- Confidence: `Medium`

### Description

The return value of a low-level call is not checked.

### Exploit Scenario:

```solidity
contract MyConc{
    function my_func(address payable dst) public payable{
        dst.call.value(msg.value)("");
    }
}
```

The return value of the low-level call is not checked, so if the call fails, the Ether will be locked in the contract.
If the low level is used to prevent blocking operations, consider logging failed calls.

### Recommendation

Ensure that the return value of a low-level call is checked or logged.

## Unchecked Send

### Configuration

- Check: `unchecked-send`
- Severity: `Medium`
- Confidence: `Medium`

### Description

The return value of a `send` is not checked.

### Exploit Scenario:

```solidity
contract MyConc{
    function my_func(address payable dst) public payable{
        dst.send(msg.value);
    }
}
```

The return value of `send` is not checked, so if the send fails, the Ether will be locked in the contract.
If `send` is used to prevent blocking operations, consider logging the failed `send`.

### Recommendation

Ensure that the return value of `send` is checked or logged.

## Uninitialized local variables

### Configuration

- Check: `uninitialized-local`
- Severity: `Medium`
- Confidence: `Medium`

### Description

Uninitialized local variables.

### Exploit Scenario:

```solidity
contract Uninitialized is Owner{
    function withdraw() payable public onlyOwner{
        address to;
        to.transfer(this.balance)
    }
}
```

Bob calls `transfer`. As a result, all Ether is sent to the address `0x0` and is lost.

### Recommendation

Initialize all the variables. If a variable is meant to be initialized to zero, explicitly set it to zero to improve code readability.

## Unused return

### Configuration

- Check: `unused-return`
- Severity: `Medium`
- Confidence: `Medium`

### Description

The return value of an external call is not stored in a local or state variable.

### Exploit Scenario:

```solidity
contract MyConc{
    using SafeMath for uint;
    function my_func(uint a, uint b) public{
        a.add(b);
    }
}
```

`MyConc` calls `add` of `SafeMath`, but does not store the result in `a`. As a result, the computation has no effect.

### Recommendation

Ensure that all the return values of the function calls are used.

## Chainlink Feed Registry usage

### Configuration

- Check: `chainlink-feed-registry`
- Severity: `Low`
- Confidence: `High`

### Description

Detect when Chainlink Feed Registry is used. At the moment is only available on Ethereum Mainnet.

### Exploit Scenario:

```solidity
import "chainlink/contracts/src/v0.8/interfaces/FeedRegistryInteface.sol"

contract A {
    FeedRegistryInterface public immutable registry;

    constructor(address _registry) {
        registry = _registry;
    }

    function getPrice(address base, address quote) public return(uint256) {
        (, int256 price,,,) = registry.latestRoundData(base, quote);
        // Do price validation
        return uint256(price);
    }
}
```

If the contract is deployed on a different chain than Ethereum Mainnet the `getPrice` function will revert.

### Recommendation

Do not use Chainlink Feed Registry outside of Ethereum Mainnet.

## Incorrect modifier

### Configuration

- Check: `incorrect-modifier`
- Severity: `Low`
- Confidence: `High`

### Description

If a modifier does not execute `_` or revert, the execution of the function will return the default value, which can be misleading for the caller.

### Exploit Scenario:

```solidity
    modidfier myModif(){
        if(..){
           _;
        }
    }
    function get() myModif returns(uint){

    }
```

If the condition in `myModif` is false, the execution of `get()` will return 0.

### Recommendation

All the paths in a modifier must execute `_` or revert.

## Optimism deprecated predeploy or function

### Configuration

- Check: `optimism-deprecation`
- Severity: `Low`
- Confidence: `High`

### Description

Detect when deprecated Optimism predeploy or function is used.

### Exploit Scenario:

```solidity
interface GasPriceOracle {
    function scalar() external view returns (uint256);
}

contract Test {
    GasPriceOracle constant OPT_GAS = GasPriceOracle(0x420000000000000000000000000000000000000F);

    function a() public {
        OPT_GAS.scalar();
    }
}
```

The call to the `scalar` function of the Optimism GasPriceOracle predeploy always revert.

### Recommendation

Do not use the deprecated components.

## Built-in Symbol Shadowing

### Configuration

- Check: `shadowing-builtin`
- Severity: `Low`
- Confidence: `High`

### Description

Detection of shadowing built-in symbols using local variables, state variables, functions, modifiers, or events.

### Exploit Scenario:

```solidity
pragma solidity ^0.4.24;

contract Bug {
    uint now; // Overshadows current time stamp.

    function assert(bool condition) public {
        // Overshadows built-in symbol for providing assertions.
    }

    function get_next_expiration(uint earlier_time) private returns (uint) {
        return now + 259200; // References overshadowed timestamp.
    }
}
```

`now` is defined as a state variable, and shadows with the built-in symbol `now`. The function `assert` overshadows the built-in `assert` function. Any use of either of these built-in symbols may lead to unexpected results.

### Recommendation

Rename the local variables, state variables, functions, modifiers, and events that shadow a Built-in symbol.

## Local variable shadowing

### Configuration

- Check: `shadowing-local`
- Severity: `Low`
- Confidence: `High`

### Description

Detection of shadowing using local variables.

### Exploit Scenario:

```solidity
pragma solidity ^0.4.24;

contract Bug {
    uint owner;

    function sensitive_function(address owner) public {
        // ...
        require(owner == msg.sender);
    }

    function alternate_sensitive_function() public {
        address owner = msg.sender;
        // ...
        require(owner == msg.sender);
    }
}
```

`sensitive_function.owner` shadows `Bug.owner`. As a result, the use of `owner` in `sensitive_function` might be incorrect.

### Recommendation

Rename the local variables that shadow another component.

## Uninitialized function pointers in constructors

### Configuration

- Check: `uninitialized-fptr-cst`
- Severity: `Low`
- Confidence: `High`

### Description

solc versions `0.4.5`-`0.4.26` and `0.5.0`-`0.5.8` contain a compiler bug leading to unexpected behavior when calling uninitialized function pointers in constructors.

### Exploit Scenario:

```solidity
contract bad0 {

  constructor() public {
    /* Uninitialized function pointer */
    function(uint256) internal returns(uint256) a;
    a(10);
  }

}
```

The call to `a(10)` will lead to unexpected behavior because function pointer `a` is not initialized in the constructor.

### Recommendation

Initialize function pointers before calling. Avoid function pointers if possible.

## Pre-declaration usage of local variables

### Configuration

- Check: `variable-scope`
- Severity: `Low`
- Confidence: `High`

### Description

Detects the possible usage of a variable before the declaration is stepped over (either because it is later declared, or declared in another scope).

### Exploit Scenario:

```solidity
contract C {
    function f(uint z) public returns (uint) {
        uint y = x + 9 + z; // 'x' is used pre-declaration
        uint x = 7;

        if (z % 2 == 0) {
            uint max = 5;
            // ...
        }

        // 'max' was intended to be 5, but it was mistakenly declared in a scope and not assigned (so it is zero).
        for (uint i = 0; i < max; i++) {
            x += 1;
        }

        return x;
    }
}
```

In the case above, the variable `x` is used before its declaration, which may result in unintended consequences.
Additionally, the for-loop uses the variable `max`, which is declared in a previous scope that may not always be reached. This could lead to unintended consequences if the user mistakenly uses a variable prior to any intended declaration assignment. It also may indicate that the user intended to reference a different variable.

### Recommendation

Move all variable declarations prior to any usage of the variable, and ensure that reaching a variable declaration does not depend on some conditional if it is used unconditionally.

## Void constructor

### Configuration

- Check: `void-cst`
- Severity: `Low`
- Confidence: `High`

### Description

Detect the call to a constructor that is not implemented

### Exploit Scenario:

```solidity
contract A{}
contract B is A{
    constructor() public A(){}
}
```

When reading `B`'s constructor definition, we might assume that `A()` initiates the contract, but no code is executed.

### Recommendation

Remove the constructor call.

## Calls inside a loop

### Configuration

- Check: `calls-loop`
- Severity: `Low`
- Confidence: `Medium`

### Description

Calls inside a loop might lead to a denial-of-service attack.

### Exploit Scenario:

```solidity
contract CallsInLoop{

    address[] destinations;

    constructor(address[] newDestinations) public{
        destinations = newDestinations;
    }

    function bad() external{
        for (uint i=0; i < destinations.length; i++){
            destinations[i].transfer(i);
        }
    }

}
```

If one of the destinations has a fallback function that reverts, `bad` will always revert.

### Recommendation

Favor [pull over push](https://github.com/ethereum/wiki/wiki/Safety#favor-pull-over-push-for-external-calls) strategy for external calls.

## Missing events access control

### Configuration

- Check: `events-access`
- Severity: `Low`
- Confidence: `Medium`

### Description

Detect missing events for critical access control parameters

### Exploit Scenario:

```solidity
contract C {

  modifier onlyAdmin {
    if (msg.sender != owner) throw;
    _;
  }

  function updateOwner(address newOwner) onlyAdmin external {
    owner = newOwner;
  }
}
```

`updateOwner()` has no event, so it is difficult to track off-chain owner changes.

### Recommendation

Emit an event for critical parameter changes.

## Missing events arithmetic

### Configuration

- Check: `events-maths`
- Severity: `Low`
- Confidence: `Medium`

### Description

Detect missing events for critical arithmetic parameters.

### Exploit Scenario:

```solidity
contract C {

    modifier onlyOwner {
        if (msg.sender != owner) throw;
        _;
    }

    function setBuyPrice(uint256 newBuyPrice) onlyOwner public {
        buyPrice = newBuyPrice;
    }

    function buy() external {
     ... // buyPrice is used to determine the number of tokens purchased
    }
}
```

`setBuyPrice()` does not emit an event, so it is difficult to track changes in the value of `buyPrice` off-chain.

### Recommendation

Emit an event for critical parameter changes.

## Dangerous unary expressions

### Configuration

- Check: `incorrect-unary`
- Severity: `Low`
- Confidence: `Medium`

### Description

Unary expressions such as `x=+1` probably typos.

### Exploit Scenario:

```Solidity
contract Bug{
    uint public counter;

    function increase() public returns(uint){
        counter=+1;
        return counter;
    }
}
```

`increase()` uses `=+` instead of `+=`, so `counter` will never exceed 1.

### Recommendation

Remove the unary expression.

## Missing zero address validation

### Configuration

- Check: `missing-zero-check`
- Severity: `Low`
- Confidence: `Medium`

### Description

Detect missing zero address validation.

### Exploit Scenario:

```solidity
contract C {

  modifier onlyAdmin {
    if (msg.sender != owner) throw;
    _;
  }

  function updateOwner(address newOwner) onlyAdmin external {
    owner = newOwner;
  }
}
```

Bob calls `updateOwner` without specifying the `newOwner`, so Bob loses ownership of the contract.

### Recommendation

Check that the address is not zero.

## Reentrancy vulnerabilities

### Configuration

- Check: `reentrancy-benign`
- Severity: `Low`
- Confidence: `Medium`

### Description

Detection of the [reentrancy bug](https://github.com/trailofbits/not-so-smart-contracts/tree/master/reentrancy).
Only report reentrancy that acts as a double call (see `reentrancy-eth`, `reentrancy-no-eth`).

### Exploit Scenario:

```solidity
    function callme(){
        if( ! (msg.sender.call()() ) ){
            throw;
        }
        counter += 1
    }
```

`callme` contains a reentrancy. The reentrancy is benign because it's exploitation would have the same effect as two consecutive calls.

### Recommendation

Apply the [`check-effects-interactions` pattern](http://solidity.readthedocs.io/en/v0.4.21/security-considerations.html#re-entrancy).

## Reentrancy vulnerabilities

### Configuration

- Check: `reentrancy-events`
- Severity: `Low`
- Confidence: `Medium`

### Description

Detects [reentrancies](https://github.com/trailofbits/not-so-smart-contracts/tree/master/reentrancy) that allow manipulation of the order or value of events.

### Exploit Scenario:

```solidity
contract ReentrantContract {
	function f() external {
		if (BugReentrancyEvents(msg.sender).counter() == 1) {
			BugReentrancyEvents(msg.sender).count(this);
		}
	}
}
contract Counter {
	uint public counter;
	event Counter(uint);

}
contract BugReentrancyEvents is Counter {
    function count(ReentrantContract d) external {
        counter += 1;
        d.f();
        emit Counter(counter);
    }
}
contract NoReentrancyEvents is Counter {
	function count(ReentrantContract d) external {
        counter += 1;
        emit Counter(counter);
        d.f();
    }
}
```

If the external call `d.f()` re-enters `BugReentrancyEvents`, the `Counter` events will be incorrect (`Counter(2)`, `Counter(2)`) whereas `NoReentrancyEvents` will correctly emit
(`Counter(1)`, `Counter(2)`). This may cause issues for offchain components that rely on the values of events e.g. checking for the amount deposited to a bridge.

### Recommendation

Apply the [`check-effects-interactions` pattern](https://docs.soliditylang.org/en/latest/security-considerations.html#re-entrancy).

## Return Bomb

### Configuration

- Check: `return-bomb`
- Severity: `Low`
- Confidence: `Medium`

### Description

A low level callee may consume all callers gas unexpectedly.

### Exploit Scenario:

```solidity
//Modified from https://github.com/nomad-xyz/ExcessivelySafeCall
contract BadGuy {
    function youveActivateMyTrapCard() external pure returns (bytes memory) {
        assembly{
            revert(0, 1000000)
        }
    }
}

contract Mark {
    function oops(address badGuy) public{
        bool success;
        bytes memory ret;

        // Mark pays a lot of gas for this copy
        //(success, ret) = badGuy.call{gas:10000}(
        (success, ret) = badGuy.call(
            abi.encodeWithSelector(
                BadGuy.youveActivateMyTrapCard.selector
            )
        );

        // Mark may OOG here, preventing local state changes
        //importantCleanup();
    }
}

```

After Mark calls BadGuy bytes are copied from returndata to memory, the memory expansion cost is paid. This means that when using a standard solidity call, the callee can "returnbomb" the caller, imposing an arbitrary gas cost.
Callee unexpectedly makes the caller OOG.

### Recommendation

Avoid unlimited implicit decoding of returndata.

## Block timestamp

### Configuration

- Check: `timestamp`
- Severity: `Low`
- Confidence: `Medium`

### Description

Dangerous usage of `block.timestamp`. `block.timestamp` can be manipulated by miners.

### Exploit Scenario:

"Bob's contract relies on `block.timestamp` for its randomness. Eve is a miner and manipulates `block.timestamp` to exploit Bob's contract.

### Recommendation

Avoid relying on `block.timestamp`.

## Assembly usage

### Configuration

- Check: `assembly`
- Severity: `Informational`
- Confidence: `High`

### Description

The use of assembly is error-prone and should be avoided.

### Recommendation

Do not use `evm` assembly.

## Assert state change

### Configuration

- Check: `assert-state-change`
- Severity: `Informational`
- Confidence: `High`

### Description

Incorrect use of `assert()`. See Solidity best [practices](https://solidity.readthedocs.io/en/latest/control-structures.html#id4).

### Exploit Scenario:

```solidity
contract A {

  uint s_a;

  function bad() public {
    assert((s_a += 1) > 10);
  }
}
```

The assert in `bad()` increments the state variable `s_a` while checking for the condition.

### Recommendation

Use `require` for invariants modifying the state.

## Boolean equality

### Configuration

- Check: `boolean-equal`
- Severity: `Informational`
- Confidence: `High`

### Description

Detects the comparison to boolean constants.

### Exploit Scenario:

```solidity
contract A {
	function f(bool x) public {
		// ...
        if (x == true) { // bad!
           // ...
        }
		// ...
	}
}
```

Boolean constants can be used directly and do not need to be compare to `true` or `false`.

### Recommendation

Remove the equality to the boolean constant.

## Cyclomatic complexity

### Configuration

- Check: `cyclomatic-complexity`
- Severity: `Informational`
- Confidence: `High`

### Description

Detects functions with high (> 11) cyclomatic complexity.

### Recommendation

Reduce cyclomatic complexity by splitting the function into several smaller subroutines.

## Deprecated standards

### Configuration

- Check: `deprecated-standards`
- Severity: `Informational`
- Confidence: `High`

### Description

Detect the usage of deprecated standards.

### Exploit Scenario:

```solidity
contract ContractWithDeprecatedReferences {
    // Deprecated: Change block.blockhash() -> blockhash()
    bytes32 globalBlockHash = block.blockhash(0);

    // Deprecated: Change constant -> view
    function functionWithDeprecatedThrow() public constant {
        // Deprecated: Change msg.gas -> gasleft()
        if(msg.gas == msg.value) {
            // Deprecated: Change throw -> revert()
            throw;
        }
    }

    // Deprecated: Change constant -> view
    function functionWithDeprecatedReferences() public constant {
        // Deprecated: Change sha3() -> keccak256()
        bytes32 sha3Result = sha3("test deprecated sha3 usage");

        // Deprecated: Change callcode() -> delegatecall()
        address(this).callcode();

        // Deprecated: Change suicide() -> selfdestruct()
        suicide(address(0));
    }
}
```

### Recommendation

Replace all uses of deprecated symbols.

## Unindexed ERC20 event parameters

### Configuration

- Check: `erc20-indexed`
- Severity: `Informational`
- Confidence: `High`

### Description

Detects whether events defined by the `ERC20` specification that should have some parameters as `indexed` are missing the `indexed` keyword.

### Exploit Scenario:

```solidity
contract ERC20Bad {
    // ...
    event Transfer(address from, address to, uint value);
    event Approval(address owner, address spender, uint value);

    // ...
}
```

`Transfer` and `Approval` events should have the 'indexed' keyword on their two first parameters, as defined by the `ERC20` specification.
Failure to include these keywords will exclude the parameter data in the transaction/block's bloom filter, so external tooling searching for these parameters may overlook them and fail to index logs from this token contract.

### Recommendation

Add the `indexed` keyword to event parameters that should include it, according to the `ERC20` specification.

## Function Initializing State

### Configuration

- Check: `function-init-state`
- Severity: `Informational`
- Confidence: `High`

### Description

Detects the immediate initialization of state variables through function calls that are not pure/constant, or that use non-constant state variable.

### Exploit Scenario:

```solidity
contract StateVarInitFromFunction {

    uint public v = set(); // Initialize from function (sets to 77)
    uint public w = 5;
    uint public x = set(); // Initialize from function (sets to 88)
    address public shouldntBeReported = address(8);

    constructor(){
        // The constructor is run after all state variables are initialized.
    }

    function set() public  returns(uint)  {
        // If this function is being used to initialize a state variable declared
        // before w, w will be zero. If it is declared after w, w will be set.
        if(w == 0) {
            return 77;
        }

        return 88;
    }
}
```

In this case, users might intend a function to return a value a state variable can initialize with, without realizing the context for the contract is not fully initialized.
In the example above, the same function sets two different values for state variables because it checks a state variable that is not yet initialized in one case, and is initialized in the other.
Special care must be taken when initializing state variables from an immediate function call so as not to incorrectly assume the state is initialized.

### Recommendation

Remove any initialization of state variables via non-constant state variables or function calls. If variables must be set upon contract deployment, locate initialization in the constructor instead.

## Incorrect usage of using-for statement

### Configuration

- Check: `incorrect-using-for`
- Severity: `Informational`
- Confidence: `High`

### Description

In Solidity, it is possible to use libraries for certain types, by the `using-for` statement (`using <library> for <type>`). However, the Solidity compiler doesn't check whether a given library has at least one function matching a given type. If it doesn't, such a statement has no effect and may be confusing.

### Exploit Scenario:

    ```solidity
    library L {
        function f(bool) public pure {}
    }

    using L for uint;
    ```
    Such a code will compile despite the fact that `L` has no function with `uint` as its first argument.

### Recommendation

Make sure that the libraries used in `using-for` statements have at least one function matching a type used in these statements.

## Low-level calls

### Configuration

- Check: `low-level-calls`
- Severity: `Informational`
- Confidence: `High`

### Description

The use of low-level calls is error-prone. Low-level calls do not check for [code existence](https://solidity.readthedocs.io/en/v0.4.25/control-structures.html#error-handling-assert-require-revert-and-exceptions) or call success.

### Recommendation

Avoid low-level calls. Check the call success. If the call is meant for a contract, check for code existence.

## Missing inheritance

### Configuration

- Check: `missing-inheritance`
- Severity: `Informational`
- Confidence: `High`

### Description

Detect missing inheritance.

### Exploit Scenario:

```solidity
interface ISomething {
    function f1() external returns(uint);
}

contract Something {
    function f1() external returns(uint){
        return 42;
    }
}
```

`Something` should inherit from `ISomething`.

### Recommendation

Inherit from the missing interface or contract.

## Conformance to Solidity naming conventions

### Configuration

- Check: `naming-convention`
- Severity: `Informational`
- Confidence: `High`

### Description

Solidity defines a [naming convention](https://solidity.readthedocs.io/en/v0.4.25/style-guide.html#naming-conventions) that should be followed.

#### Rule exceptions

- Allow constant variable name/symbol/decimals to be lowercase (`ERC20`).
- Allow `_` at the beginning of the `mixed_case` match for private variables and unused parameters.

### Recommendation

Follow the Solidity [naming convention](https://solidity.readthedocs.io/en/v0.4.25/style-guide.html#naming-conventions).

## Different pragma directives are used

### Configuration

- Check: `pragma`
- Severity: `Informational`
- Confidence: `High`

### Description

Detect whether different Solidity versions are used.

### Recommendation

Use one Solidity version.

## Redundant Statements

### Configuration

- Check: `redundant-statements`
- Severity: `Informational`
- Confidence: `High`

### Description

Detect the usage of redundant statements that have no effect.

### Exploit Scenario:

```solidity
contract RedundantStatementsContract {

    constructor() public {
        uint; // Elementary Type Name
        bool; // Elementary Type Name
        RedundantStatementsContract; // Identifier
    }

    function test() public returns (uint) {
        uint; // Elementary Type Name
        assert; // Identifier
        test; // Identifier
        return 777;
    }
}
```

Each commented line references types/identifiers, but performs no action with them, so no code will be generated for such statements and they can be removed.

### Recommendation

Remove redundant statements if they congest code but offer no value.

## Incorrect versions of Solidity

### Configuration

- Check: `solc-version`
- Severity: `Informational`
- Confidence: `High`

### Description

`solc` frequently releases new compiler versions. Using an old version prevents access to new Solidity security checks.
We also recommend avoiding complex `pragma` statement.

### Recommendation

Deploy with a recent version of Solidity (at least 0.8.0) with no known severe issues.

Use a simple pragma version that allows any of these versions.
Consider using the latest version of Solidity for testing.

## Unimplemented functions

### Configuration

- Check: `unimplemented-functions`
- Severity: `Informational`
- Confidence: `High`

### Description

Detect functions that are not implemented on derived-most contracts.

### Exploit Scenario:

```solidity
interface BaseInterface {
    function f1() external returns(uint);
    function f2() external returns(uint);
}

interface BaseInterface2 {
    function f3() external returns(uint);
}

contract DerivedContract is BaseInterface, BaseInterface2 {
    function f1() external returns(uint){
        return 42;
    }
}
```

`DerivedContract` does not implement `BaseInterface.f2` or `BaseInterface2.f3`.
As a result, the contract will not properly compile.
All unimplemented functions must be implemented on a contract that is meant to be used.

### Recommendation

Implement all unimplemented functions in any contract you intend to use directly (not simply inherit from).

## Unused state variable

### Configuration

- Check: `unused-state`
- Severity: `Informational`
- Confidence: `High`

### Description

Unused state variable.

### Recommendation

Remove unused state variables.

## Costly operations inside a loop

### Configuration

- Check: `costly-loop`
- Severity: `Informational`
- Confidence: `Medium`

### Description

Costly operations inside a loop might waste gas, so optimizations are justified.

### Exploit Scenario:

```solidity
contract CostlyOperationsInLoop{

    uint loop_count = 100;
    uint state_variable=0;

    function bad() external{
        for (uint i=0; i < loop_count; i++){
            state_variable++;
        }
    }

    function good() external{
      uint local_variable = state_variable;
      for (uint i=0; i < loop_count; i++){
        local_variable++;
      }
      state_variable = local_variable;
    }
}
```

Incrementing `state_variable` in a loop incurs a lot of gas because of expensive `SSTOREs`, which might lead to an `out-of-gas`.

### Recommendation

Use a local variable to hold the loop computation result.

## Dead-code

### Configuration

- Check: `dead-code`
- Severity: `Informational`
- Confidence: `Medium`

### Description

Functions that are not used.

### Exploit Scenario:

```solidity
contract Contract{
    function dead_code() internal() {}
}
```

`dead_code` is not used in the contract, and make the code's review more difficult.

### Recommendation

Remove unused functions.

## Reentrancy vulnerabilities

### Configuration

- Check: `reentrancy-unlimited-gas`
- Severity: `Informational`
- Confidence: `Medium`

### Description

Detection of the [reentrancy bug](https://github.com/trailofbits/not-so-smart-contracts/tree/master/reentrancy).
Only report reentrancy that is based on `transfer` or `send`.

### Exploit Scenario:

```solidity
    function callme(){
        msg.sender.transfer(balances[msg.sender]):
        balances[msg.sender] = 0;
    }
```

`send` and `transfer` do not protect from reentrancies in case of gas price changes.

### Recommendation

Apply the [`check-effects-interactions` pattern](http://solidity.readthedocs.io/en/v0.4.21/security-considerations.html#re-entrancy).

## Too many digits

### Configuration

- Check: `too-many-digits`
- Severity: `Informational`
- Confidence: `Medium`

### Description

Literals with many digits are difficult to read and review. Use scientific notation or suffixes to make the code more readable.

### Exploit Scenario:

```solidity
contract MyContract{
    uint 1_ether = 10000000000000000000;
}
```

While `1_ether` looks like `1 ether`, it is `10 ether`. As a result, it's likely to be used incorrectly.

### Recommendation

Use:

- [Ether suffix](https://solidity.readthedocs.io/en/latest/units-and-global-variables.html#ether-units),
- [Time suffix](https://solidity.readthedocs.io/en/latest/units-and-global-variables.html#time-units), or
- [The scientific notation](https://solidity.readthedocs.io/en/latest/types.html#rational-and-integer-literals)

## Cache array length

### Configuration

- Check: `cache-array-length`
- Severity: `Optimization`
- Confidence: `High`

### Description

Detects `for` loops that use `length` member of some storage array in their loop condition and don't modify it.

### Exploit Scenario:

```solidity
contract C
{
    uint[] array;

    function f() public
    {
        for (uint i = 0; i < array.length; i++)
        {
            // code that does not modify length of `array`
        }
    }
}
```

Since the `for` loop in `f` doesn't modify `array.length`, it is more gas efficient to cache it in some local variable and use that variable instead, like in the following example:

```solidity
contract C
{
    uint[] array;

    function f() public
    {
        uint array_length = array.length;
        for (uint i = 0; i < array_length; i++)
        {
            // code that does not modify length of `array`
        }
    }
}
```

### Recommendation

Cache the lengths of storage arrays if they are used and not modified in `for` loops.

## State variables that could be declared constant

### Configuration

- Check: `constable-states`
- Severity: `Optimization`
- Confidence: `High`

### Description

State variables that are not updated following deployment should be declared constant to save gas.

### Recommendation

Add the `constant` attribute to state variables that never change.

## Public function that could be declared external

### Configuration

- Check: `external-function`
- Severity: `Optimization`
- Confidence: `High`

### Description

`public` functions that are never called by the contract should be declared `external`, and its immutable parameters should be located in `calldata` to save gas.

### Recommendation

Use the `external` attribute for functions never called from the contract, and change the location of immutable parameters to `calldata` to save gas.

## State variables that could be declared immutable

### Configuration

- Check: `immutable-states`
- Severity: `Optimization`
- Confidence: `High`

### Description

State variables that are not updated following deployment should be declared immutable to save gas.

### Recommendation

Add the `immutable` attribute to state variables that never change or are set only in the constructor.

## Public variable read in external context

### Configuration

- Check: `var-read-using-this`
- Severity: `Optimization`
- Confidence: `High`

### Description

The contract reads its own variable using `this`, adding overhead of an unnecessary STATICCALL.

### Exploit Scenario:

```solidity
contract C {
    mapping(uint => address) public myMap;
    function test(uint x) external returns(address) {
        return this.myMap(x);
    }
}
```

### Recommendation

Read the variable directly from storage instead of calling the contract.
