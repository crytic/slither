from slither.tools.properties.properties.properties import (
    Property,
    PropertyType,
    PropertyReturn,
    PropertyCaller,
)

ERC721_Mintable = [
    Property(
        name="crytic_mint_ERC721Properties()",
        description="Minting creates a fresh token and increases the token supply.",
        content="""
\t\tuint selfBalance = balanceOf(msg.sender);
\t\tuint oldTotalSupply = totalSupply();
\t\tuint tokenId = mint();
\t\trequire(ownerOf(tokenId) == msg.sender); 
\t\trequire(getApproved(tokenId) == address(0x0));  
\t\treturn selfBalance + 1 == balanceOf(msg.sender) && oldTotalSupply + 1 == totalSupply();""",
        type=PropertyType.HIGH_SEVERITY,
        return_type=PropertyReturn.SUCCESS,
        is_unit_test=True,
        is_property_test=True,
        caller=PropertyCaller.ANY,
    ),
]
