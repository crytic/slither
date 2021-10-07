from slither.tools.properties.properties.properties import (
    Property,
    PropertyType,
    PropertyReturn,
    PropertyCaller,
)

ERC721_Transferable = [
    Property(
        name="crytic_revert_balanceOf_zero_ERC721Properties()",
        description="Querying the balance of address 0x0 should throw.",
        content="""
\t\tbalanceOf(address(0x0));
\t\treturn true;""",
        type=PropertyType.LOW_SEVERITY,
        return_type=PropertyReturn.FAIL_OR_THROW,
        is_unit_test=True,
        is_property_test=True,
        caller=PropertyCaller.ANY,
    ),
    Property(
        name="crytic_revert_ownerOf_invalid_ERC721Properties()",
        description="Querying the owner of an invalid token should throw",
        content="""
\t\townerOf(115792089237316195423570985008687907853269984665640564039457584007913129639935); // type(uint256).max
\t\treturn true;""",
        type=PropertyType.LOW_SEVERITY,
        return_type=PropertyReturn.FAIL_OR_THROW,
        is_unit_test=True,
        is_property_test=True,
        caller=PropertyCaller.ANY,
    ),
    Property(
        name="crytic_revert_approval_invalid_ERC721Properties()",
        description="Approving an invalid token should throw",
        content="""
\t\tapprove(address(0x0), 115792089237316195423570985008687907853269984665640564039457584007913129639935); // type(uint256).max
\t\treturn true;""",
        type=PropertyType.LOW_SEVERITY,
        return_type=PropertyReturn.FAIL_OR_THROW,
        is_unit_test=True,
        is_property_test=True,
        caller=PropertyCaller.ANY,
    ),
    Property(
        name="crytic_transfer_to_other_ERC721Properties()",
        description="Transfers and approvals to other users should work. Approvals should reset after transfer to other",
        content="""
\t\tuint otherBalance = balanceOf(crytic_attacker);
\t\tuint selfBalance = balanceOf(msg.sender);
\t\tuint oldTotalSupply = totalSupply();
\t\tfor (uint i = 0; i < selfBalance; i++) {
\t\t\tuint tokenId = tokenOfOwnerByIndex(msg.sender, 0);  // Always zero to avoid issues
\t\t\tapprove(crytic_attacker, tokenId);
\t\t\trequire(getApproved(tokenId) == crytic_attacker);
\t\t\tsafeTransferFrom(msg.sender, crytic_attacker, tokenId);
\t\t\trequire(ownerOf(tokenId) == crytic_attacker);
\t\t\trequire(getApproved(tokenId) == address(0x0));
\t\t}
\t\treturn oldTotalSupply == totalSupply() && otherBalance + selfBalance == balanceOf(crytic_attacker) && balanceOf(msg.sender) == 0;""",
        type=PropertyType.HIGH_SEVERITY,
        return_type=PropertyReturn.SUCCESS,
        is_unit_test=True,
        is_property_test=True,
        caller=PropertyCaller.ANY,
    ),
    Property(
        name="crytic_transfer_to_self_ERC721Properties()",
        description="Transfer to self should work. Approvals should reset after transfer to self",
        content="""
\t\tuint selfBalance = balanceOf(msg.sender);
\t\tfor (uint i = 0; i < selfBalance; i++) {
\t\t\tuint tokenId = tokenOfOwnerByIndex(msg.sender, i);
\t\t\tapprove(crytic_attacker, tokenId);
\t\t\trequire(getApproved(tokenId) == crytic_attacker);
\t\t\tsafeTransferFrom(msg.sender, msg.sender, tokenId);
\t\t\trequire(ownerOf(tokenId) == msg.sender);
\t\t\trequire(getApproved(tokenId) == address(0x0));
\t\t}
\t\treturn (balanceOf(msg.sender) == selfBalance);""",
       type=PropertyType.HIGH_SEVERITY,
        return_type=PropertyReturn.SUCCESS,
        is_unit_test=True,
        is_property_test=True,
        caller=PropertyCaller.ANY,
    ),
    Property(
        name="crytic_revert_unsafe_transfer_ERC721Properties()",
        description="Transfer to a contract that does not properly implement ERC721.onERC721Received should revert",
        content="""
\t\tuint selfBalance = balanceOf(msg.sender);
\t\tif (selfBalance == 0)
\t\t\trevert();
\t\tuint tokenId = tokenOfOwnerByIndex(msg.sender, 0); // Always zero to avoid issues
\t\tsafeTransferFrom(msg.sender, address(this), tokenId);
\t\treturn true;""",
       type=PropertyType.HIGH_SEVERITY,
        return_type=PropertyReturn.FAIL_OR_THROW,
        is_unit_test=True,
        is_property_test=True,
        caller=PropertyCaller.ANY,
    ),
    Property(
        name="crytic_setApprovalForAll_ERC721Properties()",
        description="setApprovalForAll works as expected",
        content="""
\t\taddress self = address(this);
\t\tsetApprovalForAll(self, true);
\t\trequire(isApprovedForAll(msg.sender, self));
\t\tsetApprovalForAll(self, true);
\t\trequire(isApprovedForAll(msg.sender, self));
\t\tfor (uint i = 0; i < balanceOf(msg.sender); i++) {
\t\t\tuint tokenId = tokenOfOwnerByIndex(msg.sender, 0);  // Always zero to avoid issues
\t\t\tthis.approve(crytic_attacker, tokenId);
\t\t\trequire(getApproved(tokenId) == crytic_attacker);
\t\t\tthis.safeTransferFrom(msg.sender, crytic_attacker, tokenId);
\t\t\trequire(ownerOf(tokenId) == crytic_attacker);
\t\t\trequire(getApproved(tokenId) == address(0x0));
\t\t}
\t\tsetApprovalForAll(self, false);
\t\trequire(!isApprovedForAll(msg.sender, self));
\t\tsetApprovalForAll(self, false);
\t\trequire(!isApprovedForAll(self, otherUser));
\t\treturn true;""",
        type=PropertyType.HIGH_SEVERITY,
        return_type=PropertyReturn.SUCCESS,
        is_unit_test=True,
        is_property_test=True,
        caller=PropertyCaller.ANY,
    ),
]
