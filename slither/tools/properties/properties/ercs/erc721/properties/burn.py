from slither.tools.properties.properties.properties import (
    Property,
    PropertyType,
    PropertyReturn,
    PropertyCaller,
)

ERC721_Burnable = [
    Property(
        name="crytic_burn_all_ERC721Properties()",
        description="The burn function should destroy tokens and reduce the total supply.",
        content="""
\t\tuint selfBalance = balanceOf(msg.sender);
\t\tif (selfBalance == 0)
\t\t\treturn true;
\t\tuint oldTotalSupply = totalSupply();
\t\tfor (uint i = 0; i < selfBalance; i++) {
\t\t\tuint tokenId = tokenOfOwnerByIndex(msg.sender, 0); // Always zero to avoid issues
\t\t\tburn(tokenId);
\t\t}
\t\treturn (oldTotalSupply - selfBalance == totalSupply() && balanceOf(msg.sender) == 0);""",
        type=PropertyType.HIGH_SEVERITY,
        return_type=PropertyReturn.SUCCESS,
        is_unit_test=True,
        is_property_test=True,
        caller=PropertyCaller.ANY,
    ),
    Property(
        name="crytic_revert_burn_transfer_ERC721Properties()",
        description="The burn function should destroy specific tokens",
        content="""
\t\tuint selfBalance = balanceOf(msg.sender);
\t\tif (selfBalance == 0)
\t\t\trevert();
\t\tuint tokenId = tokenOfOwnerByIndex(msg.sender, 0); // Always zero to avoid issues
\t\tburn(tokenId);
\t\tsafeTransferFrom(msg.sender, crytic_attacker, tokenId); 
\t\treturn true;""",
        type=PropertyType.HIGH_SEVERITY,
        return_type=PropertyReturn.FAIL_OR_THROW,
        is_unit_test=True,
        is_property_test=True,
        caller=PropertyCaller.ANY,
    ),

    Property(
        name="crytic_revert_burn_approve_ERC721Properties()",
        description="Burned tokens cannot be approved",
        content="""
\t\tuint selfBalance = balanceOf(msg.sender);
\t\tif (selfBalance == 0)
\t\t\trevert();
\t\tuint tokenId = tokenOfOwnerByIndex(msg.sender, 0); // Always zero to avoid issues
\t\tburn(tokenId);
\t\tapprove(crytic_attacker, tokenId); 
\t\treturn true;""",
        type=PropertyType.HIGH_SEVERITY,
        return_type=PropertyReturn.FAIL_OR_THROW,
        is_unit_test=True,
        is_property_test=True,
        caller=PropertyCaller.ANY,
    ), 
    Property(
        name="crytic_revert_burn_getApproval_ERC721Properties()",
        description="Burned tokens cannot be queried for approvals",
        content="""
\t\tuint selfBalance = balanceOf(msg.sender);
\t\tif (selfBalance == 0)
\t\t\trevert();
\t\tuint tokenId = tokenOfOwnerByIndex(msg.sender, 0); // Always zero to avoid issues
\t\tburn(tokenId);
\t\tgetApproved(tokenId); 
\t\treturn true;""",
        type=PropertyType.HIGH_SEVERITY,
        return_type=PropertyReturn.FAIL_OR_THROW,
        is_unit_test=True,
        is_property_test=True,
        caller=PropertyCaller.ANY,
    ),

    Property(
        name="crytic_revert_burn_ownerOf_ERC721Properties()",
        description="Burned tokens cannot be queried for ownership",
        content="""
\t\tuint selfBalance = balanceOf(msg.sender);
\t\tif (selfBalance == 0)
\t\t\trevert();
\t\tuint tokenId = tokenOfOwnerByIndex(msg.sender, 0); // Always zero to avoid issues
\t\tburn(tokenId);
\t\townerOf(tokenId); 
\t\treturn true;""",
        type=PropertyType.HIGH_SEVERITY,
        return_type=PropertyReturn.FAIL_OR_THROW,
        is_unit_test=True,
        is_property_test=True,
        caller=PropertyCaller.ANY,
    ), 


]
