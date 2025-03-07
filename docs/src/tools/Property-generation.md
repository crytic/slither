`slither-prop` generates code properties (e.g., invariants) that can be tested with unit tests or [Echidna](https://github.com/crytic/echidna/), entirely automatically. Once you have these properties in hand, use [Crytic](https://crytic.io/) to continuously test them with every commit.

Note: `slither-prop` only supports Truffle for now. We'll be adding support for other frameworks soon!

## How to Use Slither's Property Generator

There are four steps:

1. [Generate the tests](#step-1-generate-the-tests)
1. [Customize the constructor](#step-2-customize-the-constructor)
1. [Run the unit tests](#step-3-run-the-unit-tests-with-truffle)
1. [Run the Echidna tests](#step-4-run-the-property-tests-with-echidna)

### Step 1. Generate the tests

```
slither-prop . --contract ContractName
```

`slither-prop` will generate:

- Solidity files containing the properties
- `echidna_config.yaml` to configure Echidna
- One Truffle migration file
- Two Truffle unit-test files

For example on [examples/slither-prop](https://github.com/crytic/slither/tree/9623a2781faa4e7759f06d2e8c4adcd45078af69/examples/slither-prop).
```
Write contracts/crytic/interfaces.sol
Write contracts/crytic/PropertiesERC20BuggyTransferable.sol
Write contracts/crytic/TestERC20BuggyTransferable.sol
Write echidna_config.yaml
Write migrations/1_TestERC20BuggyTransferable.js
Write test/crytic/InitializationTestERC20BuggyTransferable.js
Write test/crytic/TestERC20BuggyTransferable.js
################################################
Update the constructor in contracts/crytic/TestERC20BuggyTransferable.sol

To run the unit tests:
	truffle test test/crytic/InitializationTestERC20BuggyTransferable.js
	truffle test test/crytic/TestERC20BuggyTransferable.js

To run Echidna:
	 echidna-test . --contract TestERC20BuggyTransferable --config echidna_config.yaml
```

### Step 2. Customize the constructor

Next, update the constructor in `contracts/crytic/TestX.sol`:

On [examples/slither-prop/contracts](https://github.com/crytic/slither/tree/9623a2781faa4e7759f06d2e8c4adcd45078af69/examples/slither-prop), update the constructor as follow:

```solidity
	constructor() public{

		_balanceOf[crytic_user] = 1 ether;
		_balanceOf[crytic_owner] = 1 ether;
		_balanceOf[crytic_attacker] = 1 ether;
		_totalSupply = 3 ether;

		// 
		// 
		// Update the following if totalSupply and balanceOf are external functions or state variables:

		initialTotalSupply = totalSupply();
		initialBalance_owner = balanceOf(crytic_owner);
		initialBalance_user = balanceOf(crytic_user);
		initialBalance_attacker = balanceOf(crytic_attacker);
	}
```

### Step 3. Run the unit tests with Truffle

The first unit test file, named `InitializationX.js` will check that the constructor has been correctly initialized:

```
$ truffle test test/crytic/InitializationTestERC20BuggyTransferable.js
[..]
  Contract: TestERC20BuggyTransferable
    ✓ The total supply is correctly initialized. (47ms)
    ✓ Owner's balance is correctly initialized.
    ✓ User's balance is correctly initialized.
    ✓ Attacker's balance is correctly initialized.
    ✓ All the users have a positive balance. (69ms)
    ✓ The total supply is the user and owner balance. (38ms)

```

If all the unit tests passed, run the property tests:
```
$ truffle test test/crytic/InitializationTestERC20BuggyTransferable.js
  Contract: TestERC20BuggyTransferable
    ✓ The address 0x0 should not receive tokens.
    ✓ Allowance can be changed. (108ms)
    ✓ Balance of one user must be less or equal to the total supply. (70ms)
    ✓ Balance of the crytic users must be less or equal to the total supply.
    1) No one should be able to send tokens to the address 0x0 (transfer).
    > No events were emitted
    2) No one should be able to send tokens to the address 0x0 (transferFrom).
    > No events were emitted
    ✓ Self transferFrom works. (115ms)
    ✓ transferFrom works. (108ms)
    ✓ Self transfer works. (89ms)
    ✓ transfer works. (97ms)
    3) Cannot transfer more than the balance.
    > No events were emitted

```

As you can see, the unit tests detect some of the bugs.

### Step 4. Run the property tests with Echidna

```
$ echidna-test . --contract TestERC20BuggyTransferable --config echidna_config.yaml
```

## Scenarios

`slither-prop` contains different scenarios that can be specified with the `--scenario NAME` flag.

Here are the available scenarios:
```
#################### ERC20 ####################
Transferable - Test the correct tokens transfer
Pausable - Test the pausable functionality
NotMintable - Test that no one can mint tokens
NotMintableNotBurnable - Test that no one can mint or burn tokens
NotBurnable - Test that no one can burn tokens
Burnable - Test the burn of tokens. Require the "burn(address) returns()" function
``` 

## All properties
```
+-----+-------------------------------------------------------------------------+------------------------+
| Num |                               Description                               |        Scenario        |
+-----+-------------------------------------------------------------------------+------------------------+
|  0  |                The address 0x0 should not receive tokens.               |      Transferable      |
|  1  |                        Allowance can be changed.                        |      Transferable      |
|  2  |      Balance of one user must be less or equal to the total supply.     |      Transferable      |
|  3  |  Balance of the crytic users must be less or equal to the total supply. |      Transferable      |
|  4  |   No one should be able to send tokens to the address 0x0 (transfer).   |      Transferable      |
|  5  | No one should be able to send tokens to the address 0x0 (transferFrom). |      Transferable      |
|  6  |                         Self transferFrom works.                        |      Transferable      |
|  7  |                           transferFrom works.                           |      Transferable      |
|  8  |                           Self transfer works.                          |      Transferable      |
|  9  |                             transfer works.                             |      Transferable      |
|  10 |                  Cannot transfer more than the balance.                 |      Transferable      |
|  11 |                             Cannot transfer.                            |        Pausable        |
|  12 |                       Cannot execute transferFrom.                      |        Pausable        |
|  13 |                        Cannot change the balance.                       |        Pausable        |
|  14 |                       Cannot change the allowance.                      |        Pausable        |
|  15 |                   The total supply does not increase.                   |      NotMintable       |
|  16 |                    The total supply does not change.                    | NotMintableNotBurnable |
|  17 |                   The total supply does not decrease.                   |      NotBurnable       |
|  18 |                   The total supply does not decrease.                   |        Burnable        |
+-----+-------------------------------------------------------------------------+------------------------+
```