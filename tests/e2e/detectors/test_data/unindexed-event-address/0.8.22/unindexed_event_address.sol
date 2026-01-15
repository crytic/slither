// SPDX-License-Identifier: MIT
pragma solidity 0.8.22;

// Top-level event - SHOULD DETECT (has address params, no indexed)
event TopLevelBadEvent(address from, address to, uint256 value);

// Top-level event - should NOT detect (has indexed param)
event TopLevelGoodEvent(address indexed from, address to, uint256 value);

// Top-level event - should NOT detect (no address params)
event TopLevelNoAddress(uint256 value, bytes32 data);

contract TestContract {
    // SHOULD DETECT - address params, no indexed
    event BadTransfer(address from, address to, uint256 value);
    event BadApproval(address owner, address spender, uint256 amount);
    event SingleBadAddress(address user);

    // Should NOT detect - has indexed params
    event GoodTransfer(address indexed from, address indexed to, uint256 value);
    event PartiallyIndexed(address indexed from, address to, uint256 value);
    event IndexedNonAddress(address from, uint256 indexed value);

    // Should NOT detect - no address params
    event NoAddressEvent(uint256 value, bytes32 data);
    event EmptyEvent();
}
