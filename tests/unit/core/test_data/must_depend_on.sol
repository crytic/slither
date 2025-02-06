pragma solidity ^0.8.19;

interface IERC20 {
  function transferFrom(address from, address to, uint amount) external returns (bool);
}

/**
 * @title MissingReturnBug
 * @author IllIllI
 */

// test case of the missing return bug described here:
// https://medium.com/coinmonks/missing-return-value-bug-at-least-130-tokens-affected-d67bf08521ca
contract Unsafe {
    IERC20 erc20;
    function good2(address to, uint256 am) public {
        address from_msgsender = msg.sender;
        int_transferFrom(from_msgsender, to, am); // from is constant
    }

    // This is not detected
    function bad2(address from, address to, uint256 am) public {
        address from_msgsender = msg.sender;
        int_transferFrom(from_msgsender, to, amount); // from is not a constant
    }

    function int_transferFrom(address from, address to, uint256 amount) internal {
        erc20.transferFrom(from, to, amount); // not a constant = not a constant U constant
    }
}