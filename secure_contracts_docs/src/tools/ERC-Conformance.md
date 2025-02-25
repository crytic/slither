`slither-check-erc` checks for ERC's conformance.

## Features

`slither-check-erc` will check that:

- All the functions are present
- All the events are present
- Functions return the correct type
- Functions that must be view are view
- Events' parameters are correctly indexed
- The functions emit the events
- Derived contracts do not break the conformance

## Supported ERCs

- [ERC20](https://eips.ethereum.org/EIPS/eip-20): Token standard
- [ERC223](https://github.com/ethereum/eips/issues/223): Token standard
- [ERC777](https://eips.ethereum.org/EIPS/eip-777): Token standard
- [ERC721](https://eips.ethereum.org/EIPS/eip-721): Non-fungible token standard
- [ERC165](https://eips.ethereum.org/EIPS/eip-165): Standard interface detection
- [ERC1155](https://eips.ethereum.org/EIPS/eip-1155): Multi Token Standard
- [ERC1820](https://eips.ethereum.org/EIPS/eip-1820): Pseudo-introspection registry contract
- [ERC4524](https://eips.ethereum.org/EIPS/eip-4524): Safer ERC-20
- [ERC1363](https://eips.ethereum.org/EIPS/eip-1363): Payable Token
- [ERC2612](https://eips.ethereum.org/EIPS/eip-2612): Permit Extension for EIP-20 Signed Approvals
- [ERC4626](https://eips.ethereum.org/EIPS/eip-4626): Tokenized Vaults

## Usage:

```
slither-check-erc contract.sol ContractName
```
For example, on

```Solidity
contract ERC20{

    event Transfer(address indexed,address,uint256);

    function transfer(address, uint256) public{

        emit Transfer(msg.sender,msg.sender,0);
    }

}
```

The tool will report:

```
# Check ERC20

## Check functions
[ ] totalSupply() is missing 
[ ] balanceOf(address) is missing 
[✓] transfer(address,uint256) is present
	[ ] transfer(address,uint256) -> () should return bool
	[✓] Transfer(address,address,uint256) is emitted
[ ] transferFrom(address,address,uint256) is missing 
[ ] approve(address,uint256) is missing 
[ ] allowance(address,address) is missing 
[ ] name() is missing (optional)
[ ] symbol() is missing (optional)
[ ] decimals() is missing (optional)

## Check events
[✓] Transfer(address,address,uint256) is present
	[✓] parameter 0 is indexed
	[ ] parameter 1 should be indexed
[ ] Approval(address,address,uint256) is missing
```