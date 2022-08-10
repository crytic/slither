//SPDX-License-Identifier: UNLICENSED
pragma solidity >=0.8.0;

interface IERC20 { // truncated for test purposes
	function transfer(address to, uint amount) external;
}

contract DoubleEntryTokenPossiblityTest {

	address[] public whitelist;

	// should report
	function flashLoan(
		address recipient,
		IERC20[] memory tokens,
		uint[] memory amounts) external {

		for (uint i=0;i<tokens.length;i++){
			IERC20(tokens[i]).transfer(recipient, amounts[i]);
		}

		// ...
	}

	// should not report
	function updateWhitelist(address[] memory tokens) external { // onlyOwner

		for (uint i=0;i<tokens.length;i++) {
			whitelist[i] = tokens[i];
		}
	}

}